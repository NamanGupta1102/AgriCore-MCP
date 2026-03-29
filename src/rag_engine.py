import os
import logging
from typing import Dict, Any, List, Optional
try:
    import lancedb
    from llama_index.core import VectorStoreIndex, Document, Settings
    from llama_index.vector_stores.lancedb import LanceDBVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logging.warning("LlamaIndex or LanceDB not available. RagEngine will run in stub mode.")

class RagEngine:
    """
    Engine Beta (Semantic RAG)
    Handles localized knowledge retrieval with metadata filtering.
    """
    def __init__(self, db_dir: str = "data/.lancedb", table_name: str = "guidelines"):
        self.db_dir = db_dir
        self.table_name = table_name
        self.index = None
        
        if LANCEDB_AVAILABLE:
            self._init_embedding_model()
            self._init_db()

    def _init_embedding_model(self):
        logging.info("Initializing HuggingFace embedding model: BAAI/bge-small-en-v1.5")
        try:
            # We use an accurate, local model suitable for retrieval tasks
            embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
            Settings.embed_model = embed_model
        except Exception as e:
            logging.error(f"Failed to load embedding model: {e}")

    def _init_db(self):
        """Connects to LanceDB or creates a mock table if none exists for testing."""
        if not os.path.exists(os.path.dirname(self.db_dir)):
            os.makedirs(os.path.dirname(self.db_dir), exist_ok=True)
            
        try:
            self.db = lancedb.connect(self.db_dir)
            if self.table_name not in self.db.table_names():
                logging.info(f"Table '{self.table_name}' not found. Initializing dummy data for testing.")
                self._create_dummy_data()
            
            # Setup vector store connection
            self.vector_store = LanceDBVectorStore(uri=self.db_dir, table_name=self.table_name)
            self.index = VectorStoreIndex.from_vector_store(self.vector_store)
            logging.info("Engine Beta (Semantic RAG) initialized successfully.")
        except Exception as e:
            logging.error(f"Could not connect to LanceDB at {self.db_dir}. Error: {e}")
            self.index = None

    def _create_dummy_data(self):
        """Builds an initial dummy dataset since the ingestions scripts run in Phase 4."""
        docs = [
            Document(
                text="Early blight (Alternaria solani) thrives in high humidity. Use copper fungicides every 7 days when humidity exceeds 80%. Ensure good airflow and remove lower leaves.",
                metadata={"id": "guide_tomato_blight_ne_01", "crop_tags": "tomato", "hardiness_zones": "6b", "category": "disease_management", "is_dummy": True}
            ),
            Document(
                text="Companion planting: Plant basil near tomatoes to deter hornworms and whiteflies. This improves organic pest management and can subtly improve tomato flavor.",
                metadata={"id": "guide_companion_planting_01", "crop_tags": "tomato", "hardiness_zones": "all", "category": "companion_planting", "is_dummy": True}
            ),
            Document(
                text="Corn requires rich soil with high nitrogen. Test soil prior to planting to ensure pH is between 5.8 and 7.0 for optimal germination and health.",
                metadata={"id": "guide_corn_soil_ph", "crop_tags": "corn", "hardiness_zones": "5a", "category": "soil_health", "is_dummy": True}
            )
        ]
        from llama_index.core import StorageContext
        vector_store = LanceDBVectorStore(uri=self.db_dir, table_name=self.table_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        VectorStoreIndex.from_documents(docs, storage_context=storage_context)

    def search(self, query: str, metadata_filters: Optional[Dict[str, Any]] = None, top_k: int = 3) -> str:
        if not self.index or not LANCEDB_AVAILABLE:
            return "### 📖 AGRICORE MCP: COMMUNITY GUIDELINES\nNo community guidelines are currently indexed or LanceDB is unavailable."
            
        filters = []
        if metadata_filters:
            for key, value in metadata_filters.items():
                if isinstance(value, list) and value:
                    # simplistic list matching: match first item for dummy search
                    filters.append(ExactMatchFilter(key=key, value=value[0]))
                elif isinstance(value, str):
                    filters.append(ExactMatchFilter(key=key, value=value))
                    
        mq_filters = MetadataFilters(filters=filters) if filters else None
        
        try:
            retriever = self.index.as_retriever(similarity_top_k=top_k, filters=mq_filters)
            nodes = retriever.retrieve(query)
            
            if not nodes:
                return f"### 📖 AGRICORE MCP: COMMUNITY GUIDELINES\nNo relevant guidelines found for query: '{query}'."

            result_str = "### 📖 AGRICORE MCP: COMMUNITY GUIDELINES\n\n"
            
            if any(node.metadata.get("is_dummy", False) for node in nodes):
                result_str += "> [!WARNING]\n> ⚠️ UNVERIFIED DUMMY DATA FOR TESTING PURPOSES ONLY ⚠️\n\n"

            for i, node in enumerate(nodes):
                meta = node.metadata
                source_id = meta.get("id", "Unknown")
                zone = meta.get("hardiness_zones", "Unknown")
                text = node.get_content().strip()
                result_str += f"**Source {i+1} Retrieved:** (File: `{source_id}.md`) - Zone: `{zone}`\n> {text}\n\n"
                
            return result_str
        except Exception as e:
            logging.error(f"Semantic search failed: {e}")
            return f"### 📖 AGRICORE MCP: COMMUNITY GUIDELINES\nFailed to traverse the vector bank: {str(e)}"
