from datetime import datetime

from sqlalchemy import BigInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kakao_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    kakao_profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    affiliation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="member")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user_sessions = relationship("UserSession", back_populates="user")
    team_members = relationship("TeamMember", back_populates="user")
    created_reservations = relationship("Reservation", back_populates="creator")
    reservation_participations = relationship("ReservationParticipant", back_populates="user")
    notices = relationship("Notice", back_populates="author")
