"""Getting documents INTO the vector database.

    PDF file -> pages -> chunks (~1000 characters) -> embeddings -> vector store

Two entry points share the same steps:
  * ingest_pdf()          - one PDF on disk (used by the upload endpoint)
  * ingest_stored_pdfs()  - every PDF in the document store
                            (local: .meridian/uploads/, cloud: the GCS bucket)
"""
import hashlib
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from exceptions import IngestionException
from rag import document_store
from rag.vector_store import get_vector_store
from logger import GLOBAL_LOGGER as logger

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


def split_into_chunks(document: Document) -> list[Document]:
    """Split a document into smaller chunks using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return text_splitter.split_documents([document])


def _chunk_id(chunk: Document, position: int) -> str:
    """Generate a unique chunk ID based on the document's metadata and chunk index."""
    key = f"{chunk.metadata.get('source')}|{chunk.metadata.get('page')}|{position}"
    return hashlib.sha1(key.encode()).hexdigest()


def ingest_pdf(file_path: str, source: str) -> dict[str, list[Document]]:
    """Ingest a PDF file, split it into chunks, and store them in the vector store.

    Args:
        file_path (str): The path to the PDF file.
        source (str): The source identifier for the document.

    Returns:
        dict[str, list[Document]]: A dictionary containing the original document and its chunks.
    """
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
    except Exception as e:
        raise IngestionException(f"Failed to load PDF: {e}") from e
    
    for page in pages:
        page.metadata["source"] = source

    chunks = split_into_chunks(pages)

    if chunks:
        ids = [_chunk_id(chunk, i) for i, chunk in enumerate(chunks)]
        get_vector_store().add_documents(chunks, ids=ids)

    return {
        "pages": len(pages),
        "chunks": len(chunks)
    }


def ingest_stored_pdfs() -> dict:
    """Ingest all stored PDFs from the local upload directory.

    Returns:
        dict[str, int]: A dictionary containing the total number of pages and chunks ingested.
    """
    logger.info("Starting ingestion of stored PDFs...")
    total_pages = 0
    total_chunks = 0

    for pdf_iterator in document_store.pdfs():
        for file_path, source in pdf_iterator:
            result = ingest_pdf(file_path, source)
            total_pages += result["pages"]
            total_chunks += result["chunks"]

    if total_pages == 0:
        logger.warning("No PDFs found to ingest.", local_upload_dir=document_store.location())
    
    logger.info(f"Finished ingestion of stored PDFs. Total pages: {total_pages}, Total chunks: {total_chunks}")
    return {
        "total_pages": total_pages,
        "total_chunks": total_chunks
    }
