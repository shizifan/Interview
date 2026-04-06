from sqlalchemy import Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Interview(Base, TimestampMixin):
    __tablename__ = "interview"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate.id"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job.id"), nullable=False, index=True)
    start_time: Mapped[str | None] = mapped_column(String(30), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)  # 0-待开始 1-进行中 2-已完成 3-已中断 4-已取消
    score: Mapped[float] = mapped_column(Float, default=0.0)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    current_node: Mapped[str] = mapped_column(String(30), default="intro")
    interview_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # LangGraph状态快照JSON
    report_content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown评估报告

    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    answers = relationship("InterviewAnswer", back_populates="interview", lazy="selectin")
