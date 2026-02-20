# src/tools/vector_store.py
from typing import List, Dict
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer

class TechVectorStore:
    """
    Vector store مخصص للتكنولوجيا
    - يخزن مستندات
    - يمكن البحث عن أفضل النتائج بناءً على التشابه
    """
    def __init__(self, store_file="tech_vectors.pkl", embedding_model="all-MiniLM-L6-v2"):
        self.store_file = store_file
        self.embedding_model = SentenceTransformer(embedding_model)
        self.docs: List[str] = []
        self.embeddings = None
        self.index = None
        self.load_store()

    def load_store(self):
        if os.path.exists(self.store_file):
            with open(self.store_file, "rb") as f:
                data = pickle.load(f)
                self.docs = data["docs"]
                self.embeddings = data["embeddings"]
                dim = self.embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.index.add(self.embeddings)
        else:
            self.embeddings = None
            self.index = None

    def save_store(self):
        with open(self.store_file, "wb") as f:
            pickle.dump({"docs": self.docs, "embeddings": self.embeddings}, f)

    def add_documents(self, documents: List[str]):
        new_embeddings = self.embedding_model.encode(documents)
        if self.embeddings is None:
            self.embeddings = new_embeddings
            dim = new_embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        self.index.add(new_embeddings)
        self.docs.extend(documents)
        self.save_store()

    def query(self, query: str, top_k=5) -> List[Dict]:
        if self.index is None or len(self.docs) == 0:
            return []
        query_emb = self.embedding_model.encode([query])
        D, I = self.index.search(query_emb, top_k)
        results = [{"doc": self.docs[i], "score": float(D[0][idx])} for idx, i in enumerate(I[0])]
        return results

# Singleton instance
tech_vector_store = TechVectorStore()
