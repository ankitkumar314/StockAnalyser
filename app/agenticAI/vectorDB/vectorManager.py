# utils/vector_store_manager.py

import shutil
import uuid
from langchain_community.vectorstores import FAISS


class VectorStoreManager:

    def __init__(self, embeddings, base_path="vectorstores"):
        self.embeddings = embeddings
        self.base_path = base_path

    def _get_path(self, doc_id):
        return f"{self.base_path}/{doc_id}"

    def create_store(self, chunks):
        doc_id = str(uuid.uuid4())

        vectordb = FAISS.from_documents(chunks, self.embeddings)
        path = self._get_path(doc_id)

        vectordb.save_local(path)

        return doc_id, vectordb

    def load_store(self, doc_id):
        path = self._get_path(doc_id)
        return FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)

    def delete_store(self, doc_id):
        path = self._get_path(doc_id)
        shutil.rmtree(path, ignore_errors=True)