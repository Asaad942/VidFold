import faiss
import numpy as np
from typing import List, Tuple, Dict, Any
from ..database import supabase

class VectorStore:
    def __init__(self):
        self.dimension = 384  # dimension of all-MiniLM-L6-v2 embeddings
        self.index = None
        self.id_map: Dict[int, str] = {}  # Maps FAISS index to video IDs
        
    async def initialize(self):
        """Initialize FAISS index with existing embeddings from database."""
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product index for cosine similarity
        
        # Get all embeddings from database
        try:
            result = supabase.table("video_analysis").select("video_id,embedding").execute()
            if not result.data:
                return
                
            # Build index
            embeddings = []
            self.id_map = {}
            
            for idx, record in enumerate(result.data):
                if not record.get('embedding'):
                    continue
                embedding = np.array(record['embedding'], dtype=np.float32)
                embeddings.append(embedding)
                self.id_map[idx] = str(record['video_id'])
                
            if embeddings:
                embeddings_array = np.vstack(embeddings)
                self.index.add(embeddings_array)
        except Exception as e:
            print(f"Error initializing vector store: {str(e)}")
            raise
        
    async def search(
        self,
        query_embedding: np.ndarray,
        k: int = 50
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors in the index.
        
        Args:
            query_embedding: Query vector to search for
            k: Number of results to return
            
        Returns:
            List of (video_id, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # Reshape query embedding for FAISS
        query_vector = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Search index
        distances, indices = self.index.search(query_vector, k)
        
        # Convert results to list of (id, score) tuples
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            video_id = self.id_map[idx]
            similarity = float(distance)  # Convert from numpy float to Python float
            results.append((video_id, similarity))
            
        return results
        
    async def add_embedding(
        self,
        video_id: str,
        embedding: np.ndarray
    ):
        """
        Add a new embedding to the index.
        
        Args:
            video_id: ID of the video
            embedding: Embedding vector to add
        """
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
            
        # Add to FAISS index
        vector = embedding.reshape(1, -1).astype(np.float32)
        self.index.add(vector)
        
        # Update ID mapping
        self.id_map[self.index.ntotal - 1] = video_id
        
    async def remove_embedding(self, video_id: str):
        """
        Remove an embedding from the index.
        
        Args:
            video_id: ID of the video to remove
        """
        # FAISS doesn't support direct removal, so we need to rebuild the index
        await self.initialize()

vector_store = VectorStore() 