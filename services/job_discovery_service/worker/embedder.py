"""Embedding generation powered by LangChain + Vertex AI.

The module lazily initialises a single VertexAIEmbeddings instance so that
every call reuses the same authenticated gRPC channel.

Vertex embedding APIs enforce a per-request token budget (~20k for
text-embedding-004). LangChain's ``embed_documents([a,b,c,...])`` sends all
strings in a single RPC, so their token counts add up. We truncate each
input and issue one embedding RPC per text (with bounded concurrency).
"""

import asyncio

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


def _truncate_for_embedding(text: str) -> str:
    limit = settings.max_embedding_input_chars
    if len(text) <= limit:
        return text
    return text[:limit]


async def generate_embedding(text: str) -> list[float]:
    """Return a single embedding vector for *text*."""
    t = _truncate_for_embedding(text)
    vectors = await _get_model().aembed_documents([t])
    return vectors[0]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for each text (one Vertex request per text)."""
    if not texts:
        return []

    model = _get_model()
    truncated = [_truncate_for_embedding(t or "") for t in texts]
    sem = asyncio.Semaphore(settings.embedding_request_concurrency)

    async def _one(t: str) -> list[float]:
        async with sem:
            return (await model.aembed_documents([t]))[0]

    return await asyncio.gather(*(_one(t) for t in truncated))
