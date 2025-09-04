from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, Date, func
from .db import Base


class Application(Base):
    """ User applications for medicine delivery """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)  # Organization/person name
    phone = Column(String, nullable=False)  # Contact information (phone/email)
    pharmacy_name = Column(String, nullable=False)  # Address (currently stored as pharmacy_name)
    approved = Column(Boolean, default=None)  # True = approved, False = rejected, None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Creation timestamp


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    text = Column(String, nullable=False)
    approved = Column(Boolean, default=None)  # True = approved, False = rejected, None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # drug name
    description = Column(Text, nullable=True)  # short description
    manufacturer = Column(String, nullable=True)  # manufacturer name
    dosage_form = Column(String, nullable=True)  # form: tablet, syrup, injection...
    strength = Column(String, nullable=True)  # dosage strength, e.g., 500mg
    price = Column(Integer, nullable=True, default=0)  # price in local currency
    residual = Column(Integer, nullable=True, default=0)  # stock quantity
    expiration_date = Column(Date, nullable=True)  # expiration date
    prescription_required = Column(Boolean, default=False)  # whether prescription is required
    category = Column(String, nullable=True)  # category: antibiotic, analgesic, etc.
    
    # New added fields
    image_url = Column(String, nullable=True)  # drug image URL
    thumbnail_url = Column(String, nullable=True)  # thumbnail image URL

    def __repr__(self):
        return f"<Drug(name={self.name}, manufacturer={self.manufacturer})>"
