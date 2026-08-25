from typing import Dict, Any, List

class ReportAgent:
    """
    Generates publication-ready reports in Markdown, HTML, and structured formats.
    Supported report types: Executive Summary, Compliance Report, Contract Diff, Financial Review.
    """
    
    @staticmethod
    def generate_markdown_report(report_data: Dict[str, Any]) -> str:
        title = report_data.get("research_title", "Document AI Report")
        summary = report_data.get("executive_summary", "")
        findings = report_data.get("findings", [])
        recommendations = report_data.get("recommendations", [])
        
        md = [f"# {title}\n", f"## Executive Summary\n{summary}\n"]
        
        if findings:
            md.append("## Key Findings & Evidence\n")
            for idx, item in enumerate(findings, 1):
                md.append(f"### {idx}. {item.get('sub_topic', 'Finding')}")
                for kf in item.get("key_findings", []):
                    md.append(f"- {kf}")
                for cit in item.get("citations", []):
                    md.append(f"  > {cit.get('quote_snippet')} {cit.get('badge')}")
                md.append("")
                
        if recommendations:
            md.append("## Recommendations\n")
            for rec in recommendations:
                md.append(f"- {rec}")
                
        return "\n".join(md)
