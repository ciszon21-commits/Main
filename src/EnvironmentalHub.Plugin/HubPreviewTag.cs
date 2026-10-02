using Rhino.DocObjects;

namespace EnvironmentalHub.Plugin;

// Tags identify previews created by this plugin; names alone never grant ownership.
internal static class HubPreviewTag
{
    internal const string Key = "EnvironmentalHub.PreviewOwner";
    internal const string Prefix = "bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/";
    internal static ObjectAttributes Mark(ObjectAttributes attributes, string module)
    { attributes.SetUserString(Key, Prefix + module); return attributes; }
}
