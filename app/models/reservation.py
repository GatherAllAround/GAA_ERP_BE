from datetime import date, datetime, time

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reservation_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    creator = relationship("User", back_populates="created_reservations")
    participants = relationship("ReservationParticipant", back_populates="reservation")


class ReservationParticipant(Base):
    __tablename__ = "reservation_participants"
    __table_args__ = (UniqueConstraint("reservation_id", "user_id"),)

    participant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reservations.reservation_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="confirmed")
    participated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    reservation = relationship("Reservation", back_populates="participants")
    user = relationship("User", back_populates="reservation_participations")
