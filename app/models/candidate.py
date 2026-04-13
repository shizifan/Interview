from sqlalchemy import Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), default="")
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    id_card: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    gender: Mapped[int] = mapped_column(Integer, default=1)  # 1-男 2-女
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education: Mapped[str | None] = mapped_column(String(20), nullable=True)
    work_experience: Mapped[int] = mapped_column(Integer, default=0)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=0)  # 0-未审核 1-审核中 2-通过 3-拒绝
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    qualification_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 评分明细

    documents = relationship("Document", back_populates="candidate", lazy="selectin")
    interviews = relationship("Interview", back_populates="candidate", lazy="selectin")
    score_pool_entries = relationship("ScorePool", back_populates="candidate", lazy="selectin")
