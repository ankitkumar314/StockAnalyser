import os
import requests
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import re


class DocumentIngestor:

    def __init__(self, embeddings, download_dir: str = "downloads"):
        try:
            if embeddings is None:
                raise ValueError("Embeddings cannot be None")
            
            self.embeddings = embeddings
            self.download_dir = download_dir
            
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)
                
        except Exception as e:
            raise Exception(f"Error initializing DocumentIngestor: {str(e)}")

    def download_pdf(self, pdf_url: str) -> str:
        try:
            if pdf_url is None or pdf_url.strip() == "":
                raise ValueError("PDF URL cannot be None or empty")
            
            filename = pdf_url.split("/")[-1]
            if not filename.endswith(".pdf"):
                filename = f"{filename}.pdf"
            
            file_path = os.path.join(self.download_dir, filename)
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.bseindia.com/",
                "Accept": "application/pdf"
            }
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            if not os.path.exists(file_path):
                raise Exception("Failed to save PDF file")
            
            return file_path
            
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout while downloading PDF from {pdf_url}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection error while downloading PDF from {pdf_url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {e.response.status_code} while downloading PDF")
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error downloading PDF: {str(e)}")

    def load_pdf(self, file_path: str) -> List[Document]:
        try:
            if file_path is None or file_path.strip() == "":
                raise ValueError("File path cannot be None or empty")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found at: {file_path}")
            
            if not file_path.endswith(".pdf"):
                raise ValueError("File must be a PDF")
            
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if documents is None or len(documents) == 0:
                raise Exception("No documents loaded from PDF")
            
            return documents
            
        except ValueError as e:
            raise e
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error loading PDF: {str(e)}")



    def split_into_conversations(self, documents: List[Document]):
            all_chunks = []

            for doc in documents:
                text = doc.page_content

                # Split when Moderator introduces a new question
                pattern = r"(Moderator:.*?)(?=Moderator:|\Z)"
                conversations = re.findall(pattern, text, re.DOTALL)

                for conv in conversations:
                    conv = conv.strip()

                    if len(conv) < 100:
                        continue
                    
                    all_chunks.append(
                        Document(
                            page_content=conv,
                            metadata={
                                "type": "conversation_block"
                            }
                        )
                    )

            return all_chunks

    def merge_qa_chunks(self, chunks):
         merged = []
         i = 0
        
         while i < len(chunks):
             current = chunks[i]
        
             if "Analyst" in current.metadata["speaker"] or "Ghosh" in current.metadata["speaker"]:
                 # merge with next CEO response
                 if i + 1 < len(chunks):
                     next_chunk = chunks[i + 1]
        
                     if "Ashish" in next_chunk.metadata["speaker"]:
                         combined_text = (
                             f"Question:\n{current.page_content}\n\n"
                             f"Answer:\n{next_chunk.page_content}"
                         )
        
                         merged.append(
                             Document(
                                 page_content=combined_text,
                                 metadata={
                                     "type": "qa_pair"
                                 }
                             )
                         )
                         i += 2
                         continue
                     
             merged.append(current)
             i += 1
        
         return merged

    def split_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        try:
            if documents is None or len(documents) == 0:
                raise ValueError("Documents cannot be None or empty")
            
            if chunk_size <= 0:
                raise ValueError("Chunk size must be greater than 0")
            
            if chunk_overlap < 0:
                raise ValueError("Chunk overlap cannot be negative")

            pattern = r"(?:\n|^)([A-Za-z\s\.]+?):"

            # text_splitter = RecursiveCharacterTextSplitter(
            #     chunk_size=chunk_size,
            #     chunk_overlap=chunk_overlap,
            #     length_function=len,
            #     separators=["\n\n", "\n", " ", ""]
            # )
            
            chunks = text_splitter.split_documents(documents)
            
            if chunks is None or len(chunks) == 0:
                raise Exception("No chunks generated from documents")
            
            return chunks
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error splitting documents: {str(e)}")

    def ingest(self, pdf_url: str) -> List[Document]:
        try:
            if pdf_url is None or pdf_url.strip() == "":
                raise ValueError("PDF URL cannot be None or empty")
            
            file_path = self.download_pdf(pdf_url)
            docs = self.load_pdf(file_path)
            chunks = self.split_into_conversations(docs)
            
            return chunks
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error ingesting document: {str(e)}")