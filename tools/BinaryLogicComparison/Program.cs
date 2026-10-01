using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text.Json;

static string Hash(byte[] data) => Convert.ToHexString(SHA256.HashData(data));
static object Compare(string previous, string current)
{
    using var pf = File.OpenRead(previous); using var cf = File.OpenRead(current);
    using var p = new PEReader(pf); using var c = new PEReader(cf);
    var pm = p.GetMetadataReader(); var cm = c.GetMetadataReader();
    string Info(MetadataReader md)
    {
        foreach (var h in md.GetAssemblyDefinition().GetCustomAttributes())
        {
            var attr=md.GetCustomAttribute(h);
            if (attr.Constructor.Kind!=HandleKind.MemberReference) continue;
            var member=md.GetMemberReference((MemberReferenceHandle)attr.Constructor);
            if (member.Parent.Kind!=HandleKind.TypeReference) continue;
            var type=md.GetTypeReference((TypeReferenceHandle)member.Parent);
            if (md.GetString(type.Namespace)!="System.Reflection" || md.GetString(type.Name)!="AssemblyInformationalVersionAttribute") continue;
            var blob=md.GetBlobReader(attr.Value);
            if (blob.ReadUInt16()!=1) throw new InvalidOperationException("Invalid attribute prolog");
            return blob.ReadSerializedString()!;
        }
        throw new InvalidOperationException("Missing informational version");
    }
    byte[] Normalize(PEReader pe, MetadataReader md)
    {
        var bytes = pe.GetMetadata().GetContent().ToArray();
        var id = md.GetGuid(md.GetModuleDefinition().Mvid).ToByteArray();
        var found = 0;
        for (int i = 0; i <= bytes.Length - id.Length; i++)
            if (bytes.AsSpan(i, id.Length).SequenceEqual(id)) { bytes.AsSpan(i, id.Length).Clear(); found++; }
        if (found != 1) throw new InvalidOperationException("Expected one module ID in metadata");
        var info=Info(md);
        if (!System.Text.RegularExpressions.Regex.IsMatch(info,@"^1\.0\.0\+[a-f0-9]{40}$"))
            throw new InvalidOperationException("Unexpected informational-version format: " + info);
        var value=System.Text.Encoding.UTF8.GetBytes(info); found=0;
        for (int i=0;i<=bytes.Length-value.Length;i++)
            if (bytes.AsSpan(i,value.Length).SequenceEqual(value)) { bytes.AsSpan(i+info.IndexOf('+')+1,40).Clear(); found++; }
        if (found!=1) throw new InvalidOperationException("Expected one informational-version value in metadata");
        return bytes;
    }
    var metadataSame = Normalize(p, pm).SequenceEqual(Normalize(c, cm));
    if (!metadataSame) throw new InvalidOperationException("Managed metadata differs beyond MVID and informational Git revision: " + current);
    string Body(PEReader pe, MethodDefinition m)
    {
        if (m.RelativeVirtualAddress == 0) return "No body";
        var b = pe.GetMethodBody(m.RelativeVirtualAddress);
        return JsonSerializer.Serialize(new { il=Convert.ToHexString(b.GetILBytes()!), b.MaxStack, b.LocalVariablesInitialized,
            signature=System.Reflection.Metadata.Ecma335.MetadataTokens.GetToken(b.LocalSignature),
            exceptions=b.ExceptionRegions.Select(e => new { e.Kind,e.TryOffset,e.TryLength,e.HandlerOffset,e.HandlerLength,e.FilterOffset,
                type=System.Reflection.Metadata.Ecma335.MetadataTokens.GetToken(e.CatchType) }) });
    }
    var methods = pm.MethodDefinitions.ToArray(); var other = cm.MethodDefinitions.ToArray();
    if (methods.Length != other.Length) throw new InvalidOperationException("Method count differs");
    for (int i=0;i<methods.Length;i++)
        if (Body(p,pm.GetMethodDefinition(methods[i])) != Body(c,cm.GetMethodDefinition(other[i])))
            throw new InvalidOperationException("Managed method body differs: " + pm.GetString(pm.GetMethodDefinition(methods[i]).Name));
    if (p.PEHeaders.CorHeader!.ResourcesDirectory.Size != 0 || c.PEHeaders.CorHeader!.ResourcesDirectory.Size != 0)
        throw new InvalidOperationException("Managed resources require a separate comparison");
    object[] Debug(PEReader pe) => pe.ReadDebugDirectory().Where(d=>d.Type==DebugDirectoryEntryType.CodeView).Select(d=>
    { var x=pe.ReadCodeViewDebugDirectoryData(d); return (object)new { x.Path, x.Guid, x.Age }; }).ToArray();
    return new { name=Path.GetFileName(current), previous_sha256=Hash(File.ReadAllBytes(previous)), current_sha256=Hash(File.ReadAllBytes(current)),
        metadata_equal_except_build_module_id_and_informational_git_revision=true, prior_informational_version=Info(pm),current_informational_version=Info(cm),
        method_bodies_equal=true, methods_compared=methods.Length,
        managed_resources=0, prior_debug=Debug(p), current_debug=Debug(c),
        scope="All managed metadata (including signatures, constants, attributes and references), excluding MVID and the 40-character Git revision in AssemblyInformationalVersion; all IL, locals, stack and exception regions. Not whole-file byte identity." };
}
try
{
if (args.Length!=3) throw new ArgumentException("Previous release directory, current release directory, output JSON required");
var report=new { binaries=new[] { "EnvironmentalHub.Core.dll", "EnvironmentalHub.Adapters.dll" }
    .Select(n=>Compare(Path.Combine(args[0],n),Path.Combine(args[1],n))).ToArray() };
File.WriteAllText(args[2],JsonSerializer.Serialize(report,new JsonSerializerOptions { WriteIndented=true }));
Console.WriteLine("Managed metadata and all method bodies match; build debug identity recorded.");
}
catch (Exception e) { Console.Error.WriteLine(e.Message); Environment.ExitCode=1; }
