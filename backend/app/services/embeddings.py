import logging
from typing import Any

import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger("mediclear")

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "medical_reports"

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY,
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""],
)


def get_chroma_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


def index_report(report_id: str, raw_text: str) -> int:
    chunks = text_splitter.split_text(raw_text)

    if not chunks:
        logger.warning("No chunks generated for report %s", report_id)
        return 0

    vectors = embeddings_model.embed_documents(chunks)
    collection = get_chroma_collection()

    ids = [f"{report_id}_{i}" for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=[{"report_id": report_id, "chunk_index": i} for i in range(len(chunks))],
    )

    logger.info("Indexed %d chunks for report %s", len(chunks), report_id)
    return len(chunks)


def query_report(report_id: str, query: str, n_results: int = 5) -> list[str]:
    query_vector = embeddings_model.embed_query(query)
    collection = get_chroma_collection()

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        where={"report_id": report_id},
    )

    documents = results.get("documents", [[]])[0]
    logger.info("Query returned %d chunks for report %s", len(documents), report_id)
    return documents