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
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship
from .db import Base

class BaseModel(Base):
    __abstract__ = True
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)




class Application(Base):
    """
    Represents a user application for medicine delivery.

    Attributes:
        id (int): Primary key, unique identifier for the application.
        full_name (str): Name of the organization or person applying.
        phone (str): Contact information, such as phone number or email.
        pharmacy_name (str): Name of the pharmacy or address associated with the application.
        approved (bool or None): Approval status of the application. 
            True if approved, False if rejected, None if pending.
        created_at (datetime): Timestamp indicating when the application was created.
    """
    """ User applications for medicine delivery """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)  # Organization/person name
    phone = Column(String, nullable=False)  # Contact information (phone/email)
    pharmacy_name = Column(String, nullable=False)  # Address (currently stored as pharmacy_name)
    approved = Column(Boolean, default=None)  # True = approved, False = rejected, None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Creation timestamp


class Comment(Base):
    """
    Represents a comment made by a user.

    Attributes:
        id (int): Primary key, unique identifier for the comment.
        user_id (int): Telegram user ID of the commenter.
        username (str, optional): Username of the commenter, if available.
        text (str): The content of the comment.
        approved (bool or None): Approval status of the comment.
            - True: Approved
            - False: Rejected
            - None: Pending review
        created_at (datetime): Timestamp when the comment was created (timezone-aware).
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    text = Column(String, nullable=False)
    approved = Column(Boolean, default=None)  # True = approved, False = rejected, None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Drug(Base):
    """
    Represents a drug entity in the pharmaceutical database.
    Attributes:
        id (int): Primary key, unique identifier for the drug.
        name (str): Name of the drug. (Required)
        description (str, optional): Short description of the drug.
        manufacturer (str, optional): Name of the manufacturer.
        dosage_form (str, optional): Dosage form (e.g., tablet, syrup, injection).
        strength (str, optional): Dosage strength (e.g., 500mg).
        price (int, optional): Price in local currency. Defaults to 0.
        expiration_date (date, optional): Expiration date of the drug.
        prescription_required (bool): Indicates if a prescription is required. Defaults to False.
        category (str, optional): Drug category (e.g., antibiotic, analgesic).
        image_url (str, optional): URL to the drug's image.
        thumbnail_url (str, optional): URL to the drug's thumbnail image.
    Methods:
        __repr__(): Returns a string representation of the Drug instance.
    """
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
    
    # New added fields
    image_url = Column(String, nullable=True)  # drug image URL
    thumbnail_url = Column(String, nullable=True)  # thumbnail image URL

    def __repr__(self):
        return f"<Drug(name={self.name}, manufacturer={self.manufacturer})>"


class Pharmacy(Base):
    """
    Represents a pharmacy entity in the database.

    Attributes:
        id (int): Primary key, unique identifier for the pharmacy.
        name (str): Name of the pharmacy. Cannot be null.
        address (str, optional): Address of the pharmacy.
        phone (str, optional): Contact phone number of the pharmacy.

    Methods:
        __repr__(): Returns a string representation of the Pharmacy instance.
    """
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    def __repr__(self):
        return f"<Pharmacy(name={self.name}, address={self.address})>"


class PharmacyDrug(BaseModel):
    """
    Represents the association between a pharmacy and a drug, including inventory and pricing information.

    Attributes:
        id (int): Primary key for the PharmacyDrug record.
        pharmacy_id (int): Foreign key referencing the associated pharmacy.
        drug_id (int): Foreign key referencing the associated drug.
        price (int, optional): Price of the drug in the pharmacy. Defaults to 0.
        residual (int, optional): Remaining quantity of the drug in the pharmacy. Defaults to 0.
        pharmacy (Pharmacy): Relationship to the Pharmacy model.
        drug (Drug): Relationship to the Drug model.

    Constraints:
        UniqueConstraint: Ensures that each (pharmacy_id, drug_id) pair is unique.

    Methods:
        __repr__(): Returns a string representation of the PharmacyDrug instance.
    """
    __tablename__ = "pharmacy_drugs"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"))
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"))

    price = Column(Integer, nullable=True, default=0)
    residual = Column(Integer, nullable=True, default=0)

    pharmacy = relationship("Pharmacy", backref="pharmacy_drugs")
    drug = relationship("Drug", backref="pharmacy_drugs")

    __table_args__ = (
        UniqueConstraint("pharmacy_id", "drug_id", name="uix_pharmacy_drug"),
    )

    def __repr__(self):
        return f"<PharmacyDrug(pharmacy={self.pharmacy_id}, drug={self.drug_id}, residual={self.residual})>"


class Cart(BaseModel):
    """
    Represents a user's shopping cart entry for medicines.

    Attributes:
        id (int): Primary key for the cart entry.
        user_id (int): Telegram user ID associated with the cart.
        drug_id (int): Foreign key referencing the drug in the cart.
        quantity (int): Number of units of the drug in the cart (default is 1).
        created_at (datetime): Timestamp when the cart entry was created.
        updated_at (datetime): Timestamp when the cart entry was last updated.
        drug (Drug): Relationship to the Drug model for the associated drug.

    Constraints:
        UniqueConstraint on (user_id, drug_id): Ensures a user cannot have duplicate entries for the same drug in their cart.

    Methods:
        __repr__(): Returns a string representation of the cart entry.
    """
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
    """
    Represents a user order in the system.

    Attributes:
        id (int): Primary key for the order.
        user_id (int): Telegram user ID of the customer placing the order.
        full_name (str): Full name of the customer.
        phone (str): Phone number of the customer.
        address (str): Delivery address for the order.
        total_amount (int): Total amount for the order. Defaults to 0.
        status (str): Status of the order. Possible values: 'pending', 'confirmed', 'delivered', 'cancelled'. Defaults to 'pending'.
        created_at (datetime): Timestamp when the order was created.
        updated_at (datetime): Timestamp when the order was last updated.
    """
    """User orders"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)  # Telegram user ID
    full_name = Column(String, nullable=False)  # Customer name
    phone = Column(String, nullable=False)  # Customer phone
    address = Column(String, nullable=False)  # Delivery address
    total_amount = Column(Integer, default=0)  # Total order amount
    status = Column(String, default="pending")  # pending, confirmed, delivered, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"


class OrderItem(BaseModel):
    """
    Represents an item within an order, linking a specific drug to an order with a specified quantity and price.

    Attributes:
        id (int): Primary key for the order item.
        order_id (int): Foreign key referencing the associated order.
        drug_id (int): Foreign key referencing the associated drug.
        quantity (int): The number of units of the drug ordered.
        price (int): The price of the drug at the time of the order.

    Relationships:
        order (Order): The order to which this item belongs.
        drug (Drug): The drug associated with this order item.
    """
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
    

class User(BaseModel):
    """
    Represents a user in the system.
    Attributes:
        id (int): Primary key, unique identifier for the user.
        telegram_id (int): Unique Telegram user ID.
        username (str, optional): Telegram username of the user.
        full_name (str, optional): Full name of the user.
        phone_number (str, optional): Phone number of the user.
    Methods:
        __repr__(): Returns a string representation of the User instance.
    """
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    def __repr__(self):
        return f"<User {self.telegram_id} - {self.username}>"
