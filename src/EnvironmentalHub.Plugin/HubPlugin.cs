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
