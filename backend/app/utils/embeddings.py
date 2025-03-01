from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize the model (this will download it if not present)
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> np.ndarray:
    """
    Generate embedding vector for the given text using sentence-transformers.
    
    Args:
        text: Input text to generate embedding for
        
    Returns:
        Numpy array containing the embedding vector
    """
    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True)
    
    # Normalize the embedding vector
    normalized = embedding / np.linalg.norm(embedding)
    return normalized 