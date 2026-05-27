import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def index_codebase(target_dir: str = "./src", persist_dir: str = "./agent_memory") -> None:
    """
    Crawls the target directory for Python files and indexes them into ChromaDB
    to provide the agent with local code context.
    """
    print("[Memory] Crawling local repository for Python files...")
    code_documents = []
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"[Memory] Created empty '{target_dir}' directory. Place your codebase files inside it.")
        return

    # 1. Read all Python files in the target directory
    ignored_dirs = {".git", "venv", ".venv", "env", ".env", "node_modules", "__pycache__"}
    
    for root, dirs, files in os.walk(target_dir):
        # Prevent os.walk from traversing into ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                # Wrap file contents in a Document with metadata
                doc = Document(
                    page_content=content, 
                    metadata={"source_file_path": os.path.abspath(file_path)}
                )
                code_documents.append(doc)
            except Exception as e:
                print(f"[Memory] Failed to read {file_path}. Error: {e}")

    if not code_documents:
        print("[Memory] No code files found to index yet.")
        return

    # 2. Split documents into chunks for more accurate vector retrieval
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(code_documents)

    # 3. Initialize Ollama embeddings and populate the Chroma vector database
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=persist_dir
    )
    
    print(f"[Memory] Success! Structured {len(code_documents)} files into vector storage.")

if __name__ == "__main__":
    index_codebase()
