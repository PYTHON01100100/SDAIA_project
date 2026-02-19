import fitz  # PyMuPDF

from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime, timezone
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import os
import faiss
import numpy as np

# ------extract_and_clean---------
pdf_path="/Users/hadeel/SDAIA-Building-Gen-AI-Apps/project_starter/src/gov.pdf"
def extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages_text = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages_text.append(f"[page {page_num}]\n{text.strip()}")
    doc.close()
    full_text = "\n\n".join(pages_text)
    return full_text

def clean_text(text: str) -> str:
    """Master cleaning function for extracted text."""
    if not text:
        return ""
    
    # 1. Fix common encoding artifacts
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = unicodedata.normalize("NFC", text)
    
    # 2. Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"[ \t]+", " ", text)      # Collapse spaces/tabs
    
    # 3. Remove common PDF artifacts
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"-\n(\w)", r"\1", text)  # Fix hyphenated line breaks
    
    return text.strip()

def clean_text_extended(text: str) -> str:
    """Extended cleaning with additional rules."""
    text = clean_text(text)
    
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    
    text = re.sub(r'https?://\S+', '', text)
    
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

# ------Documention---------
@dataclass
class Document:
    """Standardized representation of an ingested document."""
    content: str
    source: str
    title: Optional[str] = None
    doc_type: str = "unknown"
    author: Optional[str] = None
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    word_count: int = 0
    extra_metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.content and self.word_count == 0:
            self.word_count = len(self.content.split())

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source": self.source,
            "metadata": {
                "title": self.title,
                "type": self.doc_type,
                "author": self.author,
                "word_count": self.word_count,
            }
        }
# ------Agents_Results---------
@dataclass
class ResearchResult:
    key_topics: str
    main_entities: str
    document_type: str
    language_quality: str

@dataclass
class AnalysisResult:
    strengths: str
    weaknesses: str
    clarity_score: int
    completeness_score: int
    structure_score: int

@dataclass
class FinalRating:
    summary: str
    numerical_score: float
    detailed_report: str
    recommendations: str



# ------Chunke---------
class BaseChunker(ABC):
    """Abstract base class for all chunking strategies."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def chunk_document(self, text: str, metadata: dict = None) -> List[Dict[str, Any]]:
        pass
    
    def _create_chunk_dict(self, text: str, metadata: dict, chunk_id: int) -> dict:
        chunk_meta = metadata.copy() if metadata else {}
        chunk_meta.update({
            'chunk_id': chunk_id,
            'char_length': len(text),
            'chunker': self.__class__.__name__
        })
        return {'text': text.strip(), 'metadata': chunk_meta}


class RecursiveChunker(BaseChunker):
    """Chunks respecting paragraph and sentence boundaries."""
    
    def __init__(self, chunk_size=500, chunk_overlap=50, separators=None):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
    
    def chunk_document(self, text, metadata=None):
        text_chunks = self._splitter.split_text(text)
        return [self._create_chunk_dict(t, metadata, i) for i, t in enumerate(text_chunks)]


client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def generate_embedding(text: str):
    response = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# ------search_document---------

def search_document(query, k=3):
    global index, stored_chunks
    import numpy as np

    query_vector = generate_embedding(query)
    query_vector = np.array([query_vector]).astype("float32")

    distances, indices = index.search(query_vector, k)

    results = []
    for i in indices[0]:
        results.append(stored_chunks[i]["text"])

    return "\n\n".join(results)

#----call the functions------
raw_text = extract_pdf_text(pdf_path)
cleaned_text = clean_text_extended(raw_text)

doc = Document(
    content=cleaned_text,
    source="gov.pdf",
    title="Government PDF",
    doc_type="pdf"
)
recursive = RecursiveChunker(chunk_size=300, chunk_overlap=50)
text = doc.content
metadata = doc.to_dict()["metadata"]
chunks = recursive.chunk_document(text, metadata)

print(f"Total chunks created: {len(chunks)}")
print("Example chunk:", chunks[0])

embedded_chunks = []

for chunk in chunks:
    vector = generate_embedding(chunk["text"])
    
    embedded_chunks.append({
        "embedding": vector,
        "metadata": chunk["metadata"],
        "text": chunk["text"]
    })

print("Vector size:", len(embedded_chunks[0]["embedding"]))

embeddings = []
texts = []

for chunk in chunks:
    vector = generate_embedding(chunk["text"])
    embeddings.append(vector)
    texts.append(chunk)

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]  # 1536
index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

print("Total vectors in FAISS:", index.ntotal) #102


