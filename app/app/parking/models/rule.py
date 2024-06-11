from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base import RuleType


class Rule(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name_fa: Mapped[str] = mapped_column(String(50), default="")
    rule_type: Mapped[RuleType] = mapped_column(Integer, nullable=True)
    start_datetime = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow
    )
    end_datetime = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow
    )
    registeration_date = mapped_column(Date, default=date.today)

    zones = relationship("ZoneRule", back_populates="rule", lazy="immediate")
    plates = relationship("PlateRule", back_populates="rule", lazy="immediate")


class ZoneRule(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkingzone.id"), nullable=True
    )
    zone = relationship("ParkingZone", back_populates="rules")
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rule.id"),
        nullable=True,
    )
    rule = relationship("Rule", back_populates="zones")


class PlateRule(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plate: Mapped[str] = mapped_column(String(50))
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rule.id"),
        nullable=True,
    )
    rule = relationship("Rule", back_populates="plates")
