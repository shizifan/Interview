from sqlalchemy import Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    quota: Mapped[int] = mapped_column(Integer, default=1)
    start_coefficient: Mapped[float] = mapped_column(Float, default=1.2)
    min_interview_count: Mapped[int] = mapped_column(Integer, default=5)
    required_license_type: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON数组
    status: Mapped[int] = mapped_column(Integer, default=0)  # 0-草稿 1-发布中 2-已结束

    interviews = relationship("Interview", back_populates="job", lazy="selectin")
    questions = relationship("Question", back_populates="job", lazy="selectin")
    score_pool_entries = relationship("ScorePool", back_populates="job", lazy="selectin")
