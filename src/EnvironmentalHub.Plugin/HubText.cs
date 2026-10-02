using System.Text.Json;
using System.Text.RegularExpressions;
using EnvironmentalHub.Core;

namespace EnvironmentalHub.Plugin;

// Display translation only. Never mutate native values, identifiers or exported contracts.
internal static class HubText
{
    private static readonly Dictionary<string,string> Fields = new(StringComparer.Ordinal)
    {
        ["location"]="地點", ["dry_bulb_temperature"]="乾球溫度", ["dew_point_temperature"]="露點溫度",
        ["relative_humidity"]="相對濕度", ["wind_speed"]="風速", ["wind_direction"]="風向",
        ["direct_normal_rad"]="法向直射輻射", ["diffuse_horizontal_rad"]="水平散射輻射",
        ["global_horizontal_rad"]="水平總輻射", ["horizontal_infrared_rad"]="水平紅外線輻射",
        ["direct_normal_ill"]="法向直射照度", ["diffuse_horizontal_ill"]="水平散射照度",
        ["global_horizontal_ill"]="水平總照度", ["total_sky_cover"]="總雲量",
        ["barometric_pressure"]="大氣壓力", ["model_year"]="資料年份", ["ground_temperature"]="地溫",
        ["design_days"]="設計日", ["ashrae_zone"]="ASHRAE 氣候分區", ["koppen_zone"]="柯本氣候分區",
        ["clear_dir_norm_rad"]="晴空法向直射輻射", ["clear_diff_horiz_rad"]="晴空水平散射輻射",
        ["ann_heat_dday_996"]="全年供暖設計日 · 99.6%", ["ann_heat_dday_990"]="全年供暖設計日 · 99.0%",
        ["ann_cool_dday_004"]="全年冷房設計日 · 0.4%", ["ann_cool_dday_010"]="全年冷房設計日 · 1.0%",
        ["monthly_ddays_050"]="每月設計日 · 5.0%", ["monthly_ddays_100"]="每月設計日 · 10.0%",
        ["extreme_cold_week"]="極端寒冷週", ["extreme_hot_week"]="極端炎熱週", ["typical_weeks"]="典型週",
        ["source"]="資料來源", ["country"]="國家", ["city"]="城市", ["time-zone"]="時區",
        ["station_id"]="測站編號", ["depth"]="深度", ["latitude"]="緯度", ["longitude"]="經度", ["elevation"]="海拔"
    };
    private static readonly Dictionary<string,string> Codes = new(StringComparer.Ordinal)
    {
        ["RAD-CONTRACT-001"]="請使用版本 1.0 的有效分析輸入。",
        ["RAD-CONTRACT-002"]="模型、遮蔭、年時數清單與模擬設定不得為空值。",
        ["RAD-DOC-001"]="請啟用目標 Rhino 文件，確認模型單位後再執行。",
        ["RAD-DOC-002"]="目前文件已變更，請重新選取分析模型。",
        ["RAD-INPUT-001"]="請選取分析模型。",
        ["RAD-INPUT-002"]="模型物件已不存在，請重新選取。",
        ["RAD-INPUT-003"]="請選取有效的 Brep 或網格。",
        ["RAD-INPUT-004"]="分析模型與遮蔭物件不可重複或重疊選取。",
        ["RAD-SCALE-001"]="模型尺度無效，請確認物件尺寸與模型單位。",
        ["RAD-UNIT-001"]="請設定可換算為公尺的 Rhino 文件單位。",
        ["RAD-PARAM-001"]="網格間距須為大於零的有限值。",
        ["RAD-PARAM-002"]="北向旋轉須介於 −360° 至 360°。",
        ["RAD-PARAM-003"]="請確認 CPU 數量、正值感測點偏移及 0–1 地表反射率。",
        ["RAD-PERIOD-001"]="年時數須為不重複的整數 0–8759；空清單代表全年。",
        ["RAD-PRESET-001"]="分析品質標籤無效，請使用支援的設定。",
        ["RAD-PLUGIN-001"]="缺少必要的原生 Ladybug 元件，請檢查安裝路徑。",
        ["RAD-SOLVER-001"]="找不到 Radiance gendaymtx 或 rtrace，請檢查求解器安裝。",
        ["RAD-OUTPUT-001"]="請使用有效的絕對輸出資料夾路徑。",
        ["RAD-CONTEXT-001"]="未選取遮蔭環境；分析將假設沒有外部遮蔭。",
        ["RAD-GRID-001"]="網格相對模型較粗，請確認所需分析解析度。",
        ["RAD-THREAD-001"]="分析必須在 Rhino 介面執行緒執行。",
        ["RAD-WARNING-001"]="請先檢視並接受輸入警告，再執行分析。",
        ["RAD-GH-001"]="Grasshopper 求解已停用，請啟用後再執行。",
        ["RAD-SOLVER-005"]="設定的 Radiance 與 Ladybug 實際使用版本不同，請確認路徑。",
        ["RAD-RESULT-001"]="分析結果為空、含無效數值或網格未對齊。",
        ["RAD-RESULT-002"]="原生分析未提供圖例。",
        ["RAD-VIEW-001"]="結果網格顯示失敗；已保留前次預覽。",
        ["RAD-VIEW-002"]="結果網格無效或為空；已保留前次預覽。",
        ["RAD-VIEW-003"]="請開啟結果所屬的 Rhino 文件，再定位預覽。",
        ["RAD-VIEW-004"]="沒有可定位的預覽或作用中的視埠。",
        ["CLIMATE-THREAD-001"]="氣象操作必須在 Rhino 介面執行緒執行。",
        ["CLIMATE-CONTRACT-001"]="輸入格式或操作類型無效，請使用支援的版本 1.0 請求。",
        ["CLIMATE-EPW-003"]="EPW 檔案不存在或內容不支援，請選擇完整的非閏年逐時 EPW。",
        ["CLIMATE-FILE-001"]="請選擇存在且副檔名符合 STAT／DDY 格式的檔案。",
        ["CLIMATE-GH-001"]="Grasshopper 求解已停用，請啟用後重新匯入。",
        ["CLIMATE-PLUGIN-001"]="找不到必要的原生 Ladybug 元件，請確認安裝路徑。",
        ["CLIMATE-PERIOD-001"]="時間輸入無效；請檢查非閏年日期、HOY 範圍或每小時步數。",
        ["CLIMATE-PERIOD-002"]="目前僅支援非閏年 8,760 筆逐時 EPW 資料。",
        ["CLIMATE-LOCATION-001"]="緯度須為 −90 至 90°、經度 −180 至 180°、UTC 時差 −12 至 12 h，海拔須為有限值。",
        ["CLIMATE-LOCATION-002"]="時區由原生 Ladybug 依經度估算；分析前請核對所在地實際時區。",
        ["CLIMATE-INPUT-001"]="來源檔案或元件在執行期間已變更，請重新確認後執行。",
        ["CLIMATE-RESULT-001"]="原生結果缺失、資料型別不支援或數值與時間未對齊。",
        ["CLIMATE-DATA-001"]="部分原生輸出未提供；未產生替代數值。",
        ["CLIMATE-MONTHLY-001"]="逐時選取不會變更每月地溫資料組。",
        ["CLIMATE-MISSING-001"]="保留 EPW 缺值標記；統計已排除標記為缺值的數值。"
    };
    internal static string Field(string key) => Fields.GetValueOrDefault(key) ?? $"原生欄位：{key}";
    internal static string Frequency(string value) => value switch { "Hourly"=>"逐時", "Monthly"=>"逐月", "Daily"=>"逐日", _=>$"原生頻率（{value}）" };
    internal static string DayType(string? value) => value switch { "SummerDesignDay"=>"夏季設計日", "WinterDesignDay"=>"冬季設計日", _=>$"設計日類型：{value}" };
    internal static string Severity(string value) => value switch { "ERROR"=>"錯誤", "WARNING"=>"警告", "INFO"=>"資訊", _=>value };
    internal static string Diagnostic(Diagnostic d) => $"{Severity(d.Severity)} {d.Code}：{Message(d.Code,d.Message)}";
    private static string Message(string code,string original)
    {
        // Retain object/path details and unfamiliar solver messages, rather than guessing a translation.
        if (Codes.TryGetValue(code,out var translated))
            return translated + (code is "RAD-INPUT-002" or "RAD-INPUT-003" or "RAD-SCALE-001" ? $"\n原始診斷：{original}" : "");
        return $"原生診斷，請檢查輸入與求解器：{original}";
    }
    internal static string Error(Exception error)
    {
        try
        {
            using var json=JsonDocument.Parse(error.Message);
            var values=json.RootElement.ValueKind==JsonValueKind.Array?json.RootElement:json.RootElement.GetProperty("Diagnostics");
            return string.Join("\n",values.EnumerateArray().Select(d=>Diagnostic(new(
                d.TryGetProperty("Severity",out var severity)?severity.GetString()!:"ERROR",
                d.GetProperty("Code").GetString()!,d.GetProperty("Message").GetString()!))));
        }
        catch (Exception)
        {
            var match=Regex.Match(error.Message,@"^((?:RAD|CLIMATE)-[A-Z]+-\d{3}):\s*(.*)$",RegexOptions.Singleline);
            if(match.Success)return $"{match.Groups[1].Value}：{Message(match.Groups[1].Value,match.Groups[2].Value)}";
            return Regex.IsMatch(error.Message,@"[\u4e00-\u9fff]")?error.Message:$"操作未完成；原始診斷：{error.Message}";
        }
    }
}
