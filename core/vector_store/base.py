from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStoreBackend(ABC):
    """
    Abstract base class for vector store backends.
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """
        Initialize the backend with configuration.
        """
        pass

    @abstractmethod
    def add_embeddings(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        """
        Add embeddings to the vector store.
        """
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        Returns a list of results, each containing 'id', 'text', 'metadata', 'score'.
        """
        pass

    @abstractmethod
    def get_documents(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get documents by ID.
        Returns a list of dicts with 'id', 'text', 'metadata'.
        """
        pass

    @abstractmethod
    def delete_embeddings(self, ids: List[str]) -> bool:
        """
        Delete embeddings by ID.
        """
        pass

    @abstractmethod
    def update_embeddings(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> bool:
        """
        Update existing embeddings.
        """
        pass

    @abstractmethod
    def create_snapshot(self, snapshot_name: str) -> bool:
        """
        Create a snapshot of the current state.
        """
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_name: str) -> bool:
        """
        Restore from a snapshot.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store (size, count, etc.).
        """
        pass
