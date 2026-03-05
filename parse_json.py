import pandas as pd
import json

def main():
    excel_file = "reference/容積計算.xlsx"
    out = {}
    try:
        xl = pd.ExcelFile(excel_file)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            out[sheet] = {
                "columns": list(df.columns),
                "data": json.loads(df.head(5).to_json(orient='records', force_ascii=False))
            }
        with open("excel_info.json", "w", encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("Written to excel_info.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
