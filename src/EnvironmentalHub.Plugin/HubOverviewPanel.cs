using System.Runtime.InteropServices;
using Eto.Drawing;
using Eto.Forms;
using Rhino.UI;
namespace EnvironmentalHub.Plugin;

[Guid("7281a8f2-e2c4-4c27-bcb5-22cbb0688b32")]
public sealed class HubOverviewPanel:Panel
{
    public HubOverviewPanel()
    {
        var layout=new DynamicLayout{Padding=16,Spacing=new Size(8,14)};
        layout.AddRow(HubUi.Header("Building performance","A model-to-results workspace for architectural environmental analysis."));
        layout.AddRow(HubUi.Section("ANALYSIS WORKFLOW",HubUi.Hint("01  Geometry / Model\n02  Environment / Weather\n03  Simulation settings\n04  Validate / Run\n05  Results\n06  Compare / Export")));
        var solar=new Button{Text="Start solar radiation analysis"};
        solar.Click+=(_,_)=>Panels.OpenPanel(typeof(RadiationPanel));
        layout.AddRow(HubUi.Section("SIMULATIONS",HubUi.Hint("SOLAR RADIATION  ·  Available\nIncident energy on geometry, with shading context.\nLadybug / Radiance · kWh/m²"),solar,
            HubUi.Hint("Daylight · Thermal comfort · Energy · Carbon · CFD\nPlanned integrations; no executable workflow yet.\nHoneybee / OpenStudio / EnergyPlus / Eddy3D")));
        var climateTools=new DynamicLayout{Spacing=new Size(8,8)};
        foreach(var module in HubUi.Modules.Skip(1).Take(4))
        {
            var open=new Button{Text="Open "+module.Label};var type=module.Panel;open.Click+=(_,_)=>Panels.OpenPanel(type);
            climateTools.AddRow(open);
        }
        layout.AddRow(HubUi.Section("ENVIRONMENT TOOLS",climateTools,HubUi.Hint("Inspect EPW weather, construct a location, import design conditions or define analysis time. Each tool retains its own state.")));
        layout.AddRow(HubUi.Hint("8 of 122 installed Ladybug entries integrated as independent functions. Solver availability and validation are checked before running; exports include parameters, units and provenance."));
        layout.Add(null);HubUi.Mount(this,layout);
    }
}
