"""Embedding generation powered by LangChain + Vertex AI.

The module lazily initialises a single VertexAIEmbeddings instance so that
every call reuses the same authenticated gRPC channel.
"""

from langchain_google_vertexai import VertexAIEmbeddings

from ..config import settings

_model: VertexAIEmbeddings | None = None


def _get_model() -> VertexAIEmbeddings:
    global _model
    if _model is None:
        _model = VertexAIEmbeddings(
            model_name=settings.embedding_model,
            project=settings.gcp_project_id,
            location=settings.vertex_ai_location,
        )
    return _model


async def generate_embedding(text: str) -> list[float]:
    """Return a single embedding vector for *text*."""
    vectors = await _get_model().aembed_documents([text])
    return vectors[0]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a batch of texts."""
    return await _get_model().aembed_documents(texts)
