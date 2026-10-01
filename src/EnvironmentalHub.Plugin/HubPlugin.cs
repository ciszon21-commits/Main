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
        Panels.RegisterPanel(this, typeof(RadiationPanel), "Environmental Hub", null);
        Panels.RegisterPanel(this, typeof(WeatherPanel), "Hub • Weather", null);
        Panels.RegisterPanel(this, typeof(LocationPanel), "Hub • Location", null);
        Panels.RegisterPanel(this, typeof(ClimateFilePanel), "Hub • Climate files", null);
        return LoadReturnCode.Success;
    }
}

public sealed class EnvironmentalHubCommand : Command
{
    public override string EnglishName => "EnvironmentalHub";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        Panels.OpenPanel(typeof(RadiationPanel));
        return Result.Success;
    }
}

public sealed class EnvironmentalWeatherCommand : Command
{
    public override string EnglishName => "EnvironmentalWeather";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        Panels.OpenPanel(typeof(WeatherPanel));
        return Result.Success;
    }
}

public sealed class EnvironmentalLocationCommand : Command
{
    public override string EnglishName => "EnvironmentalLocation";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        Panels.OpenPanel(typeof(LocationPanel)); return Result.Success;
    }
}

public sealed class EnvironmentalClimateCommand : Command
{
    public override string EnglishName => "EnvironmentalClimate";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    { Panels.OpenPanel(typeof(ClimateFilePanel)); return Result.Success; }
}
