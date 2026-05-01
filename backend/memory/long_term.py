"""
memory/long_term.py - FAISS-based vector store for long-term memory.
Stored in OneDrive for persistence and cloud sync.
"""
import os
import json
import asyncio
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional

from config import settings
from llm.openai_client import get_client

class LongTermMemory:
    def __init__(self):
        self.onedrive_path = Path(settings.onedrive_path)
        self.index_path = self.onedrive_path / "memory_index.faiss"
        self.metadata_path = self.onedrive_path / "memory_metadata.json"
        
        self.dimension = 1024  # Default for nvidia/nv-embedqa-e5-v5
        self.index = None
        self.metadata = []  # List of strings corresponding to index IDs
        
        self._load_or_create()

    def _load_or_create(self):
        """Loads existing FAISS index and metadata or creates new ones."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self.dimension = self.index.d
            except Exception as e:
                print(f"[ERROR] Failed to load memory index: {e}")
                self._create_new()
        else:
            self._create_new()

    def _create_new(self):
        """Initializes a new FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self._save()

    def _save(self):
        """Saves index and metadata to OneDrive."""
        self.onedrive_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    async def _get_embedding(self, text: str, is_query: bool = True) -> List[float]:
        """Fetches embedding from NVIDIA/OpenAI API."""
        client = get_client()
        try:
            # NVIDIA asymmetric models (like e5-v5) require input_type
            extra_body = {"input_type": "query" if is_query else "passage"}
            response = await asyncio.wait_for(
                client.embeddings.create(
                    input=[text],
                    model=settings.embedding_model,
                    extra_body=extra_body
                ),
                timeout=10.0
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Embedding failed: {e}")
            return [0.0] * self.dimension

    async def add_memory(self, text: str):
        """Embeds and adds a new fact to long-term memory."""
        if not text.strip():
            return
            
        embedding = await self._get_embedding(text, is_query=False)
        vector = np.array([embedding]).astype('float32')
        
        self.index.add(vector)
        self.metadata.append(text)
        self._save()

    async def search(self, query: str, top_k: int = 3) -> List[str]:
        """Searches for relevant past memories."""
        if self.index.ntotal == 0:
            return []
            
        embedding = await self._get_embedding(query, is_query=True)
        vector = np.array([embedding]).astype('float32')
        
        distances, indices = self.index.search(vector, top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])
        
        return results

# Singleton instance
long_term_memory = LongTermMemory()
