from pathlib import Path
from pypdf import PdfReader
import re
import unicodedata
from langchain_core.documents import Document

class Loader:
    def __init__(self):
        self.materials = Path("./files")
    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        # Normalize unicode (fixes weird accents, ligatures)
        text = unicodedata.normalize("NFKC", text)

        # Remove NULL bytes (CRITICAL for PostgreSQL)
        text = text.replace("\x00", "")

        # Remove problematic control characters
        text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)

        # Fix hyphenated line breaks (PDF artifact)
        text = re.sub(r"-\n", "", text)

        # Replace newlines with spaces (optional but recommended)
        text = re.sub(r"\n+", " ", text)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def content_to_doc(self) -> list[Document]:
        docs = []
        for pdf_file in self.materials.glob("*.pdf"):
            reader = PdfReader(pdf_file)
            name = pdf_file.name
            stem = pdf_file.stem
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            text = self.clean_text(text)

            docs.append(Document(page_content=text,metadata={"file_name":name, "stem":stem}))
        
        return docs