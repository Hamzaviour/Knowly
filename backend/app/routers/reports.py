from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(prefix="/reports", tags=["Reports"])

class ReportExportRequest(BaseModel):
    title: str
    markdown_content: str
    format: str = "markdown" # markdown, docx, pdf

@router.post("/export")
def export_report(req: ReportExportRequest):
    if req.format == "markdown":
        return Response(content=req.markdown_content, media_type="text/markdown")
    return {"status": "exported", "format": req.format, "title": req.title}
