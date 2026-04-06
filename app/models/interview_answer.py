from sqlalchemy import Integer, Float, Text, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InterviewAnswer(Base, TimestampMixin):
    __tablename__ = "interview_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview.id"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("question.id"), nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    score_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    interview = relationship("Interview", back_populates="answers")
