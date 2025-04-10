from sqlalchemy import Integer, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Ticket(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("record.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    record_rel = relationship("Record", foreign_keys=record_id)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bill.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    bill_rel = relationship("Bill", foreign_keys=bill_id)

    correct_plate: Mapped[str] = mapped_column(
        String, nullable=True, index=True
    )

    requesting_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    requesting_user_rel = relationship("User", foreign_keys=requesting_user_id)

    verifying_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    verifying_user_rel = relationship("User", foreign_keys=verifying_user_id)

    additional_data: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=True
    )

    type: Mapped[str] = mapped_column(String, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)
