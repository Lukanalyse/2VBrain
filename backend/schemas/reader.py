from pydantic import BaseModel


class MarkdownDocumentResponse(BaseModel):
    library_item_id: int
    markdown_path: str
    content: str


class MarkdownDocumentUpdate(BaseModel):
    content: str

