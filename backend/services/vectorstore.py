"""
Vector Store Service

Converts markdown files to vector stores using FAISS with markdown-based text splitting
and MistralAI embeddings.
"""

from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_core.documents import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
import faiss
from uuid import uuid4
import logging

logger = logging.getLogger("vectorstore")


# ==============================================================================
# VECTOR STORE SERVICE
# ==============================================================================

def create_vector_store_from_markdown(md_file_path: str) -> FAISS:
    """
    Create a FAISS vector store from a markdown file.
    
    Process:
    1. Read markdown file
    2. Split by markdown headers (# ## ###)
    3. Embed chunks using MistralAI embeddings
    4. Store in FAISS vector store
    
    Args:
        md_file_path: Path to markdown file
        
    Returns:
        FAISS vector store ready for querying
    """
    try:
        logger.info(f"[VectorStore] Creating vector store from: {md_file_path}")
        
        # Read markdown file
        md_path = Path(md_file_path)
        if not md_path.exists():
            logger.error(f"[VectorStore] Markdown file not found: {md_file_path}")
            raise FileNotFoundError(f"Markdown file not found: {md_file_path}")
        
        markdown_content = md_path.read_text(encoding="utf-8")
        logger.debug(f"[VectorStore] Read markdown content: {len(markdown_content)} characters")
        
        # Initialize embeddings
        logger.debug(f"[VectorStore] Initializing MistralAI embeddings...")
        embeddings = MistralAIEmbeddings(model="mistral-embed")
        
        # Initialize markdown header splitter
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        
        # Split markdown into documents
        logger.debug(f"[VectorStore] Splitting markdown by headers...")
        md_header_splits = markdown_splitter.split_text(markdown_content)
        logger.debug(f"[VectorStore] Split into {len(md_header_splits)} documents")
        
        if not md_header_splits:
            logger.warning(f"[VectorStore] ⚠ No content extracted from markdown: {md_file_path}")
            # Create at least one document from the entire content
            md_header_splits = [
                Document(
                    page_content=markdown_content,
                    metadata={"source": md_path.name}
                )
            ]
            logger.warning(f"[VectorStore] Created fallback document with full content")
        
        # Get embedding dimension
        logger.debug(f"[VectorStore] Computing embedding dimension...")
        embedding_dim = len(embeddings.embed_query("hello world"))
        logger.debug(f"[VectorStore] Embedding dimension: {embedding_dim}")
        
        # Initialize FAISS index
        logger.debug(f"[VectorStore] Initializing FAISS index...")
        index = faiss.IndexFlatL2(embedding_dim)
        
        # Create vector store
        vector_store = FAISS(
            embedding_function=embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        
        # Add documents with UUIDs
        logger.debug(f"[VectorStore] Adding {len(md_header_splits)} documents to vector store...")
        uuids = [str(uuid4()) for _ in range(len(md_header_splits))]
        vector_store.add_documents(documents=md_header_splits, ids=uuids)
        logger.debug(f"[VectorStore] Documents added successfully")
        
        # Save vector store to disk
        vector_store_dir = Path(__file__).parent.parent / "workers" / "contract" / "vectorstores"
        vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Use markdown filename as key for vector store
        store_name = md_path.stem
        store_path = vector_store_dir / store_name
        
        logger.debug(f"[VectorStore] Saving vector store to: {store_path}")
        vector_store.save_local(str(store_path))
        
        logger.info(
            f"[VectorStore] ✓ Vector store created and saved successfully. "
            f"Documents: {len(md_header_splits)}, "
            f"Embedding dim: {embedding_dim}, "
            f"Store path: {store_path}"
        )
        
        return vector_store
        
    except Exception as e:
        logger.error(f"[VectorStore] ✗ Error creating vector store: {str(e)}", exc_info=True)
        raise


def load_vector_store_from_disk(md_filename: str) -> FAISS:
    """
    Load a previously saved vector store from disk.
    
    Args:
        md_filename: Name of markdown file (without path, e.g., "company_contract.md")
        
    Returns:
        FAISS vector store loaded from disk
    """
    try:
        logger.info(f"[VectorStore] Loading vector store for: {md_filename}")
        
        # Get the store name from filename (without extension)
        store_name = Path(md_filename).stem
        logger.debug(f"[VectorStore] Store name (stem): {store_name}")
        
        # Load vector store from disk
        vector_store_dir = Path(__file__).parent.parent / "workers" / "contract" / "vectorstores"
        store_path = vector_store_dir / store_name
        
        logger.debug(f"[VectorStore] Looking for store at: {store_path}")
        logger.debug(f"[VectorStore] Store path exists: {store_path.exists()}")
        
        if not store_path.exists():
            available_stores = list(vector_store_dir.glob("*"))
            logger.error(f"[VectorStore] Vector store not found at: {store_path}")
            logger.error(f"[VectorStore] Available stores: {[s.name for s in available_stores]}")
            raise FileNotFoundError(f"Vector store not found at: {store_path}")
        
        # Initialize embeddings
        logger.debug(f"[VectorStore] Initializing MistralAI embeddings...")
        embeddings = MistralAIEmbeddings(model="mistral-embed")
        
        # Load from disk
        logger.debug(f"[VectorStore] Loading FAISS index from: {store_path}")
        vector_store = FAISS.load_local(str(store_path), embeddings, allow_dangerous_deserialization=True)
        
        logger.info(f"[VectorStore] ✓ Vector store successfully loaded from disk: {store_path}")
        return vector_store
        
    except Exception as e:
        logger.error(f"[VectorStore] ✗ Error loading vector store: {str(e)}", exc_info=True)
        raise


def get_vector_store_retriever(vector_store: FAISS, search_type: str = "similarity", k: int = 3):
    """
    Convert vector store to a retriever.
    
    Args:
        vector_store: FAISS vector store
        search_type: Type of search ("similarity", "mmr", etc.)
        k: Number of results to return
        
    Returns:
        Retriever object for querying
    """
    return vector_store.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k}
    )
