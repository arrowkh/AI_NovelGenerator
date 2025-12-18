import logging
import os
import shutil
import time
from typing import List, Dict, Any, Optional
import chromadb
from core.vector_store.base import VectorStoreBackend

logger = logging.getLogger(__name__)

class ChromaBackend(VectorStoreBackend):
    def __init__(self):
        self.client = None
        self.collection = None
        self.persist_directory = None
        self.collection_name = None

    def initialize(self, config: Dict[str, Any]):
        self.persist_directory = config.get("persist_directory", "./vectorstore")
        self.collection_name = config.get("collection_name", "novel_embeddings")
        
        # Ensure directory exists
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
            
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"ChromaDB initialized at {self.persist_directory}, collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise e

    def add_embeddings(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Chroma add_embeddings error: {e}")
            return False

    def search(self, query_embedding: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter
            )
            
            formatted_results = []
            if results['ids']:
                ids = results['ids'][0]
                documents = results['documents'][0] if results['documents'] else [""] * len(ids)
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(ids)
                distances = results['distances'][0] if results['distances'] else [0.0] * len(ids)
                
                for i in range(len(ids)):
                    formatted_results.append({
                        "id": ids[i],
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "score": 1.0 - distances[i] if distances else 0.0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Chroma search error: {e}")
            return []

    def get_documents(self, ids: List[str]) -> List[Dict[str, Any]]:
        try:
            results = self.collection.get(ids=ids)
            formatted_results = []
            
            r_ids = results.get('ids', [])
            r_docs = results.get('documents', [])
            r_metas = results.get('metadatas', [])
            
            if r_ids:
                for i in range(len(r_ids)):
                    formatted_results.append({
                        "id": r_ids[i],
                        "text": r_docs[i],
                        "metadata": r_metas[i]
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Chroma get_documents error: {e}")
            return []

    def delete_embeddings(self, ids: List[str]) -> bool:
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Chroma delete_embeddings error: {e}")
            return False

    def update_embeddings(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> bool:
        try:
            self.collection.update(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            logger.error(f"Chroma update_embeddings error: {e}")
            return False

    def create_snapshot(self, snapshot_name: str) -> bool:
        """
        Create a file-system backup of the persist directory.
        """
        snapshot_dir = os.path.join(os.path.dirname(self.persist_directory), "snapshots", snapshot_name)
        try:
            if os.path.exists(snapshot_dir):
                shutil.rmtree(snapshot_dir)
            shutil.copytree(self.persist_directory, snapshot_dir)
            logger.info(f"Snapshot created at {snapshot_dir}")
            return True
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return False

    def restore_snapshot(self, snapshot_name: str) -> bool:
        """
        Restore from a snapshot. WARNING: This overwrites current data.
        """
        snapshot_dir = os.path.join(os.path.dirname(self.persist_directory), "snapshots", snapshot_name)
        if not os.path.exists(snapshot_dir):
            logger.error(f"Snapshot {snapshot_name} not found")
            return False
            
        try:
            # Re-initializing client might be needed or handled by manager/lock
            # Since we are using FileLock in Manager, we are safe from other processes.
            # But we need to make sure this process doesn't hold file handles that prevent deletion.
            
            # Chroma PersistentClient might keep files open.
            # We can try to rely on OS or maybe force garbage collection.
            # In a long running app, this might be tricky.
            # For now, let's assume we can overwrite if we are careful.
            
            # If we are on Linux/Unix, unlink works even if open.
            
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
            
            shutil.copytree(snapshot_dir, self.persist_directory)
            
            # Re-initialize to ensure client sees new data
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            
            logger.info(f"Restored snapshot {snapshot_name}")
            return True
        except Exception as e:
            logger.error(f"Restore snapshot failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.persist_directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            return {
                "count": count,
                "size_bytes": total_size,
                "backend": "chroma",
                "collection": self.collection_name
            }
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {}
