import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim=1536):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []
        self.metadata = []  # NEW: stores {"username": ..., "filename": ...} per chunk

    # =========================
    # ADD VECTORS
    # =========================
    def add(self, embedding, text, username=None, filename=None):
        embedding = np.array(embedding, dtype="float32")

        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)

        if embedding.shape[1] != self.dim:
            raise ValueError(f"Embedding dim mismatch: expected {self.dim}, got {embedding.shape[1]}")

        self.index.add(embedding)
        self.texts.append(text)
        self.metadata.append({"username": username, "filename": filename})  # NEW

    # =========================
    # SEARCH VECTORS (filtered by username)
    # =========================
    def search(self, query_embedding, k=3, username=None):

        if len(self.texts) == 0:
            return []

        query_embedding = np.array(query_embedding, dtype="float32").reshape(1, -1)

        # Search more candidates so we can filter down to k after username filtering
        fetch_k = min(len(self.texts), k * 10)
        D, I = self.index.search(query_embedding, fetch_k)

        results = []
        for i in I[0]:
            if 0 <= i < len(self.texts):
                # NEW: filter by username if provided
                if username is None or self.metadata[i].get("username") == username:
                    results.append(self.texts[i])
                    if len(results) == k:
                        break

        return results

    # =========================
    # DELETE VECTORS BY FILENAME + USERNAME
    # =========================
    def delete_by_filename(self, filename, username):
        """Remove all chunks belonging to a specific file and user."""
        keep_indices = [
            i for i, m in enumerate(self.metadata)
            if not (m.get("filename") == filename and m.get("username") == username)
        ]

        if len(keep_indices) == len(self.texts):
            return  # nothing to delete

        # Rebuild index with remaining vectors
        kept_texts = [self.texts[i] for i in keep_indices]
        kept_meta = [self.metadata[i] for i in keep_indices]

        new_index = faiss.IndexFlatL2(self.dim)
        if kept_texts:
            # We don't have the original embeddings, so we track them too
            # Re-use stored embeddings array
            kept_embeddings = np.array(
                [self._embeddings[i] for i in keep_indices], dtype="float32"
            )
            new_index.add(kept_embeddings)

        self.index = new_index
        self.texts = kept_texts
        self.metadata = kept_meta
        self._embeddings = [self._embeddings[i] for i in keep_indices] if hasattr(self, '_embeddings') else []

    def add(self, embedding, text, username=None, filename=None):
        """Overwrite add to also store raw embeddings for rebuild support."""
        emb_array = np.array(embedding, dtype="float32")

        if emb_array.ndim == 1:
            emb_array = emb_array.reshape(1, -1)

        if emb_array.shape[1] != self.dim:
            raise ValueError(f"Embedding dim mismatch: expected {self.dim}, got {emb_array.shape[1]}")

        if not hasattr(self, '_embeddings'):
            self._embeddings = []

        self.index.add(emb_array)
        self.texts.append(text)
        self.metadata.append({"username": username, "filename": filename})
        self._embeddings.append(emb_array[0].tolist())