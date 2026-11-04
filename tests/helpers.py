"""Small fake embedder so retrieval tests run without downloading a model."""
import math
import re
import zlib


class HashEmbedder:
    """Bag-of-words vectors via hashing. Texts that share words get similar vectors."""

    model_name = "test-hash"
    dim = 512

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for token in re.findall(r"\w+", text.lower()):
            v[zlib.crc32(token.encode("utf-8")) % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_passages(self, texts, batch_size=16):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)
