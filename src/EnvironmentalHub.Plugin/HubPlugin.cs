using System.Runtime.InteropServices;
using Rhino;
using Rhino.Commands;
using Rhino.PlugIns;
using Rhino.UI;

[assembly: Guid("bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f")]

namespace EnvironmentalHub.Plugin;

public sealed class HubPlugin : PlugIn
{
    protected override LoadReturnCode OnLoad(ref string errorMessage)
    {
        Panels.RegisterPanel(this, typeof(HubWorkspacePanel), "建築環境模擬平台", null);
        return LoadReturnCode.Success;
    }
}

public sealed class EnvironmentalHubCommand : Command
{
    public override string EnglishName => "EnvironmentalHub";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        return HubWorkspacePanel.Open(doc, typeof(HubOverviewPanel)) ? Result.Success : Result.Failure;
    }
}

public sealed class EnvironmentalWeatherCommand : Command
{
    public override string EnglishName => "EnvironmentalWeather";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        return HubWorkspacePanel.Open(doc, typeof(WeatherPanel)) ? Result.Success : Result.Failure;
    }
}

public sealed class EnvironmentalLocationCommand : Command
{
    public override string EnglishName => "EnvironmentalLocation";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        return HubWorkspacePanel.Open(doc, typeof(LocationPanel)) ? Result.Success : Result.Failure;
    }
}

public sealed class EnvironmentalClimateCommand : Command
{
    public override string EnglishName => "EnvironmentalClimate";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    { return HubWorkspacePanel.Open(doc, typeof(ClimateFilePanel)) ? Result.Success : Result.Failure; }
}

public sealed class EnvironmentalRadiationCommand : Command
{
    public override string EnglishName=>"EnvironmentalRadiation";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){return HubWorkspacePanel.Open(doc, typeof(RadiationPanel)) ? Result.Success : Result.Failure;}
}
public sealed class EnvironmentalTimeCommand : Command
{
    public override string EnglishName=>"EnvironmentalTime";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){return HubWorkspacePanel.Open(doc, typeof(TimePanel)) ? Result.Success : Result.Failure;}
}
public sealed class EnvironmentalSunPathCommand : Command
{
    public override string EnglishName => "EnvironmentalSunPath";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => HubWorkspacePanel.Open(doc, typeof(SunPathPanel)) ? Result.Success : Result.Failure;
}

public sealed class EnvironmentalSunHoursCommand : Command
{
    public override string EnglishName => "EnvironmentalSunHours";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => HubWorkspacePanel.Open(doc, typeof(SunHoursPanel)) ? Result.Success : Result.Failure;
}
