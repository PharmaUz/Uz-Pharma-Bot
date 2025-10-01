from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Boolean, 
    DateTime, 
    BigInteger, 
    Text, 
    Date, 
    ForeignKey, 
    Float,  # Added for coordinates
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship
from .db import Base

class BaseModel(Base):
    __abstract__ = True
    def __init__(self, *args, **kwargs):
        # Call SQLAlchemy Base __init__
        super().__init__(*args, **kwargs)

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
    expiration_date = Column(Date, nullable=True)  # expiration date
    prescription_required = Column(Boolean, default=False)  # whether prescription is required
    category = Column(String, nullable=True)  # category: antibiotic, analgesic, etc.
    
    # Image fields
    image_url = Column(String, nullable=True)  # drug image URL
    thumbnail_url = Column(String, nullable=True)  # thumbnail image URL

    def __repr__(self):
        return f"<Drug(name={self.name}, manufacturer={self.manufacturer})>"


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Geographic coordinates for location-based search
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Additional location information
    district = Column(String, nullable=True)
    city = Column(String, nullable=True, default="Tashkent")
    
    # Working hours and status
    working_hours = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_24_hours = Column(Boolean, default=False)
    
    # Timestamps - BU QATORLARNI QAYTARING
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Pharmacy(name={self.name}, address={self.address}, lat={self.latitude}, lon={self.longitude})>"

class PharmacyDrug(BaseModel):
    __tablename__ = "pharmacy_drugs"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"))
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"))

    price = Column(Integer, nullable=True, default=0)  # Price at this specific pharmacy
    residual = Column(Integer, nullable=True, default=0)  # Stock quantity available

    pharmacy = relationship("Pharmacy", backref="pharmacy_drugs")
    drug = relationship("Drug", backref="pharmacy_drugs")

    __table_args__ = (
        UniqueConstraint("pharmacy_id", "drug_id", name="uix_pharmacy_drug"),
    )

    def __repr__(self):
        return f"<PharmacyDrug(pharmacy={self.pharmacy_id}, drug={self.drug_id}, residual={self.residual})>"


class Cart(BaseModel):
    """User's shopping cart for medicines"""
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)  # Telegram user ID
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)  # quantity of drug in cart
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    drug = relationship("Drug", backref="cart_items")

    __table_args__ = (
        UniqueConstraint("user_id", "drug_id", name="uix_user_drug_cart"),
    )

    def __repr__(self):
        return f"<Cart(user_id={self.user_id}, drug_id={self.drug_id}, quantity={self.quantity})>"


class Order(BaseModel):
    """User orders"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)  # Telegram user ID

    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="SET NULL"), nullable=True)  # Selected pharmacy
    
    full_name = Column(String, nullable=False)  # Customer name
    phone = Column(String, nullable=False)  # Customer phone / pickup code
    address = Column(String, nullable=False)  # Delivery address or pharmacy address
    
    total_amount = Column(Integer, default=0)  # Total order amount
    delivery_type = Column(String, default="pickup")  # "pickup" or "delivery"
    pickup_code = Column(String, nullable=True)  # Unique pickup code for pharmacy pickup
    
    status = Column(String, default="pending")  # pending, confirmed, ready, completed, cancelled
    payment_status = Column(String, default="unpaid")  # unpaid, paid, refunded
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When order was completed

    # Relationship
    pharmacy = relationship("Pharmacy", backref="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status}, pickup_code={self.pickup_code})>"

      
class OrderItem(BaseModel):
    """Order items"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # Price at time of order

    # Relationships
    order = relationship("Order", backref="order_items")
    drug = relationship("Drug", backref="order_items")

    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, drug_id={self.drug_id}, quantity={self.quantity})>"