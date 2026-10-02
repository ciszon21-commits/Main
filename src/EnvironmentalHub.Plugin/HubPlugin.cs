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
        Panels.RegisterPanel(this, typeof(HubOverviewPanel), "建築環境模擬平台", null);
        Panels.RegisterPanel(this, typeof(RadiationPanel), "環境平台 · 日射", null);
        Panels.RegisterPanel(this, typeof(WeatherPanel), "環境平台 · 氣象", null);
        Panels.RegisterPanel(this, typeof(LocationPanel), "環境平台 · 地點", null);
        Panels.RegisterPanel(this, typeof(ClimateFilePanel), "環境平台 · 氣候檔案", null);
        Panels.RegisterPanel(this, typeof(TimePanel), "環境平台 · 時間", null);
        return LoadReturnCode.Success;
    }
}

public sealed class EnvironmentalHubCommand : Command
{
    public override string EnglishName => "EnvironmentalHub";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        Panels.OpenPanel(typeof(HubOverviewPanel));
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

public sealed class EnvironmentalRadiationCommand : Command
{
    public override string EnglishName=>"EnvironmentalRadiation";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){Panels.OpenPanel(typeof(RadiationPanel));return Result.Success;}
}
public sealed class EnvironmentalTimeCommand : Command
{
    public override string EnglishName=>"EnvironmentalTime";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode){Panels.OpenPanel(typeof(TimePanel));return Result.Success;}
}
