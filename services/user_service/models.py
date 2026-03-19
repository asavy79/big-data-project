from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .config import settings
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Firebase UID
    email = Column(String)
    display_name = Column(String)
    bio = Column(Text)
    skills = Column(ARRAY(String), default=[])
    location = Column(String)
    remote_preference = Column(Boolean, default=True)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    needs_refresh = Column(Boolean, default=False)

    # 768-dim vector built from bio + skills for matching against job embeddings
    embedding = Column(Vector(settings.embedding_dimensions))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    matches = relationship("UserMatch", back_populates="user", order_by="UserMatch.calculated_at.desc()")


class UserMatch(Base):
    __tablename__ = "user_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    matched_job_ids = Column(ARRAY(Integer), default=[])
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="matches")
