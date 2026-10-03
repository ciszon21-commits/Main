using System.Runtime.InteropServices;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.UI;

namespace EnvironmentalHub.Plugin;

// Keep the original overview identity so Rhino can reuse its saved dock location.
[Guid("7281a8f2-e2c4-4c27-bcb5-22cbb0688b32")]
public sealed class HubWorkspacePanel : Panel, IPanel
{
    private sealed class DocumentSession
    {
        internal readonly Dictionary<Type, Panel> Modules = [];
        internal Type ActiveModule = typeof(HubOverviewPanel);
        internal HubWorkspacePanel? Owner;
    }
    private static readonly Dictionary<uint, DocumentSession> sessions = [];
    private Dictionary<Type, Panel> modules = [];
    private DocumentSession? session;
    private uint documentSerial;
    private readonly DropDown selector = new();
    private readonly Panel body = new();
    private readonly Label context = HubUi.Hint("");
    private bool switching;
    private bool initialFloatingWidthApplied;

    public Type ActiveModule { get; private set; } = typeof(HubOverviewPanel);
    public int CachedModuleCount => modules.Count;

    static HubWorkspacePanel()
    {
        RhinoDoc.CloseDocument += (_, args) => ReleaseDocument(args.Document.RuntimeSerialNumber);
    }

    public HubWorkspacePanel()
    {
        MinimumSize = new Size(300, 200);
        BackgroundColor = SystemColors.ControlBackground;
        foreach (var module in HubUi.Modules) selector.Items.Add(module.Label);
        selector.ToolTip = "在同一工作平台切換模組；保留已輸入的條件與分析結果。";
        selector.SelectedIndexChanged += (_, _) =>
        {
            if (!switching && selector.SelectedIndex >= 0)
                ShowModule(HubUi.Modules[selector.SelectedIndex].Panel);
        };
        var home = new Button { Text = "首頁", ToolTip = "返回分析流程總覽" };
        home.Click += (_, _) => ShowModule(typeof(HubOverviewPanel));
        var navigation = new DynamicLayout { Padding = new Padding(16, 10), Spacing = new Size(8, 6) };
        navigation.AddRow(selector, home);
        navigation.AddRow(context);
        var layout = new DynamicLayout { Spacing = Size.Empty };
        layout.AddRow(navigation);
        layout.AddRow(new Panel { Height = 1, BackgroundColor = HubVisuals.Rule(HubTopic.Overview) });
        layout.Add(body, yscale: true);
        Content = layout;
        ShowModule(typeof(HubOverviewPanel));
        LoadComplete += (_, _) => Application.Instance.AsyncInvoke(EnsureInitialFloatingWidth);
    }

    public Panel GetModule(Type type)
    {
        if (!HubUi.Modules.Any(module => module.Panel == type))
            throw new ArgumentException("此模組未納入工作平台。", nameof(type));
        if (!modules.TryGetValue(type, out var panel))
        {
            panel = (Panel)Activator.CreateInstance(type)!;
            modules.Add(type, panel);
        }
        return panel;
    }

    public T GetModule<T>() where T : Panel => (T)GetModule(typeof(T));

    public void ShowModule(Type type)
    {
        var index = Array.FindIndex(HubUi.Modules, module => module.Panel == type);
        if (index < 0) throw new ArgumentException("此模組未納入工作平台。", nameof(type));
        var next = GetModule(type);
        switching = true;
        try
        {
            if (body.Content is SunHoursPanel hours && !ReferenceEquals(hours, next)) hours.ReleaseFocusVisibility();
            // Detach the previous view without disposing it: results and snapshots stay owned by it.
            if (!ReferenceEquals(body.Content, next)) { body.Content = null; body.Content = next; }
            ActiveModule = type;
            if (session is not null) session.ActiveModule = type;
            selector.SelectedIndex = index;
            context.Text = HubUi.Modules[index].Detail;
        }
        finally { switching = false; }
    }

