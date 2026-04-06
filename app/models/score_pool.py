from sqlalchemy import Integer, Float, Boolean, ForeignKey, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ScorePool(Base, TimestampMixin):
    __tablename__ = "score_pool"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job.id"), nullable=False)
    doc_score: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_invited: Mapped[bool] = mapped_column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="score_pool_entries")
    job = relationship("Job", back_populates="score_pool_entries")
