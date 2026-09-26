from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class HostedZone(Base):
    __tablename__ = "hosted_zones"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(253), unique=True, index=True)
    comment: Mapped[str] = mapped_column(String(500), default="")
    is_private: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    records: Mapped[list["DNSRecord"]] = relationship(back_populates="zone", cascade="all, delete-orphan")

class DNSRecord(Base):
    __tablename__ = "dns_records"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("hosted_zones.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(253), index=True)
    type: Mapped[str] = mapped_column(String(8), index=True)
    value: Mapped[str] = mapped_column(Text)
    ttl: Mapped[int] = mapped_column(Integer, default=300)
    routing_policy: Mapped[str] = mapped_column(String(40), default="Simple")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    zone: Mapped[HostedZone] = relationship(back_populates="records")
