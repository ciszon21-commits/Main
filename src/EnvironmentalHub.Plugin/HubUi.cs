using Eto.Drawing;
using Eto.Forms;
using Rhino.UI;
namespace EnvironmentalHub.Plugin;

internal static class HubUi
{
    internal static readonly (string Label,Type Panel,string Detail)[] Modules=
    [ ("平台首頁",typeof(HubOverviewPanel),"選擇分析流程"),
      ("EPW 氣象",typeof(WeatherPanel),"逐時氣象、時間選取與缺值檢視"),
      ("地點",typeof(LocationPanel),"座標、海拔與 UTC 時差"),
      ("氣候與設計日",typeof(ClimateFilePanel),"氣候分區、晴空與設計條件"),
      ("時間與分析期間",typeof(TimePanel),"分析期間與日期／年時數轉換"),
      ("日射分析",typeof(RadiationPanel),"模型、遮蔭與原生日射分析") ];
    internal static Label Hint(string text)=>new(){Text=text,UseMnemonic=false,Wrap=WrapMode.Word,TextColor=HubVisuals.Secondary};
    internal static string FieldTitle(string name)=>HubText.Field(name);
    internal static Control Header(string title,string description,Type? module=null)
    {
        var layout=new DynamicLayout{Spacing=new Size(8,6)};
        var topic=module is null?HubTopic.Overview:HubVisuals.ModuleTopic(module);
        var glyph=module is null?HubGlyph.Overview:HubVisuals.ModuleGlyph(module);
        var heading=new DynamicLayout{Spacing=new Size(8,6)};
        heading.AddRow(HubVisuals.Icon(glyph,topic,18),new Label{Text="建築環境模擬平台  /  "+typeof(HubUi).Assembly.GetName().Version!.ToString(3),Font=new Eto.Drawing.Font(SystemFont.Default,10),TextColor=HubVisuals.Secondary,Wrap=WrapMode.Word});
        layout.AddRow(heading);
        layout.AddRow(new Label{Text=title,UseMnemonic=false,Font=new Eto.Drawing.Font(SystemFont.Bold,18),Wrap=WrapMode.Word});
        layout.AddRow(Hint(description));return layout;
    }
    internal static Control Navigation(Type active)
    {
        var choice=new DropDown();foreach(var m in Modules)choice.Items.Add(m.Label);
        choice.SelectedIndex=Array.FindIndex(Modules,m=>m.Panel==active);
        var open=new Button{Text="開啟",ToolTip="開啟選取的模組，保留各面板已有結果"};
        open.Click+=(_,_)=>{if(choice.SelectedIndex>=0)Panels.OpenPanel(Modules[choice.SelectedIndex].Panel);};
        var row=new DynamicLayout{Spacing=new Size(8,6)};row.AddRow(choice,open);return row;
    }
    // Open, ruled sections fit a technical workspace without a stack of cards.
    internal static Control Section(string title,params Control[] controls)=>Section(title,HubTopic.Overview,controls);
    internal static Control Section(string title,HubTopic topic,params Control[] controls)
    {
        var body=new DynamicLayout{Spacing=new Size(8,8)};
        var heading=new DynamicLayout{Spacing=new Size(8,6)};
        heading.AddRow(HubVisuals.Icon(HubVisuals.Glyph(topic),topic),new Label{Text=title,UseMnemonic=false,Font=new Eto.Drawing.Font(SystemFont.Bold,11),TextColor=HubVisuals.Accent(topic),Wrap=WrapMode.Word});
        body.AddRow(heading);
        body.AddRow(new Panel{Height=1,BackgroundColor=HubVisuals.Rule(topic)});
        foreach(var c in controls)body.AddRow(c);
        return body;
    }
    internal static Control WorkflowLine(string title,HubTopic topic)
    {
        var row=new DynamicLayout{Spacing=new Size(8,6)};
        row.AddRow(HubVisuals.Icon(HubVisuals.Glyph(topic),topic,18),new Label{Text=title,UseMnemonic=false,TextColor=HubVisuals.Accent(topic),Wrap=WrapMode.Word});return row;
    }
    internal static Control ModuleAction(Button button,Type module)
    {
        var row=new DynamicLayout{Spacing=new Size(8,6)};
        row.AddRow(HubVisuals.Icon(HubVisuals.ModuleGlyph(module),HubVisuals.ModuleTopic(module)),button);return row;
    }
    internal static void Mount(Panel panel,DynamicLayout layout)
    {panel.MinimumSize=new Size(300,200);panel.Size=new Size(360,680);panel.BackgroundColor=SystemColors.ControlBackground;
     var scroll=new Scrollable{Content=layout,ExpandContentWidth=true};scroll.SizeChanged+=(_,_)=>layout.Width=Math.Max(120,scroll.ClientSize.Width-20);panel.Content=scroll;}
}
