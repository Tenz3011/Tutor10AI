from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from rag.loader import Loader
import os
from fastapi import FastAPI

load_dotenv()
app = FastAPI()

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
    chunk_size=1000, 
    chunk_overlap=200,  
    add_start_index=True,  
    )
    all_splits = text_splitter.split_documents(docs)

    store.add_documents(documents=all_splits)