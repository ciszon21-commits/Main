using System.Runtime.InteropServices;
using Eto.Drawing;
using Eto.Forms;
using Rhino.UI;
namespace EnvironmentalHub.Plugin;

public sealed class HubOverviewPanel:Panel
{
    public HubOverviewPanel()
    {
        var layout=new DynamicLayout{Padding=16,Spacing=new Size(8,14)};
        layout.AddRow(HubUi.Header("建築性能分析","從模型到分析結果的建築環境模擬工作平台。"));
        var workflow=new DynamicLayout{Spacing=new Size(8,6)};
        foreach(var step in new[]{("01  幾何／模型",HubTopic.Model),("02  環境／氣象",HubTopic.Environment),
            ("03  模擬設定",HubTopic.Settings),("04  檢核／執行",HubTopic.Run),("05  分析結果",HubTopic.Results),("06  比較／匯出",HubTopic.Compare)})
            workflow.AddRow(HubUi.WorkflowLine(step.Item1,step.Item2));
        layout.AddRow(HubUi.Section("分析流程",workflow));
        var solar=new Button{Text="開始日射分析"};
        solar.Click+=(_,_)=>HubUi.OpenModule(this,typeof(RadiationPanel));
        var sunpath=new Button{Text="開啟太陽路徑"};
        sunpath.Click+=(_,_)=>HubUi.OpenModule(this,typeof(SunPathPanel));
        layout.AddRow(HubUi.Section("模擬分析",HubTopic.Run,HubUi.Hint("日射分析 · 已可使用\n分析模型表面的入射太陽能量與遮蔭影響。\nLadybug / Radiance · kWh/m²"),HubUi.ModuleAction(solar,typeof(RadiationPanel)),
            HubUi.Hint("太陽路徑 · 原生太陽位置與幾何\n全年／指定日期日弧、北向、投影與視埠定位。"),HubUi.ModuleAction(sunpath,typeof(SunPathPanel)),
            HubUi.Hint("採光 · 熱舒適 · 能耗 · 碳排 · 風環境\n後續整合範圍，目前尚未提供可執行流程。\nHoneybee / OpenStudio / EnergyPlus / Eddy3D")));
        var climateTools=new DynamicLayout{Spacing=new Size(8,8)};
        foreach(var module in HubUi.Modules.Skip(1).Take(4))
        {
            var open=new Button{Text="開啟 "+module.Label};var type=module.Panel;open.Click+=(_,_)=>HubUi.OpenModule(this,type);
            climateTools.AddRow(HubUi.ModuleAction(open,type));
        }
        layout.AddRow(HubUi.Section("環境工具",HubTopic.Environment,climateTools,HubUi.Hint("檢視 EPW 氣象、建立地點、匯入設計條件或定義分析時間。各工具分別保留輸入與結果。")));
        layout.AddRow(HubUi.Hint("已盤點 122 個 Ladybug 入口，其中 9 項已接入為獨立功能。各項支援範圍請見功能表。執行前檢查求解環境與輸入；匯出包含參數、單位與資料來源。"));
        layout.Add(null);HubUi.Mount(this,layout);
    }
}
