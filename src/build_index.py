import os
import shutil
import yaml
import logging
from typing import List

try:
    import lancedb
    from llama_index.core import Document, VectorStoreIndex, Settings, StorageContext
    from llama_index.vector_stores.lancedb import LanceDBVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core.node_parser import SentenceSplitter
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logging.error("Missing required dependencies (lancedb, llama-index). Please verify requirements.")

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def wipe_database(db_dir: str):
    """Perform a clean wipe of the vector database directory."""
    if os.path.exists(db_dir):
        logging.info(f"Wiping existing LanceDB directory: {db_dir}")
        shutil.rmtree(db_dir)

def parse_markdown_with_frontmatter(file_path: str) -> Document:
    """Parses a single Markdown file, extracting the YAML frontmatter into metadata."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by '---'
    parts = content.split("---", 2)
    metadata = {}
    text_body = content
    
    if len(parts) >= 3 and parts[0].strip() == "":
        try:
            yaml_front = parts[1]
            text_body = parts[2].strip()
            metadata = yaml.safe_load(yaml_front) or {}
            if not isinstance(metadata, dict):
                metadata = {}
            # LanceDB/LlamaIndex requires primitive metadata types
            for k, v in metadata.items():
                if isinstance(v, list):
                    metadata[k] = v[0] if len(v) == 1 else ", ".join(v)
        except Exception as e:
            logging.warning(f"Failed to parse YAML in {file_path}: {e}")
            text_body = content # Fallback to full content on failure

    # We enforce is_dummy: False because these are real generated docs via script
    metadata["is_dummy"] = False
    
    return Document(text=text_body, metadata=metadata)

def load_documents(guidelines_dir: str) -> List[Document]:
    """Iterates recursively through the guidelines directory."""
    docs = []
    if not os.path.exists(guidelines_dir):
        logging.warning(f"Guidelines directory {guidelines_dir} not found.")
        return docs

    for root, _, files in os.walk(guidelines_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                logging.info(f"Parsing: {file_path}")
                docs.append(parse_markdown_with_frontmatter(file_path))
    
    return docs

def build_index():
    if not LANCEDB_AVAILABLE:
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_dir = os.path.join(base_dir, "data", ".lancedb")
    guidelines_dir = os.path.join(base_dir, "data", "guidelines")
    table_name = "guidelines"

    # Step 1: Wipe existing db
    wipe_database(db_dir)

    # Step 2: Ensure destination directory layout
    os.makedirs(os.path.dirname(db_dir), exist_ok=True)

    # Step 3: Load Markdown
    documents = load_documents(guidelines_dir)
    if not documents:
        logging.warning("No documents found to index.")
        return

    logging.info(f"Loaded {len(documents)} documents. Initializing BAAI/bge-small-en-v1.5 embeddings...")
    
    # Step 4: Configure Embedder & Chunker
    try:
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.embed_model = embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    except Exception as e:
        logging.error(f"Failed to initialize embedding model: {e}")
        return

    # Step 5: Upsert to LanceDB
    try:
        logging.info(f"Connecting to LanceDB at {db_dir} and writing to table '{table_name}'...")
        vector_store = LanceDBVectorStore(uri=db_dir, table_name=table_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
        logging.info("✅ Build Complete! Data pipeline successfully ingested Markdown into LanceDB.")
    except Exception as e:
        logging.error(f"Failed to upsert vectors into LanceDB: {e}")

if __name__ == "__main__":
    build_index()
