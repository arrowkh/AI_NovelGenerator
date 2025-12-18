import logging
import os
import time
import json
from typing import List, Dict, Any, Optional, Union
from threading import Lock
from filelock import FileLock

from core.vector_store.base import VectorStoreBackend

logger = logging.getLogger(__name__)

SUPPORTED_BACKENDS = {
    "chroma": {
        "local": True,
        "cloud": False,
        "open_source": True,
        "recommended_for": "本地开发和小规模项目",
        "module": "core.vector_store.chroma_backend",
        "class": "ChromaBackend"
    },
    "weaviate": {
        "local": True,
        "cloud": True,
        "open_source": True,
        "recommended_for": "生产环境和大规模项目",
    },
    "milvus": {
        "local": True,
        "cloud": False,
        "open_source": True,
        "recommended_for": "高性能需求",
    },
    "qdrant": {
        "local": True,
        "cloud": True,
        "open_source": True,
        "recommended_for": "平衡性能和易用性",
    },
    "pinecone": {
        "local": False,
        "cloud": True,
        "open_source": False,
        "recommended_for": "云端完全托管",
    }
}

class VectorStoreManager:
    """
    Unified manager for vector store operations.
    Handles backend selection, consistency (locking), and embedding generation.
    """

    def __init__(self, config: Dict[str, Any], embedding_adapter=None):
        self.config = config
        self.embedding_adapter = embedding_adapter
        self.backend_name = config.get("vector_store", {}).get("backend", "chroma")
        self.backend_config = config.get("vector_store", {}).get("config", {})
        self.auto_switch = config.get("vector_store", {}).get("auto_switch", True)
        
        self.backend: Optional[VectorStoreBackend] = None
        self.lock_path = os.path.join(os.getcwd(), "vector_store.lock")
        self.file_lock = FileLock(self.lock_path)
        self.memory_lock = Lock()
        
        self._initialize_backend()

    def _initialize_backend(self):
        """
        Initialize the selected backend.
        """
        logger.info(f"Initializing Vector Store Backend: {self.backend_name}")
        
        if self.backend_name not in SUPPORTED_BACKENDS:
            logger.warning(f"Backend {self.backend_name} not supported or configured. Falling back to Chroma.")
            self.backend_name = "chroma"

        try:
            # Dynamic import
            if self.backend_name == "chroma":
                from core.vector_store.chroma_backend import ChromaBackend
                self.backend = ChromaBackend()
            else:
                 # TODO: Implement other backends
                 logger.error(f"Backend implementation for {self.backend_name} not found.")
                 if self.auto_switch and self.backend_name != "chroma":
                     logger.info("Auto-switching to Chroma...")
                     self.backend_name = "chroma"
                     from core.vector_store.chroma_backend import ChromaBackend
                     self.backend = ChromaBackend()
                 else:
                     raise NotImplementedError(f"Backend {self.backend_name} is not implemented yet.")
            
            self.backend.initialize(self.backend_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize backend {self.backend_name}: {e}")
            if self.auto_switch and self.backend_name != "chroma":
                logger.info("Attempting to fallback to Chroma...")
                try:
                    self.backend_name = "chroma"
                    from core.vector_store.chroma_backend import ChromaBackend
                    self.backend = ChromaBackend()
                    self.backend.initialize(self.backend_config)
                except Exception as ex:
                    logger.critical(f"Fallback to Chroma failed: {ex}")
                    raise ex
            else:
                raise e

    def _get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        if not self.embedding_adapter:
            raise ValueError("No embedding adapter provided to VectorStoreManager.")
        
        if isinstance(texts, str):
            texts = [texts]
            
        return self.embedding_adapter.embed_documents(texts)

    def add_document(self, text: str, metadata: Dict[str, Any], doc_id: Optional[str] = None) -> bool:
        """
        Add a single document.
        """
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())
            
        return self.add_documents([text], [metadata], [doc_id])

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        """
        Add multiple documents with thread and process safety.
        """
        if not texts:
            return True
            
        embeddings = self._get_embeddings(texts)
        
        # Use a transaction/lock mechanism
        with self.memory_lock:
            with self.file_lock:
                try:
                    return self.backend.add_embeddings(texts, embeddings, metadatas, ids)
                except Exception as e:
                    logger.error(f"Error adding documents: {e}")
                    return False

    def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        """
        if not self.embedding_adapter:
             raise ValueError("No embedding adapter provided.")
             
        query_embedding = self.embedding_adapter.embed_query(query)
        
        try:
            return self.backend.search(query_embedding, top_k, filter)
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
            
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        results = self.get_documents([doc_id])
        return results[0] if results else None
        
    def get_documents(self, ids: List[str]) -> List[Dict[str, Any]]:
         try:
            return self.backend.get_documents(ids)
         except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        return self.delete_documents([doc_id])

    def delete_documents(self, ids: List[str]) -> bool:
        with self.memory_lock:
            with self.file_lock:
                try:
                    return self.backend.delete_embeddings(ids)
                except Exception as e:
                    logger.error(f"Error deleting documents: {e}")
                    return False

    def update_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a document. If metadata is None, keeps old metadata.
        """
        if metadata is None:
             # Fetch existing metadata
             existing = self.get_document(doc_id)
             if existing:
                 metadata = existing.get("metadata", {})
             else:
                 metadata = {}

        return self.update_documents([doc_id], [text], [metadata])

    def update_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]) -> bool:
        embeddings = self._get_embeddings(texts)
        
        with self.memory_lock:
            with self.file_lock:
                try:
                    return self.backend.update_embeddings(ids, texts, embeddings, metadatas)
                except Exception as e:
                    logger.error(f"Error updating documents: {e}")
                    return False

    def create_snapshot(self, snapshot_name: str) -> bool:
        with self.memory_lock:
            with self.file_lock:
                return self.backend.create_snapshot(snapshot_name)

    def restore_snapshot(self, snapshot_name: str) -> bool:
        with self.memory_lock:
            with self.file_lock:
                return self.backend.restore_snapshot(snapshot_name)

    def get_stats(self) -> Dict[str, Any]:
        return self.backend.get_stats()
