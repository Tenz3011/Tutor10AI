from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document

class Loader:
    def __init__(self):
        self.materials = Path("./files")

    def content_to_doc(self) -> list[Document]:
        docs = []
        for pdf_file in self.materials.glob("*.pdf"):
            reader = PdfReader(pdf_file)
            name = pdf_file.name
            stem = pdf_file.stem
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            docs.append(Document(page_content=text,metadata={"file_name":name, "stem":stem}))
        
        return docs