"""Build a text representation of a user profile and generate its embedding
via LangChain + Vertex AI.  The resulting vector lives in the same 768-dim
space as the job embeddings so cosine distance is meaningful.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_google_vertexai import VertexAIEmbeddings

from .config import settings

if TYPE_CHECKING:
    from .models import User

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


def build_profile_text(user: User) -> str:
    """Concatenate the most relevant profile fields into a single string
    that can be compared against job description embeddings."""
    parts: list[str] = []

    if user.display_name:
        parts.append(user.display_name)
    if user.bio:
        parts.append(user.bio)
    if user.skills:
        parts.append("Skills: " + ", ".join(user.skills))
    if user.location:
        parts.append("Location: " + user.location)

    return "\n".join(parts) if parts else ""


async def generate_profile_embedding(user: User) -> list[float]:
    text = build_profile_text(user)
    if not text:
        return [0.0] * settings.embedding_dimensions

    vectors = await _get_model().aembed_documents([text])
    return vectors[0]
