# Uz-Pharma-Bot 💊

A Telegram bot for pharmaceutical services in Uzbekistan. Features partnership application management with admin approval system.

## 🚀 Features

### Core Functionality
- 🤝 **Partnership Module** - Users can submit partnership applications
- 👨‍💼 **Admin Approval System** - Applications are reviewed by administrators
- � **Shopping Cart** - Add medicines to cart and manage quantities
- 🏥 **Drug Search & Purchase** - Search for medicines and add to cart
- 📍 **Location-based Pharmacy Search** - Find nearest pharmacies with required medicines
- 📦 **Order Management System** - Complete order flow from cart to delivery

### Advanced Features  
- 🤖 **AI Medical Consultation** - Get AI-powered health advice (5 questions/day)
- 📊 **Pharmacy Dashboard** - Pharmacies can manage orders and view statistics
- 🔍 **Intelligent Drug Search** - Inline search for medicines with detailed info
- 🚚 **Pickup & Delivery Options** - Choose between pharmacy pickup or delivery
- 💳 **Order Status Tracking** - Track orders from pending to completed
- 📞 **Multi-language Support** - Uzbek language interface

### Technical Features
- 🗄️ **PostgreSQL Database** - Comprehensive data storage with relationships
- 📱 **Telegram Bot** - Built with Aiogram 3.x framework
- 🔐 **User Authentication** - Role-based access (regular users, pharmacy admins)
- 📈 **Real-time Updates** - Live order status updates for both users and pharmacies
- 🛡️ **Data Validation** - Input validation and error handling

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- Telegram Bot Token
- Admin Telegram ID

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/PharmaUz/Uz-Pharma-Bot.git
cd Uz-Pharma-Bot
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. PostgreSQL setup

Install PostgreSQL and create database:

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE pharma_bot_db;
CREATE USER pharma_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE pharma_bot_db TO pharma_user;
ALTER USER pharma_user CREATEDB;
\q
```

### 5. Environment variables

Create a `.env` file in the root directory:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_admin_id_here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://pharma_user:your_strong_password@localhost:5432/pharma_bot_db

# AI Configuration (Optional - for AI consultation feature)
GROQ_API_KEY=your_groq_api_key_here

# Additional Configuration
DEBUG=True
LOG_LEVEL=INFO
```

### 6. Get Telegram Bot Token

