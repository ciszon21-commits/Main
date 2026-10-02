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
    private readonly Label status=HubUi.Hint("選擇時間操作。"),summary=HubUi.Hint("尚無時間計算結果");
    private readonly Button run=new(){Text="建立分析期間"},export=new(){Text="匯出時間結果 JSON…",Enabled=false};
    private string? result;
    private bool updating;
    private static NumericStepper N(int min,int max,int value)=>new(){MinValue=min,MaxValue=max,Value=value,DecimalPlaces=0,Width=76};
    public string StatusText=>status.Text;
    public string SummaryText=>summary.Text;
    public string? CompletedResultJson=>result;
    public TimePanel()
    {
        mode.Items.Add("分析期間");mode.Items.Add("日期 → 年時數 (HOY)");mode.Items.Add("年時數 (HOY) → 日期");mode.SelectedIndex=0;
        var period=new DynamicLayout{Padding=12,Spacing=new Size(8,8)};
        var periodFields=new DynamicLayout{Spacing=new Size(6,8)};
        periodFields.AddRow(null,new Label{Text="起始"},new Label{Text="結束"});
        periodFields.AddRow(new Label{Text="月"},sm,em);periodFields.AddRow(new Label{Text="日"},sd,ed);periodFields.AddRow(new Label{Text="時"},sh,eh);
        var stepField=new DynamicLayout{Spacing=new Size(8,8)};stepField.AddRow(new Label{Text="每小時步數"},step);
        period.AddRow(periodFields);period.AddRow(stepField);period.AddRow(HubUi.Hint("支援每小時 1、2、3、4、5、6、10、12、15、20、30、60 步。包含結束小時；沿用原生跨年與跨夜規則。"));
        var pg=HubUi.Section("02  分析期間",HubTopic.Settings,period);
        var calendar=new DynamicLayout{Padding=12,Spacing=new Size(8,8)};
        calendar.AddRow(new Label{Text="月"},month);calendar.AddRow(new Label{Text="日"},day);
        calendar.AddRow(new Label{Text="時"},hour);calendar.AddRow(new Label{Text="分"},minute);calendar.AddRow(new Label{Text="年時數 (HOY)"},hoy);
        var cg=HubUi.Section("02  日期換算",HubTopic.Settings,calendar);cg.Visible=false;
        void Changed(){if(!updating)status.Text=result is null?"可開始計算":"前次結果 · 重新計算以更新";}
        mode.SelectedIndexChanged+=(_,_)=>{pg.Visible=mode.SelectedIndex==0;cg.Visible=mode.SelectedIndex!=0;
            month.Enabled=day.Enabled=hour.Enabled=minute.Enabled=mode.SelectedIndex==1;hoy.Enabled=mode.SelectedIndex==2;
            run.Text=mode.SelectedIndex==0?"建立分析期間":"換算時間";Changed();};
        foreach(var n in new[]{sm,sd,sh,em,ed,eh,step,month,day,hour,minute,hoy})n.ValueChanged+=(_,_)=>Changed();
        run.Click+=(_,_)=>Guard(()=>{
            if(mode.SelectedIndex==0)ExecutePeriodJson(JsonSerializer.Serialize(new PeriodRequest{StartMonth=(int)sm.Value,StartDay=(int)sd.Value,StartHour=(int)sh.Value,EndMonth=(int)em.Value,EndDay=(int)ed.Value,EndHour=(int)eh.Value,TimeStep=(int)step.Value}));
            else ExecuteCalendarJson(JsonSerializer.Serialize(new CalendarRequest{Mode=mode.SelectedIndex==1?"Calculate":"FromHOY",Month=(int)month.Value,Day=(int)day.Value,Hour=(int)hour.Value,Minute=(int)minute.Value,HourOfYear=hoy.Value}));});
        export.Click+=(_,_)=>Guard(()=>{if(result is null)return;var dialog=new SaveFileDialog{FileName="time_result.json"};dialog.Filters.Add(new FileFilter("時間結果 JSON",".json"));if(dialog.ShowDialog(this)==DialogResult.Ok)File.WriteAllText(dialog.FileName,result);});
        var layout=new DynamicLayout{Padding=16,Spacing=new Size(8,14)};
        layout.AddRow(HubUi.Header("時間與分析期間","定義分析時間，沿用 Ladybug 原生日期與時間規則。",typeof(TimePanel)));layout.AddRow(HubUi.Section("01  操作類型",HubTopic.Settings,mode));layout.AddRow(pg);layout.AddRow(cg);layout.AddRow(HubUi.Section("03  計算",HubTopic.Run,run,status));layout.AddRow(HubUi.Section("04  分析結果",HubTopic.Results,summary,export));
        layout.AddRow(HubUi.Hint("採非閏年的當地標準時間；HOY 0 為 1 月 1 日 00:00。保留小數年時數；EPW 氣象分析目前僅接受整數小時。"));layout.Add(null);HubUi.Mount(this,layout);
    }
    private LadybugTimeAdapter Adapter()
    {using var config=JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!,"hub.config.json")));return new(System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!));}
    private void Guard(Action action){try{action();}catch(Exception e){status.Text=(result is null?"執行失敗\n":"執行失敗 · 已保留前次結果\n")+HubText.Error(e);}}
    public string ExecutePeriodJson(string json)=>Execute(()=>{var r=Adapter().Period(JsonSerializer.Deserialize<PeriodRequest>(json)!);
        updating=true;try{mode.SelectedIndex=0;sm.Value=r.InputParameters.StartMonth;sd.Value=r.InputParameters.StartDay;sh.Value=r.InputParameters.StartHour;
            em.Value=r.InputParameters.EndMonth;ed.Value=r.InputParameters.EndDay;eh.Value=r.InputParameters.EndHour;step.Value=r.InputParameters.TimeStep;}finally{updating=false;}
        var note=r.Period.GetProperty("end_day").GetInt32()!=r.InputParameters.EndDay?"\n原生規則將結束日調整為 "+r.Period.GetProperty("end_day").GetInt32():"";
        return (JsonSerializer.Serialize(r),$"{r.HoursOfYear.Length:N0} 個時間步\n起始 HOY {r.HoursOfYear.First():0.####} • 結束 HOY {r.HoursOfYear.Last():0.####}\n{r.InputParameters.TimeStep} 步／小時 · 匯出包含原生期間"+note);});
    public string ExecuteCalendarJson(string json)=>Execute(()=>{var r=Adapter().Calendar(JsonSerializer.Deserialize<CalendarRequest>(json)!);
        updating=true;try{mode.SelectedIndex=r.InputParameters.Mode=="Calculate"?1:2;month.Value=r.Time.Month;day.Value=r.Time.Day;hour.Value=r.Time.Hour;minute.Value=r.Time.Minute;hoy.Value=r.InputParameters.Mode=="FromHOY"?r.InputParameters.HourOfYear:r.Time.HourOfYear;}finally{updating=false;}
        return(JsonSerializer.Serialize(r),$"{r.Time.Month:00}/{r.Time.Day:00}  {r.Time.Hour:00}:{r.Time.Minute:00}\n年時數 (HOY) {r.Time.HourOfYear:0.####} · 年日數 (DOY) {r.DayOfYear}");});
    private string Execute(Func<(string Json,string Summary)> action)
    {run.Enabled=false;try{var next=action();result=next.Json;summary.Text=next.Summary;status.Text="計算完成 · 原生 Ladybug";export.Enabled=true;return result;}
     catch(Exception e){status.Text=(result is null?"執行失敗\n":"執行失敗 · 已保留前次結果\n")+HubText.Error(e);throw;}finally{run.Enabled=true;}}
}
