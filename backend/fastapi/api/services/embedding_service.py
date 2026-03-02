import os
import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None

    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_local_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a given text."""
        if not text:
            return []

        if self.use_openai:
            return await self._generate_openai_embedding(text)
        else:
            return await self._generate_local_embedding_via_proxy(text)

    async def _generate_local_embedding_via_proxy(self, text: str) -> List[float]:
        """ Delegates embedding generation to the isolated ML process. """
        from ..ml.inference_server import inference_proxy
        try:
            embedding = inference_proxy.run_inference(
                "generate_embedding", 
                {"text": text, "model_name": self.model_name}
            )
            return embedding
        except Exception as e:
            logger.error(f"Inference proxy failed for embedding: {e}. Falling back to local load.")
            # Fallback to loading it in the current process if proxy fails for some reason
            self._load_local_model()
            embedding = self._model.encode(text)
            return embedding.tolist()


    async def _generate_openai_embedding(self, text: str) -> List[float]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.embeddings.create(
                input=[text],
                model=self.openai_model
            )
            return response.data[0].embedding
        except ImportError:
            logger.error("openai not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    def get_dimension(self) -> int:
        """Returns the dimension of the embeddings produced by the current model."""
        if self.use_openai:
            # text-embedding-3-small default is 1536
            # text-embedding-ada-002 is 1536
            return 1536 
        else:
            self._load_local_model()
            # Most sentence-transformers models are 384 or 768
            return self._model.get_sentence_embedding_dimension()

embedding_service = EmbeddingService.get_instance()
