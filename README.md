# Uz-Pharma-Bot 💊

A Telegram bot for pharmaceutical services in Uzbekistan. Features partnership application management with admin approval system.

## 🚀 Features

- 🤝 **Partnership Module** - Users can submit partnership applications
- 👨‍💼 **Admin Approval** - Applications are reviewed by administrators
- 🗄️ **PostgreSQL Database** - All data is securely stored
- 📱 **Telegram Bot** - Built with Aiogram 3.x framework

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

# Create database
sudo -u postgres psql
CREATE DATABASE pharma_bot_db;
CREATE USER pharma_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE pharma_bot_db TO pharma_user;
\q
```

### 5. Environment variables

Create a `.env` file in the root directory:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_admin_id_here
DATABASE_URL=postgresql+asyncpg://pharma_user:your_strong_password@localhost:5432/pharma_bot_db
```

### 6. Get Telegram Bot Token

1. Contact [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file

### 7. Get Admin ID

1. Start a chat with [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID to the `.env` file

## 🚀 Running the bot

```bash
python main.py
```

The bot will:
- ✅ Create database tables automatically
- 🤖 Start polling for messages
- 📱 Be ready to accept partnership applications

## 📱 Bot Usage

### For Users:
1. Start the bot with `/start`
2. Click "🤝 Hamkorlik" (Partnership)
3. Fill in the required information:
   - Organization name
   - Contact details
   - Address
   - License/certificate photo
4. Confirm the data
5. Wait for admin approval

### For Admins:
1. Receive partnership applications with photos
2. Click "✅ Tasdiqlash" to approve or "❌ Rad etish" to reject
3. Users will be automatically notified of the decision

## 🗂️ Project Structure

```
Uz-Pharma-Bot/
├── database/
│   ├── __init__.py
│   ├── db.py          # Database connection
│   └── models.py      # SQLAlchemy models
├── handlers/
│   ├── __init__.py
│   ├── admin.py       # Admin handlers (empty)
│   ├── cooperation.py # Partnership module
│   └── start.py       # Start command
├── keyboards/
│   ├── __init__.py
│   └── main_menu.py   # Inline keyboards
├── utils/
│   ├── __init__.py
│   └── config.py      # Configuration
├── main.py            # Bot entry point
├── requirements.txt   # Dependencies
└── .env               # Environment variables
```

## 🗄️ Database Schema

### Applications Table
- `id` - Primary key
- `full_name` - Organization/person name
- `phone` - Contact information
- `pharmacy_name` - Address (stored in pharmacy_name field)
- `approved` - Approval status (True/False/None)
- `created_at` - Timestamp

## 🔄 Workflow

1. **User submits application** → Form data collected via FSM
2. **Admin receives notification** → Photo + details + approval buttons
3. **Admin makes decision** → Approve/Reject buttons
4. **Database updated** → Only approved applications are saved
5. **User notified** → Automatic notification of approval/rejection

## 🛡️ Security Features

- Admin-only approval system
- Input validation
- Error handling
- Secure database connections

## 🚧 Todo / Future Features

- [ ] Drug search functionality
- [ ] Delivery system
- [ ] AI consultation
- [ ] Feedback system
- [ ] Order management
- [ ] Multi-language support

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

---

**Note**: This bot is currently in development. The partnership module is functional, but other features are planned for future releases.


[![Dependabot Updates](https://github.com/PharmaUz/Uz-Pharma-Bot/actions/workflows/dependabot/dependabot-updates/badge.svg?branch=main)](https://github.com/PharmaUz/Uz-Pharma-Bot/actions/workflows/dependabot/dependabot-updates)
