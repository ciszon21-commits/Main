import pandas as pd
import json

def main():
    excel_file = "reference/容積計算.xlsx"
    try:
        xl = pd.ExcelFile(excel_file)
        print("Sheets:", xl.sheet_names)
        for sheet in xl.sheet_names:
            print(f"\n--- Sheet: {sheet} ---")
            df = xl.parse(sheet)
            print("Columns:", list(df.columns))
            print("============= Head 2 =============")
            print(df.head(2).to_string())
    except Exception as e:
        print(f"Error reading excel: {e}")

if __name__ == "__main__":
    main()
