import os
import shutil
import logging
from core.vector_store_manager import VectorStoreManager
from core.vector_store.base import VectorStoreBackend

# Configure logging
logging.basicConfig(level=logging.INFO)

# Mock Embedding Adapter
class MockEmbeddingAdapter:
    def embed_documents(self, texts):
        # Return fake embeddings of dimension 4
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]
        
    def embed_query(self, text):
        return [0.1, 0.2, 0.3, 0.4]

def test_vector_store():
    print("--- Starting Vector Store Demo ---")
    
    # Clean up previous test runs
    if os.path.exists("./vectorstore_test"):
        shutil.rmtree("./vectorstore_test")
    if os.path.exists("./snapshots"):
        shutil.rmtree("./snapshots")
        
    config = {
        "vector_store": {
            "backend": "chroma",
            "config": {
                "persist_directory": "./vectorstore_test",
                "collection_name": "test_collection"
            }
        }
    }
    
    adapter = MockEmbeddingAdapter()
    manager = VectorStoreManager(config, embedding_adapter=adapter)
    
    # 1. Add Documents
    print("\n1. Adding documents...")
    docs = ["Hello world", "Vector store is cool", "Python is great"]
    metadatas = [{"source": "a"}, {"source": "b"}, {"source": "c"}]
    ids = ["1", "2", "3"]
    
    manager.add_documents(docs, metadatas, ids)
    print("Documents added.")
    
    # 2. Get Stats
    stats = manager.get_stats()
    print(f"Stats: {stats}")
    assert stats["count"] == 3
    
    # 3. Search
    print("\n2. Searching...")
    results = manager.search("Hello")
    print(f"Search results: {results}")
    assert len(results) > 0
    
    # 4. Snapshot
    print("\n3. Creating snapshot 'v1'...")
    manager.create_snapshot("v1")
    
    # 5. Delete a document
    print("\n4. Deleting document 1...")
    manager.delete_document("1")
    stats = manager.get_stats()
    print(f"Stats after delete: {stats}")
    assert stats["count"] == 2
    
    # 6. Restore Snapshot
    print("\n5. Restoring snapshot 'v1'...")
    manager.restore_snapshot("v1")
    stats = manager.get_stats()
    print(f"Stats after restore: {stats}")
    
    if stats["count"] == 3:
        print("Restore successful: Count is 3")
    else:
        print(f"Restore failed or lag? Count is {stats['count']}")

    print("\n--- Demo Finished ---")

if __name__ == "__main__":
    test_vector_store()
