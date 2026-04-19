from typing import Optional, List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.agenticAI.vectorDB.documentIngestor import DocumentIngestor
from app.agenticAI.vectorDB.vectorManager import VectorStoreManager


class VectorDBManager:
    def __init__(self, embedding_model: str = "BAAI/bge-large-en", base_path: str = "vectorstores"):
        try:
            if embedding_model is None or embedding_model.strip() == "":
                raise ValueError("Embedding model cannot be None or empty")
            
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
            self.ingestor = DocumentIngestor(self.embeddings)
            self.vs_manager = VectorStoreManager(self.embeddings, base_path)
            
        except Exception as e:
            raise Exception(f"Error initializing VectorDBManager: {str(e)}")
    
    def create_vector_store(self, chunks: List) -> tuple:
        try:
            if chunks is None or len(chunks) == 0:
                raise ValueError("Chunks cannot be None or empty")
            
            doc_id, vectorstore = self.vs_manager.create_store(chunks)
            
            if doc_id is None:
                raise Exception("Failed to create vector store")
            
            return doc_id, vectorstore
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error creating vector store: {str(e)}")
    
    def load_vector_store(self, doc_id: str) -> FAISS:
        try:
            if doc_id is None or doc_id.strip() == "":
                raise ValueError("Document ID cannot be None or empty")
            
            vectorstore = self.vs_manager.load_store(doc_id)
            
            if vectorstore is None:
                raise Exception(f"Vector store not found for doc_id: {doc_id}")
            
            return vectorstore
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error loading vector store: {str(e)}")
    
    def delete_vector_store(self, doc_id: str) -> bool:
        try:
            if doc_id is None or doc_id.strip() == "":
                raise ValueError("Document ID cannot be None or empty")
            
            self.vs_manager.delete_store(doc_id)
            return True
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error deleting vector store: {str(e)}")
    
    def ingest_and_store(self, pdf_url: str) -> tuple:
        try:
            if pdf_url is None or pdf_url.strip() == "":
                raise ValueError("PDF URL cannot be None or empty")
            
            chunks = self.ingestor.ingest(pdf_url)
            doc_id, vectorstore = self.create_vector_store(chunks)
            
            return doc_id, vectorstore, chunks
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error in ingest and store: {str(e)}")


if __name__ == "__main__":
    try:
        db_manager = VectorDBManager()
        
        doc_id, vectorstore = db_manager.ingest_and_store("https://example.com/sample.pdf")
        
        print(f"Successfully created vector store with doc_id: {doc_id}")
        
        loaded_store = db_manager.load_vector_store(doc_id)
        print(f"Successfully loaded vector store for doc_id: {doc_id}")
        
    except Exception as e:
        print(f"Error: {str(e)}")