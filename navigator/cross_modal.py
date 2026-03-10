"""
Cross-modal encoders and retrieval index using CLIP.
Supports searching for images using text queries, and vice-versa.
"""

import os
from PIL import Image
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass

import numpy as np
import faiss
import structlog

from navigator.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class MultimodalItem:
    """An item in the multimodal index (text or image)."""
    id: str
    type: str  # "text" or "image"
    content: str  # Text snippet or path to image
    source: str
    metadata: dict


@dataclass
class SearchResult:
    item: MultimodalItem
    score: float


class CrossModalIndex:
    """
    Unified index for text and images using CLIP embeddings.
    Allows for text->image, image->text, and text->text retrieval.
    """

    def __init__(self, demo_mode: Optional[bool] = None):
        self.demo_mode = demo_mode if demo_mode is not None else settings.demo_mode
        self.dimension = 512  # CLIP ViT-B/32 output dimension
        self.index = faiss.IndexFlatIP(self.dimension)
        self.items: List[MultimodalItem] = []
        
        self._model = None
        self._processor = None
        self._tokenizer = None

    def _load_model(self):
        """Lazy load CLIP model."""
        if self._model is not None or self.demo_mode:
            return

        try:
            from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
            import torch
            
            logger.info("loading_clip_model", model=settings.clip_model)
            self._model = CLIPModel.from_pretrained(settings.clip_model)
            self._processor = CLIPProcessor.from_pretrained(settings.clip_model)
            self._tokenizer = CLIPTokenizer.from_pretrained(settings.clip_model)
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self.device)
            self._model.eval()
            logger.info("clip_model_loaded", device=self.device)
        except Exception as e:
            logger.error("failed_to_load_clip", error=str(e))
            self.demo_mode = True

    def encode_text(self, texts: List[str]) -> np.ndarray:
        """Encode text strings into CLIP embedding space."""
        if self.demo_mode:
            return self._mock_encode(texts)
            
        self._load_model()
        import torch
        
        with torch.no_grad():
            inputs = self._tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
            embeddings = self._model.get_text_features(**inputs)
            # Normalize
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            return embeddings.cpu().numpy()

    def encode_image(self, image_paths: List[str]) -> np.ndarray:
        """Encode images into CLIP embedding space."""
        if self.demo_mode:
            return self._mock_encode(image_paths)
            
        self._load_model()
        import torch
        
        images = []
        for path in image_paths:
            try:
                images.append(Image.open(path).convert("RGB"))
            except Exception as e:
                logger.warning("failed_to_load_image", path=path, error=str(e))
                # Create a blank image as fallback
                images.append(Image.new('RGB', (224, 224), color = 'white'))
                
        with torch.no_grad():
            inputs = self._processor(images=images, return_tensors="pt").to(self.device)
            embeddings = self._model.get_image_features(**inputs)
            # Normalize
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            return embeddings.cpu().numpy()

    def add_texts(self, texts: List[str], ids: List[str], sources: List[str], metadatas: List[dict]):
        """Add text items to the index."""
        embeddings = self.encode_text(texts)
        self.index.add(embeddings.astype(np.float32))
        
        for t, i, s, m in zip(texts, ids, sources, metadatas):
            self.items.append(MultimodalItem(id=i, type="text", content=t, source=s, metadata=m))
            
        logger.info("added_texts", count=len(texts), total_size=len(self.items))

    def add_images(self, image_paths: List[str], ids: List[str], sources: List[str], metadatas: List[dict]):
        """Add image items to the index."""
        embeddings = self.encode_image(image_paths)
        self.index.add(embeddings.astype(np.float32))
        
        for p, i, s, m in zip(image_paths, ids, sources, metadatas):
            self.items.append(MultimodalItem(id=i, type="image", content=p, source=s, metadata=m))
            
        logger.info("added_images", count=len(image_paths), total_size=len(self.items))

    def search_by_text(self, query: str, top_k: int = 5, item_type: Optional[str] = None) -> List[SearchResult]:
        """Search for items (text or image) using a text query."""
        if not self.items:
            return []
            
        query_embedding = self.encode_text([query])
        return self._search(query_embedding, top_k, item_type)

    def search_by_image(self, image_path: str, top_k: int = 5, item_type: Optional[str] = None) -> List[SearchResult]:
        """Search for items using an image query."""
        if not self.items:
            return []
            
        query_embedding = self.encode_image([image_path])
        return self._search(query_embedding, top_k, item_type)

    def _search(self, embedding: np.ndarray, top_k: int, item_type: Optional[str]) -> List[SearchResult]:
        # Search more if we need to filter
        search_k = top_k * 3 if item_type else top_k
        search_k = min(search_k, len(self.items))
        
        scores, indices = self.index.search(embedding.astype(np.float32), search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.items):
                continue
                
            item = self.items[idx]
            
            # Apply filter
            if item_type and item.type != item_type:
                continue
                
            results.append(SearchResult(item=item, score=float(score)))
            
            if len(results) >= top_k:
                break
                
        return results

    def _mock_encode(self, inputs: List[str]) -> np.ndarray:
        """Generate deterministic mock embeddings."""
        import hashlib
        embeddings = []
        for text in inputs:
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            emb = rng.randn(self.dimension).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
        return np.array(embeddings)