    public void PanelShown(uint serial, ShowPanelReason reason)
    {
        // Rhino can replace the shell when moving between dock containers.
        // The document session owns the cached views, not that disposable shell.
        if (serial == 0) serial = RhinoDoc.ActiveDoc?.RuntimeSerialNumber ?? 0;
        if (serial == 0) return;
        if (!sessions.TryGetValue(serial, out var next))
            sessions.Add(serial, next = new DocumentSession());
        if (!ReferenceEquals(session, next))
        {
            DetachSession();
            foreach (var view in modules.Values) view.Dispose();
            next.Owner?.DetachSession();
            session = next;
            documentSerial = serial;
            modules = next.Modules;
            next.Owner = this;
        }
        ShowModule(next.ActiveModule);
        Application.Instance.AsyncInvoke(EnsureInitialFloatingWidth);
    }

    public void PanelHidden(uint serial, ShowPanelReason reason)
    {
        if (body.Content is SunHoursPanel hours) hours.ReleaseFocusVisibility();
    }

    public void PanelClosing(uint serial, bool onCloseDocument)
    {
        var bound = documentSerial;
        DetachSession();
        if (onCloseDocument && bound != 0) ReleaseDocument(bound);
    }

    private void DetachSession()
    {
        if (body.Content is SunHoursPanel hours) hours.ReleaseFocusVisibility();
        body.Content = null;
        if (session is null) return;
        if (ReferenceEquals(session.Owner, this)) session.Owner = null;
        session = null;
        documentSerial = 0;
        modules = [];
    }

    private static void ReleaseDocument(uint serial)
    {
        if (!sessions.Remove(serial, out var closed)) return;
        closed.Owner?.DetachSession();
        foreach (var view in closed.Modules.Values) view.Dispose();
        closed.Modules.Clear();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            // Detach before the Eto shell disposes its children. Unregistered
            // capture shells own their views; document sessions retain theirs.
            var retained = session is not null;
            DetachSession();
            if (!retained)
            {
                foreach (var view in modules.Values) view.Dispose();
                modules.Clear();
            }
        }
        base.Dispose(disposing);
    }

    internal static void ReleaseSessions()
    {
        foreach (var serial in sessions.Keys.ToArray()) ReleaseDocument(serial);
    }

    internal static bool Open(RhinoDoc document, Type module)
    {
        Panels.OpenPanel(typeof(HubWorkspacePanel));
        var workspace = Panels.GetPanel<HubWorkspacePanel>(document);
        if (workspace is null) return false;
        workspace.PanelShown(document.RuntimeSerialNumber, ShowPanelReason.Show);
        workspace.ShowModule(module);
        workspace.EnsureInitialFloatingWidth();
        return true;
    }

    private void EnsureInitialFloatingWidth()
    {
        // A docked panel belongs to Rhino's main window. Resize only the actual
        // Eto floating form, once; later user resizing and module switches win.
        if (initialFloatingWidthApplied || !Loaded || ParentWindow is not Form window ||
            window.NativeHandle == RhinoApp.MainWindowHandle() || !window.Resizable)
            return;
        var document = RhinoDoc.ActiveDoc;
        if (document is null || !Panels.GetPanels(typeof(HubWorkspacePanel).GUID, document)
                .Any(panel => ReferenceEquals(panel, this)))
            return;
        var container = Panels.PanelDockBar(typeof(HubWorkspacePanel));
        if (container == Guid.Empty || Panels.GetOpenPanelIds().Any(id =>
                id != typeof(HubWorkspacePanel).GUID && Panels.PanelDockBars(id).Contains(container)))
            return;
        var targetWidth = Math.Min(500, (int)window.Screen.WorkingArea.Width);
        if (targetWidth <= 0) return;
        try
        {
            if (window.Size.Width < targetWidth)
                window.Size = new Size(targetWidth, window.Size.Height);
            initialFloatingWidthApplied = true;
        }
        catch (NotSupportedException)
        {
            // Some host versions expose a read-only native window wrapper.
            // Keep the panel usable without changing the rest of Rhino's layout.
        }
    }
}
