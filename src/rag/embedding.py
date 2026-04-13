from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from src.rag.loader import Loader
from langchain_postgres import PGVector
import re
import os
load_dotenv()


def get_store(collection: str) -> PGVector:
    """Returns the PGVector Store"""
    embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL")) # type: ignore
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection,
        connection=os.getenv("DB_CONNECTION"), # type: ignore
        use_jsonb=True
    )
    return vector_store


def embed():
    loader = Loader()
    docs = loader.content_to_doc()
    store = get_store("files")

    store.delete_collection()

    store = get_store("files") 

    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, 
    chunk_overlap=200,  
    add_start_index=True,  
    )
    all_splits = text_splitter.split_documents(docs)

    store.add_documents(documents=all_splits)

def clean_text(text: str):
    text = text.replace("\x00", "")

    # Remove other problematic control characters
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)

    return text
