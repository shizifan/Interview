from sqlalchemy import Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate.id"), nullable=False, index=True)
    type: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-身份证 2-驾驶证 3-从业资格证 4-其他
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    status: Mapped[int] = mapped_column(Integer, default=0)  # 0-待审核 1-审核中 2-通过 3-拒绝
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    candidate = relationship("Candidate", back_populates="documents")
