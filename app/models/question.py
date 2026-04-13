from sqlalchemy import Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[int] = mapped_column(Integer, default=1)  # 1-基础 2-专业 3-情景
    difficulty: Mapped[int] = mapped_column(Integer, default=2)  # 1-简单 2-中等 3-困难
    score_points: Mapped[str] = mapped_column(Text, nullable=False)  # JSON数组
    follow_up_scripts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON数组
    tts_audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    job = relationship("Job", back_populates="questions")
