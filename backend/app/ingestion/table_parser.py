import pandas as pd
import io
import json
from typing import Dict, Any, List, Optional

class TableIntelligenceEngine:
    """
    Analyzes spreadsheets (XLSX, CSV) into structured DataFrames,
    detects schema, computes summaries, and executes deterministic data queries.
    """
    
    @staticmethod
    def parse_spreadsheet(file_path: str) -> Dict[str, Any]:
        if file_path.endswith(".csv"):
            df_dict = {"Sheet1": pd.read_csv(file_path)}
        else:
            df_dict = pd.read_excel(file_path, sheet_name=None)
        
        tables_summary = []
        sheets_data = {}
        
        for sheet_name, df in df_dict.items():
            # Clean dataframe
            df = df.dropna(how="all").fillna("")
            schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
            sample_records = df.head(10).to_dict(orient="records")
            num_rows, num_cols = df.shape
            
            # Numeric summaries
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            stats = df[numeric_cols].describe().to_dict() if numeric_cols else {}
            
            sheets_data[sheet_name] = {
                "schema": schema,
                "rows": num_rows,
                "columns": num_cols,
                "sample": sample_records,
                "statistics": stats
            }
            
            # Create a textual representation for search indexing
            tables_summary.append(
                f"Sheet: {sheet_name} ({num_rows} rows, {num_cols} cols)\n"
                f"Columns: {', '.join(schema.keys())}\n"
                f"Sample Top Rows:\n{df.head(5).to_markdown(index=False)}"
            )

        return {
            "is_tabular": True,
            "sheets": sheets_data,
            "text_representation": "\n\n".join(tables_summary)
        }

    @staticmethod
    def execute_analysis(file_path: str, python_code: str) -> Dict[str, Any]:
        """
        Safely executes analytical python query on the dataframe.
        """
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            sheets = pd.read_excel(file_path, sheet_name=None)
            df = next(iter(sheets.values()))
            
        local_scope = {"pd": pd, "df": df, "result": None}
        try:
            exec(python_code, {}, local_scope)
            res = local_scope.get("result")
            if isinstance(res, pd.DataFrame):
                return {"success": True, "output": res.to_dict(orient="records"), "type": "table"}
            elif isinstance(res, (pd.Series, dict, list, int, float, str)):
                return {"success": True, "output": res, "type": "scalar"}
            return {"success": True, "output": str(res), "type": "text"}
        except Exception as e:
            return {"success": False, "error": str(e)}