1. Contact [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file

### 7. Get Admin ID

1. Start a chat with [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID to the `.env` file

## 🚀 Running the bot

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
# Install process manager (optional)
pip install supervisor

# Or use systemd service
sudo systemctl enable pharma-bot
sudo systemctl start pharma-bot
```

The bot will:
- ✅ Create all database tables automatically (8+ tables)
- 🤖 Start polling for Telegram messages
- 📱 Accept partnership applications and user registrations
- 🛒 Handle drug searches and order placements
- 🤖 Provide AI medical consultations
- 📊 Enable pharmacy management dashboards
- 🔄 Process real-time order status updates

## 📱 Bot Usage

### For Regular Users:

#### 🛒 Shopping & Orders
1. **Drug Search**: Use inline search or menu to find medicines
2. **Add to Cart**: Select drugs and add desired quantities
3. **View Cart**: Review items, modify quantities, or remove items
4. **Place Order**: Choose delivery type (pickup/delivery)
5. **Location**: Share location to find nearest pharmacies
6. **Pharmacy Selection**: Choose from available pharmacies with your medicines
7. **Order Confirmation**: Review order details and confirm
8. **Track Order**: Monitor order status updates

#### 🤖 AI Medical Consultation
1. Click "🤖 AI Konsultatsiya" from main menu
2. Ask health-related questions (5 per day limit)
3. Receive AI-powered medical advice
4. Clear conversation history if needed

#### 🤝 Partnership Application
1. Click "🤝 Hamkorlik" (Partnership)
2. Fill in organization details and contact information
3. Upload license/certificate photo
4. Wait for admin approval

### For Pharmacy Owners:
1. **Dashboard Access**: Get pharmacy management interface
2. **View Orders**: See all orders with status filtering
3. **Order Management**: 
   - View pending orders
   - Confirm orders
   - Mark orders as ready
   - Complete orders
4. **Statistics**: Track performance metrics and revenue
5. **Status Updates**: Orders automatically filtered by status

### For Admins:
1. **Partnership Approval**: Review and approve/reject applications
2. **User Management**: Manage user accounts and permissions
3. **Product Management**: Add/edit medicines in database
4. **Order Oversight**: Monitor all platform orders
5. **System Settings**: Configure bot parameters

## 🗂️ Project Structure

```
Uz-Pharma-Bot/
├── database/
│   ├── __init__.py
│   ├── db.py              # Database connection & session management
│   └── models.py          # SQLAlchemy models (8+ tables)
├── handlers/
│   ├── __init__.py
│   ├── ai_assistant.py    # AI medical consultation with Groq API
│   ├── cooperation.py     # Partnership application system
│   ├── feedback.py        # User feedback collection
│   ├── filter.py          # Message filtering & routing
│   ├── start.py           # Start command & main menu
│   ├── admin/             # Admin panel modules
│   │   ├── __init__.py
│   │   ├── router.py      # Admin router configuration
│   │   ├── back_button.py # Navigation utilities
│   │   ├── orders.py      # Order management
│   │   ├── products.py    # Product/drug management
│   │   ├── settings.py    # System settings
│   │   └── users.py       # User management
│   ├── order/             # Complete order system
│   │   ├── __init__.py
│   │   ├── cart.py        # Shopping cart functionality
│   │   ├── flow.py        # Order placement workflow
│   │   ├── search.py      # Drug search & inline queries
│   │   └── utils.py       # Helper functions
│   └── tests/             # Test handlers
│       └── order.py       # Order system tests
├── keyboards/
│   ├── __init__.py
│   ├── main_menu.py       # Main user interface
│   ├── admin_menu.py      # Admin panel keyboards
│   └── pharmacy_menu.py   # Pharmacy dashboard
├── users/
│   ├── __init__.py
│   └── pharmacy.py        # Pharmacy owner interface
├── utils/
│   ├── __init__.py
│   └── config.py          # Bot configuration
├── data/
│   ├── __pycache__/
│   └── transfer.py        # Data migration utilities
├── main.py                # Bot entry point with all routers
├── loader.py              # Bot and dispatcher initialization
├── requirements.txt       # Dependencies (25+ packages)
├── tests.py               # Main test suite
└── .env                   # Environment variables
```

## 🗄️ Database Schema

### Core Tables

#### Users Table
- `id` - Primary key
- `telegram_id` - Unique Telegram user ID
- `username` - Telegram username
- `fullname` - Full name
- `phone_number` - Contact number
- `status` - User role (regular/pharmacy_admin)

#### Applications Table (Partnership)
- `id` - Primary key
- `full_name` - Organization/person name
- `phone` - Contact information
- `pharmacy_name` - Address information
- `approved` - Approval status (True/False/None)
- `created_at` - Timestamp

#### Drugs Table
- `id` - Primary key
- `drug_id` - External API reference
- `name` - Medicine name
- `description` - Detailed description
- `manufacturer` - Producer information
- `dosage_form` - Form (tablet, syrup, injection)
- `strength` - Dosage strength (e.g., 500mg)
- `price` - Base price
- `expiration_date` - Expiry date
- `prescription_required` - Prescription requirement
- `category` - Medicine category
- `image_url` - Product image
- `thumbnail_url` - Thumbnail image

#### Pharmacies Table
- `id` - Primary key
- `name` - Pharmacy name
- `address` - Full address
- `tg_id` - Telegram ID of pharmacy admin
- `phone` - Contact number
- `latitude/longitude` - GPS coordinates
- `district/city` - Location details
- `working_hours` - Operating hours
- `is_active` - Active status
- `is_24_hours` - 24/7 availability

### Order Management Tables

#### Orders Table
- `id` - Primary key
- `user_id` - Customer Telegram ID
- `pharmacy_id` - Selected pharmacy
- `full_name` - Customer name
- `phone` - Contact/pickup code
- `address` - Delivery address
- `total_amount` - Total cost
- `delivery_type` - Pickup/delivery
- `pickup_code` - Unique pickup identifier
- `status` - Order status (pending/confirmed/ready/completed/cancelled)
- `payment_status` - Payment state
- `created_at/updated_at/completed_at` - Timestamps

#### Order Items Table
- `id` - Primary key
- `order_id` - Parent order reference
- `drug_id` - Medicine reference
- `quantity` - Ordered quantity
- `price` - Price at time of order

#### Cart Table (Shopping Cart)
- `id` - Primary key
- `user_id` - Customer Telegram ID
- `drug_id` - Medicine reference
- `quantity` - Cart quantity
- `created_at/updated_at` - Timestamps

### Supporting Tables

#### Pharmacy Drugs Table (Inventory)
- `id` - Primary key
- `pharmacy_id` - Pharmacy reference
- `drug_id` - Medicine reference
- `price` - Pharmacy-specific price
- `residual` - Available stock

#### Comments Table (Feedback)
- `id` - Primary key
- `user_id` - Commenter Telegram ID
- `username` - Telegram username
- `text` - Feedback content
- `approved` - Admin approval status
- `created_at` - Timestamp

## 🔄 Workflows

### 🛒 Order Placement Workflow
1. **Drug Search** → User searches medicines via inline query or menu
2. **Add to Cart** → Selected drugs added with quantities
3. **Cart Management** → View, modify, or remove items from cart
4. **Location Sharing** → User shares location for pharmacy search
5. **Pharmacy Discovery** → System finds nearby pharmacies with required drugs
6. **Pharmacy Selection** → User chooses preferred pharmacy
7. **Order Confirmation** → Review total, pharmacy details, pickup code
8. **Order Placement** → Order saved to database, notifications sent
9. **Status Updates** → Real-time updates (pending → confirmed → ready → completed)

### 🤝 Partnership Application Workflow
1. **Application Submission** → User fills partnership form via FSM
2. **Document Upload** → License/certificate photo uploaded
3. **Admin Notification** → Admin receives application with details
4. **Review Process** → Admin approves or rejects application
5. **Database Update** → Application status updated
6. **User Notification** → Automatic approval/rejection notification

### 🏥 Pharmacy Management Workflow
1. **Order Receipt** → Pharmacy receives new order notifications
2. **Order Review** → Pharmacy views order details and items
3. **Order Confirmation** → Pharmacy confirms order availability
4. **Preparation** → Order marked as "ready" when prepared
5. **Customer Pickup/Delivery** → Order completed and marked as finished
6. **Statistics Tracking** → Performance metrics updated

### 🤖 AI Consultation Workflow
1. **Menu Access** → User selects AI consultation from main menu
2. **Question Input** → User types health-related question
3. **API Processing** → Question sent to Groq API with conversation history
4. **Response Generation** → AI generates medical advice
5. **Response Formatting** → Clean and format response for Telegram
6. **Daily Limit Check** → Track user's daily question count (5 max)

## 🛡️ Security & Quality Features

### Security
- **Role-based Access Control** - Different permissions for users, pharmacy admins, and system admins
- **Admin-only Approval System** - Partnership applications require admin approval
- **Input Validation** - All user inputs are validated and sanitized
- **SQL Injection Prevention** - Using SQLAlchemy ORM with parameterized queries
- **Rate Limiting** - AI consultation limited to 5 questions per day per user
- **Secure Database Connections** - Async PostgreSQL with connection pooling

### Quality Assurance
- **Comprehensive Error Handling** - Try-catch blocks for all critical operations
- **Logging System** - Detailed logging for debugging and monitoring
- **Data Validation** - Pydantic models for data structure validation
- **Transaction Management** - Database transactions with rollback capability
- **API Timeout Handling** - Proper timeout management for external API calls
- **Memory Management** - Efficient session handling and resource cleanup

## ✅ Completed Features

- [x] **Drug Search & Purchase System** - Complete inline search with cart functionality
- [x] **Order Management System** - Full order flow from cart to delivery
- [x] **AI Medical Consultation** - Groq API integration with daily limits
- [x] **Feedback System** - User feedback collection with admin approval
- [x] **Multi-user Support** - Role-based access for users, pharmacy admins
- [x] **Location-based Services** - Find nearest pharmacies using GPS
- [x] **Real-time Status Updates** - Order tracking for users and pharmacies
- [x] **Shopping Cart** - Add/remove items, quantity management
- [x] **Pharmacy Dashboard** - Order management and statistics
- [x] **Admin Panel** - User, product, and order management
- [x] **Database Relations** - Complete normalized schema with foreign keys

## 🚧 Future Enhancements

- [ ] **Payment Integration** - Online payment processing (Click, Payme, etc.)
- [ ] **Advanced AI Features** - Drug interaction checking, dosage calculator
- [ ] **Delivery Tracking** - Real-time GPS tracking for delivery orders
- [ ] **Prescription Management** - Digital prescription upload and verification
- [ ] **Multi-language Support** - Russian and English language options
- [ ] **Push Notifications** - SMS/email notifications for order updates
- [ ] **Analytics Dashboard** - Advanced statistics and reporting
- [ ] **API Documentation** - RESTful API for third-party integrations
- [ ] **Mobile App** - Native iOS/Android companion apps
- [ ] **Inventory Automation** - Auto-reorder when stock is low

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please contact the project maintainer.

## 📊 Current Statistics

- **Database Tables**: 8+ fully implemented tables with relationships
- **Handlers**: 15+ handler modules with 50+ callback functions
- **Features**: 10+ major features implemented and tested
- **Code Coverage**: Comprehensive error handling and logging
- **API Integration**: Groq AI API for medical consultations
- **User Roles**: 3 different user types (Regular, Pharmacy Admin, System Admin)

## 🔧 Technical Stack

- **Backend**: Python 3.8+ with AsyncIO
- **Bot Framework**: Aiogram 3.x (latest)
- **Database**: PostgreSQL 12+ with AsyncPG driver
- **ORM**: SQLAlchemy 2.0 with async support
- **API Integration**: Groq AI API for medical consultations
- **Deployment**: Docker-ready with environment configuration
- **Dependencies**: 25+ carefully selected packages

## 📈 Performance Features

- **Async Operations**: All database and API calls are asynchronous
- **Connection Pooling**: Efficient database connection management
- **Caching**: User conversation history and session management
- **Rate Limiting**: API call limits and user interaction throttling
- **Error Recovery**: Graceful error handling with user-friendly messages
- **Scalability**: Designed to handle multiple concurrent users

---

**Current Status**: 🟢 **Production Ready** - All major features implemented and tested. The bot handles complete pharmaceutical ordering workflow, AI consultations, and pharmacy management.


[![Dependabot Updates](https://github.com/PharmaUz/Uz-Pharma-Bot/actions/workflows/dependabot/dependabot-updates/badge.svg?branch=main)](https://github.com/PharmaUz/Uz-Pharma-Bot/actions/workflows/dependabot/dependabot-updates)
