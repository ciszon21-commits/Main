using System.Collections;
using System.Security.Cryptography;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;
namespace EnvironmentalHub.Adapters;

public sealed class LadybugTimeAdapter(string folder)
{
    public static string PeriodJson(string json,string folder) => JsonSerializer.Serialize(new LadybugTimeAdapter(folder).Period(JsonSerializer.Deserialize<PeriodRequest>(json)!));
    public static string CalendarJson(string json,string folder) => JsonSerializer.Serialize(new LadybugTimeAdapter(folder).Calendar(JsonSerializer.Deserialize<CalendarRequest>(json)!));
    private T Solve<T>(string name, Dictionary<string,object> inputs, Func<IGH_Component,Dictionary<string,string>,T> read)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("CLIMATE-THREAD-001: Execute on Rhino UI thread.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("CLIMATE-GH-001: Grasshopper solver disabled.");
        var path=Path.Combine(folder,name+".ghuser");
        if (!File.Exists(path)) throw new InvalidOperationException("CLIMATE-PLUGIN-001: Original time component missing.");
        var hash=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
        using var d=new GH_Document();d.Enabled=false;
        try
        {
            var c=(IGH_Component)new GH_UserObject(path).InstantiateObject();c.CreateAttributes();d.AddObject(c,false);
            foreach(var pair in inputs)
            { var p=new Param_GenericObject();p.CreateAttributes();p.SetPersistentData(new GH_ObjectWrapper(pair.Value));d.AddObject(p,false);c.Params.Input.Single(i=>i.Name==pair.Key).AddSource(p); }
            Instances.DocumentServer.AddDocument(d);d.Enabled=true;d.NewSolution(false);
            var errors=c.RuntimeMessages(GH_RuntimeMessageLevel.Error);
            if(errors.Count>0)throw new InvalidOperationException("CLIMATE-SOLVER-001: "+string.Join("\n",errors));
            var result=read(c,new(){["Source"]=path,["UserObjectSha256"]=hash,["ComponentVersion"]=c.Message,["Convention"]="Native Ladybug non-leap local-standard-time; HOY zero-based, DOY one-based; fractional HOY retained"});
            if(hash!=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))))throw new InvalidOperationException("CLIMATE-INPUT-001: Component changed during execution.");
            return result;
        }
        finally { Instances.DocumentServer.RemoveDocument(d); }
    }
    private static object[] Values(IGH_Component c,string name)=>c.Params.Output.Single(o=>o.Name==name).VolatileData.AllData(true).Select(v=>v.ScriptVariable()).ToArray();
    private static WeatherTime Date(dynamic value)=>new((int)value.month,(int)value.day,(int)value.hour,(int)value.minute,(double)value.hoy);
    public PeriodResult Period(PeriodRequest r)
    {
        if(r is null||r.SchemaVersion!="1.0")throw new InvalidOperationException("CLIMATE-CONTRACT-001: Period schema 1.0 required.");
        if(r.StartMonth is <1 or >12||r.EndMonth is <1 or >12||r.StartDay is <1 or >31||r.EndDay is <1 or >31||r.StartHour is <0 or >23||r.EndHour is <0 or >23||!new[]{1,2,3,4,5,6,10,12,15,20,30,60}.Contains(r.TimeStep))
            throw new InvalidOperationException("CLIMATE-PERIOD-001: Valid month/day/hour and supported time step required.");
        return Solve("LB Analysis Period",new(){["_start_month_"]=r.StartMonth,["_start_day_"]=r.StartDay,["_start_hour_"]=r.StartHour,["_end_month_"]=r.EndMonth,["_end_day_"]=r.EndDay,["_end_hour_"]=r.EndHour,["_timestep_"]=r.TimeStep},(c,metadata)=>
        {
            dynamic period=Values(c,"period").Single();var dictionary=new Dictionary<string,object?>();
            foreach(DictionaryEntry entry in (IDictionary)period.to_dict())dictionary[(string)entry.Key]=entry.Value;
            var hoys=Values(c,"hoys").Select(Convert.ToDouble).ToArray();var times=Values(c,"dates").Select(v=>Date(v)).ToArray();
            if(hoys.Length==0||hoys.Length!=times.Length||hoys.Where((h,i)=>!double.IsFinite(h)||h!=times[i].HourOfYear).Any())throw new InvalidOperationException("CLIMATE-RESULT-001: Native period/time mismatch.");
            return new PeriodResult(r,JsonSerializer.SerializeToElement(dictionary),hoys,times,metadata);
        });
    }
    public CalendarResult Calendar(CalendarRequest r)
    {
        if(r is null||r.SchemaVersion!="1.0"||r.Mode is not ("Calculate" or "FromHOY"))throw new InvalidOperationException("CLIMATE-CONTRACT-001: Calendar schema/mode invalid.");
        if(r.Mode=="Calculate"&&(r.Month is <1 or >12||r.Day<1||r.Day>DateTime.DaysInMonth(2001,r.Month)||r.Hour is <0 or >23||r.Minute is <0 or >59)||
            r.Mode=="FromHOY"&&(!double.IsFinite(r.HourOfYear)||r.HourOfYear<0||r.HourOfYear>=8760))throw new InvalidOperationException("CLIMATE-PERIOD-001: Valid non-leap date or HOY 0..<8760 required.");
        var inputs=r.Mode=="Calculate"?new Dictionary<string,object>{["_month_"]=r.Month,["_day_"]=r.Day,["_hour_"]=r.Hour,["_minute_"]=r.Minute}:new(){["_hoy"]=r.HourOfYear};
        return Solve(r.Mode=="Calculate"?"LB Calculate HOY":"LB HOY to DateTime",inputs,(c,metadata)=>
        { dynamic native=Values(c,"date").Single();var time=Date(native);return new CalendarResult(r,time,(int)native.doy,metadata); });
    }
}
