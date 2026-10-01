using System.Runtime.InteropServices;
using System.Text.Json;
using Eto.Drawing;
using Eto.Forms;
using EnvironmentalHub.Core;
using EnvironmentalHub.Adapters;
namespace EnvironmentalHub.Plugin;

[Guid("06843693-df8a-421c-938b-96e2b9e88066")]
public sealed class TimePanel:Panel
{
    private readonly DropDown mode=new();
    private readonly NumericStepper sm=N(1,12,1),sd=N(1,31,1),sh=N(0,23,0),em=N(1,12,12),ed=N(1,31,31),eh=N(0,23,23),step=N(1,60,1);
    private readonly NumericStepper month=N(1,12,1),day=N(1,31,1),hour=N(0,23,0),minute=N(0,59,0),hoy=new(){MinValue=0,MaxValue=8759.9999,DecimalPlaces=4,Width=120};
    private readonly Label status=HubUi.Hint("Choose a time operation."),summary=HubUi.Hint("No time result yet");
    private readonly Button run=new(){Text="Build analysis period"},export=new(){Text="Export time result JSON…",Enabled=false};
    private string? result;
    private bool updating;
    private static NumericStepper N(int min,int max,int value)=>new(){MinValue=min,MaxValue=max,Value=value,DecimalPlaces=0,Width=76};
    public string StatusText=>status.Text;
    public string SummaryText=>summary.Text;
    public string? CompletedResultJson=>result;
    public TimePanel()
    {
        mode.Items.Add("Analysis period");mode.Items.Add("Date → HOY");mode.Items.Add("HOY → date");mode.SelectedIndex=0;
        var period=new DynamicLayout{Padding=12,Spacing=new Size(8,8)};
        var periodFields=new DynamicLayout{Spacing=new Size(6,8)};
        periodFields.AddRow(null,new Label{Text="Start"},new Label{Text="End"});
        periodFields.AddRow(new Label{Text="Month"},sm,em);periodFields.AddRow(new Label{Text="Day"},sd,ed);periodFields.AddRow(new Label{Text="Hour"},sh,eh);
        var stepField=new DynamicLayout{Spacing=new Size(8,8)};stepField.AddRow(new Label{Text="Steps / hour"},step);
        period.AddRow(periodFields);period.AddRow(stepField);period.AddRow(HubUi.Hint("Supported: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60. End hour is inclusive; native cross-year and overnight rules apply."));
        var pg=HubUi.Section("02  Analysis period",HubTopic.Settings,period);
        var calendar=new DynamicLayout{Padding=12,Spacing=new Size(8,8)};
        calendar.AddRow(new Label{Text="Month"},month);calendar.AddRow(new Label{Text="Day"},day);
        calendar.AddRow(new Label{Text="Hour"},hour);calendar.AddRow(new Label{Text="Minute"},minute);calendar.AddRow(new Label{Text="HOY"},hoy);
        var cg=HubUi.Section("02  Calendar conversion",HubTopic.Settings,calendar);cg.Visible=false;
        void Changed(){if(!updating)status.Text=result is null?"Ready to calculate":"Previous result • Calculate again to update";}
        mode.SelectedIndexChanged+=(_,_)=>{pg.Visible=mode.SelectedIndex==0;cg.Visible=mode.SelectedIndex!=0;
            month.Enabled=day.Enabled=hour.Enabled=minute.Enabled=mode.SelectedIndex==1;hoy.Enabled=mode.SelectedIndex==2;
            run.Text=mode.SelectedIndex==0?"Build analysis period":"Convert time";Changed();};
        foreach(var n in new[]{sm,sd,sh,em,ed,eh,step,month,day,hour,minute,hoy})n.ValueChanged+=(_,_)=>Changed();
        run.Click+=(_,_)=>Guard(()=>{
            if(mode.SelectedIndex==0)ExecutePeriodJson(JsonSerializer.Serialize(new PeriodRequest{StartMonth=(int)sm.Value,StartDay=(int)sd.Value,StartHour=(int)sh.Value,EndMonth=(int)em.Value,EndDay=(int)ed.Value,EndHour=(int)eh.Value,TimeStep=(int)step.Value}));
            else ExecuteCalendarJson(JsonSerializer.Serialize(new CalendarRequest{Mode=mode.SelectedIndex==1?"Calculate":"FromHOY",Month=(int)month.Value,Day=(int)day.Value,Hour=(int)hour.Value,Minute=(int)minute.Value,HourOfYear=hoy.Value}));});
        export.Click+=(_,_)=>Guard(()=>{if(result is null)return;var dialog=new SaveFileDialog{FileName="time_result.json"};dialog.Filters.Add(new FileFilter("Time JSON",".json"));if(dialog.ShowDialog(this)==DialogResult.Ok)File.WriteAllText(dialog.FileName,result);});
        var layout=new DynamicLayout{Padding=16,Spacing=new Size(8,14)};
        layout.AddRow(HubUi.Header("Time & periods","Define when analysis runs, with native Ladybug calendar rules.",typeof(TimePanel)));layout.AddRow(HubUi.Navigation(typeof(TimePanel)));
        layout.AddRow(HubUi.Section("01  Operation",HubTopic.Settings,mode));layout.AddRow(pg);layout.AddRow(cg);layout.AddRow(HubUi.Section("03  Calculate",HubTopic.Run,run,status));layout.AddRow(HubUi.Section("04  Result",HubTopic.Results,summary,export));
        layout.AddRow(HubUi.Hint("Non-leap local standard time • HOY 0 = Jan 1 00:00. Fractional HOY is retained; EPW weather requests currently accept integer hours only."));layout.Add(null);HubUi.Mount(this,layout);
    }
    private LadybugTimeAdapter Adapter()
    {using var config=JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!,"hub.config.json")));return new(System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!));}
    private void Guard(Action action){try{action();}catch(Exception e){status.Text=(result is null?"Failed\n":"Failed • Previous result retained\n")+e.Message;}}
    public string ExecutePeriodJson(string json)=>Execute(()=>{var r=Adapter().Period(JsonSerializer.Deserialize<PeriodRequest>(json)!);
        updating=true;try{mode.SelectedIndex=0;sm.Value=r.InputParameters.StartMonth;sd.Value=r.InputParameters.StartDay;sh.Value=r.InputParameters.StartHour;
            em.Value=r.InputParameters.EndMonth;ed.Value=r.InputParameters.EndDay;eh.Value=r.InputParameters.EndHour;step.Value=r.InputParameters.TimeStep;}finally{updating=false;}
        var note=r.Period.GetProperty("end_day").GetInt32()!=r.InputParameters.EndDay?"\nNative end day normalized to "+r.Period.GetProperty("end_day").GetInt32():"";
        return (JsonSerializer.Serialize(r),$"{r.HoursOfYear.Length:N0} time steps\nFirst HOY {r.HoursOfYear.First():0.####} • Last HOY {r.HoursOfYear.Last():0.####}\n{r.InputParameters.TimeStep} steps / hour • Native period included in export"+note);});
    public string ExecuteCalendarJson(string json)=>Execute(()=>{var r=Adapter().Calendar(JsonSerializer.Deserialize<CalendarRequest>(json)!);
        updating=true;try{mode.SelectedIndex=r.InputParameters.Mode=="Calculate"?1:2;month.Value=r.Time.Month;day.Value=r.Time.Day;hour.Value=r.Time.Hour;minute.Value=r.Time.Minute;hoy.Value=r.InputParameters.Mode=="FromHOY"?r.InputParameters.HourOfYear:r.Time.HourOfYear;}finally{updating=false;}
        return(JsonSerializer.Serialize(r),$"{r.Time.Month:00}/{r.Time.Day:00}  {r.Time.Hour:00}:{r.Time.Minute:00}\nHOY {r.Time.HourOfYear:0.####} • DOY {r.DayOfYear}");});
    private string Execute(Func<(string Json,string Summary)> action)
    {run.Enabled=false;try{var next=action();result=next.Json;summary.Text=next.Summary;status.Text="Calculated • Original Ladybug";export.Enabled=true;return result;}
     catch(Exception e){status.Text=(result is null?"Failed\n":"Failed • Previous result retained\n")+e.Message;throw;}finally{run.Enabled=true;}}
}
