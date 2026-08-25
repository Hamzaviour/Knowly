from typing import Dict, Any, List
from app.ingestion.table_parser import TableIntelligenceEngine

class AnalystAgent:
    """
    Performs deterministic calculations, table analysis, aggregations,
    and numerical queries over spreadsheet documents using DataFrames.
    """
    
    @staticmethod
    def analyze_table_data(file_path: str, user_question: str) -> Dict[str, Any]:
        # Generate targeted python analysis code
        code = """
# Auto-generated analysis script
if isinstance(df, pd.DataFrame):
    # Try finding highest/lowest values or summary
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        primary_col = numeric_cols[0]
        max_idx = df[primary_col].idxmax()
        result = {
            "primary_metric": primary_col,
            "max_row": df.loc[max_idx].to_dict(),
            "summary": df[numeric_cols].describe().to_dict()
        }
    else:
        result = df.head(10).to_dict(orient='records')
"""
        exec_res = TableIntelligenceEngine.execute_analysis(file_path, code)
        return {
            "agent": "AnalystAgent",
            "question": user_question,
            "execution": exec_res
        }
