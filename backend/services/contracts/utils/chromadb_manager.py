"""
ChromaDB Vector Storage Manager
File-based persistent storage for contract clause embeddings and metadata
"""

import os
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manager for ChromaDB vector storage (file-based persistent)"""
    
    # Collection names
    CONTRACT_CLAUSES_COLLECTION = "contract_clauses"
    PRECEDENT_PLAYBOOK_COLLECTION = "precedent_playbook"
    STATUTORY_REFERENCES_COLLECTION = "statutory_references"
    
    def __init__(self, db_path: str = None):
        """
        Initialize ChromaDB client with persistent file-based storage
        
        Args:
            db_path: Path to ChromaDB storage directory (default: backend/chromadb_data)
        """
        if db_path is None:
            # Use chromadb_data directory in backend
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "chromadb_data"
            )
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Create persistent client
        self.client = chromadb.PersistentClient(path=db_path)
        self.db_path = db_path
        
        logger.info(f"Initialized ChromaDB with persistent storage at {db_path}")
        
        # Initialize or get default collections
        self._init_collections()
    
    def _init_collections(self):
        """Initialize default collections for clauses, precedents, and statutes"""
        try:
            # Get or create contract clauses collection
            self.clauses_collection = self.client.get_or_create_collection(
                name=self.CONTRACT_CLAUSES_COLLECTION,
                metadata={
                    "description": "Extracted contract clauses with embeddings",
                    "version": "1.0",
                    "embedding_model": "mistral-embed",
                    "embedding_dimension": 1536
                }
            )
            
            # Get or create precedent playbook collection
            self.playbook_collection = self.client.get_or_create_collection(
                name=self.PRECEDENT_PLAYBOOK_COLLECTION,
                metadata={
                    "description": "Standard playbook precedents for comparison",
                    "version": "1.0",
                    "embedding_model": "mistral-embed",
                    "embedding_dimension": 1536
                }
            )
            
            # Get or create statutory references collection
            self.statute_collection = self.client.get_or_create_collection(
                name=self.STATUTORY_REFERENCES_COLLECTION,
                metadata={
                    "description": "Indian statutory ground truth and references",
                    "version": "1.0",
                    "embedding_model": "mistral-embed",
                    "embedding_dimension": 1536
                }
            )
            
            logger.info("Initialized ChromaDB collections successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collections: {str(e)}")
            raise
    
    def add_clause(
        self,
        clause_id: UUID,
        clause_text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Add extracted clause to ChromaDB with embedding and metadata
        
        Args:
            clause_id: UUID of the clause from PostgreSQL
            clause_text: Raw clause text
            embedding: 1536-dimensional Mistral embedding
            metadata: Dict containing:
                - contract_id: UUID of parent contract
                - tenant_id: UUID of tenant
                - clause_type: Type of clause
                - severity: Risk severity level
                - clause_number: Sequential position
                - confidence_score: AI confidence score
                - and any other enriched metadata
        
        Returns:
            str: Chroma document ID (same as clause_id)
        """
        try:
            doc_id = str(clause_id)
            
            self.clauses_collection.add(
                ids=[doc_id],
                documents=[clause_text],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            logger.info(f"Added clause {clause_id} to ChromaDB")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add clause to ChromaDB: {str(e)}")
            raise
    
    def add_clauses_batch(
        self,
        clauses: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Batch add multiple clauses for better performance
        
        Args:
            clauses: List of dicts with keys:
                - clause_id (UUID)
                - clause_text (str)
                - embedding (List[float])
                - metadata (Dict)
        
        Returns:
            List[str]: List of added document IDs
        """
        try:
            ids = [str(c["clause_id"]) for c in clauses]
            documents = [c["clause_text"] for c in clauses]
            embeddings = [c["embedding"] for c in clauses]
            metadatas = [c["metadata"] for c in clauses]
            
            self.clauses_collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(clauses)} clauses to ChromaDB in batch")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to batch add clauses to ChromaDB: {str(e)}")
            raise
    
    def search_similar_clauses(
        self,
        query_embedding: List[float],
        contract_id: Optional[UUID] = None,
        severity_filter: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar clauses using vector similarity
        
        Args:
            query_embedding: Query embedding vector
            contract_id: Optional filter for clauses from the same contract
            severity_filter: Optional filter by severity (critical, high, medium, low, info)
            n_results: Number of results to return
        
        Returns:
            List[Dict]: Ranked similar clauses with metadata
        """
        try:
            where_filter = None
            if contract_id:
                where_filter = {"contract_id": str(contract_id)}
            elif severity_filter:
                where_filter = {"severity": severity_filter}
            
            results = self.clauses_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Transform results to readable format
            similar_clauses = []
            if results and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    similar_clauses.append({
                        "clause_id": doc_id,
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    })
            
            return similar_clauses
            
        except Exception as e:
            logger.error(f"Failed to search similar clauses: {str(e)}")
            raise
    
    def get_clauses_by_contract(self, contract_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieve all clauses for a specific contract
        
        Args:
            contract_id: UUID of the contract
        
        Returns:
            List[Dict]: All clauses with metadata
        """
        try:
            results = self.clauses_collection.get(
                where={"contract_id": str(contract_id)},
                include=["documents", "metadatas"]
            )
            
            clauses = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    clauses.append({
                        "clause_id": doc_id,
                        "text": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    })
            
            return clauses
            
        except Exception as e:
            logger.error(f"Failed to get clauses for contract: {str(e)}")
            raise
    
    def update_clause_metadata(
        self,
        clause_id: UUID,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update metadata for an existing clause (e.g., after human review)
        
        Args:
            clause_id: UUID of the clause
            metadata: Updated metadata dict
        """
        try:
            self.clauses_collection.update(
                ids=[str(clause_id)],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated metadata for clause {clause_id}")
            
        except Exception as e:
            logger.error(f"Failed to update clause metadata: {str(e)}")
            raise
    
    def delete_clauses_for_contract(self, contract_id: UUID) -> None:
        """
        Delete all clauses for a contract (when contract is deleted/archived)
        
        Args:
            contract_id: UUID of the contract
        """
        try:
            # First get all clause IDs for the contract
            results = self.clauses_collection.get(
                where={"contract_id": str(contract_id)},
                include=[]
            )
            
            if results and results["ids"]:
                self.clauses_collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} clauses for contract {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete clauses for contract: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about ChromaDB collections
        
        Returns:
            Dict with collection names and document counts
        """
        try:
            stats = {
                "clauses": self.clauses_collection.count(),
                "playbook": self.playbook_collection.count(),
                "statutes": self.statute_collection.count(),
            }
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise


def get_chromadb_manager(db_path: str = None) -> ChromaDBManager:
    """
    Get or create ChromaDB manager instance (lazy singleton)
    
    Args:
        db_path: Optional path to ChromaDB storage
    
    Returns:
        ChromaDBManager: Initialized manager
    """
    if not hasattr(get_chromadb_manager, "_instance"):
        get_chromadb_manager._instance = ChromaDBManager(db_path)
    
    return get_chromadb_manager._instance
