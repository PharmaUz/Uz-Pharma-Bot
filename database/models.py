from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from .db import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)  # Organization/person name
    phone = Column(String, nullable=False)  # Contact information (phone/email)
    pharmacy_name = Column(String, nullable=False)  # Address (currently stored as pharmacy_name)
    approved = Column(Boolean, default=None)  # True = approved, False = rejected, None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Creation timestamp
