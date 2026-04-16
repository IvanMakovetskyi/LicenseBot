# 🤖 LicenseBot

A **Telegram automation bot** built with **Python and Aiogram** to manage client workflows, automate communication, and simplify administrative tasks.

LicenseBot allows admins to manage clients and send predefined workflow messages based on the client's **US state and process stage**.

---

# ✨ Features

## 👤 Client Management
- Create new clients
- View all clients
- Delete clients
- Store client information in database

## 📨 Automated Messaging
- Predefined message templates
- Organized workflows per **US State**
- Dynamic placeholders for variables (amount, file number, etc.)

## 🛠 Admin Panel
Hidden admin interface accessible through command:

```
/admin
```

Admin panel allows:

- Viewing clients
- Sending workflow messages
- Managing communication
- Deleting clients

---

# 🧠 State-Based Message System

Messages are organized by **US state workflow**.

Example workflow for **California**:

```
CA
├ welcome
├ payment
├ form
├ documents_ready
├ license_approved
├ board_created
├ application_completed
├ board_message
├ email_check
├ congratulations
└ review
```

Different states may have **different workflows**.

---

# 🏗 Project Structure

```
LicenseBot
│
├── app
│   │
│   ├── handlers
│   │   ├── admin.py
│   │   ├── createClient.py
│   │   ├── deleteClient.py
│   │   └── send.py
│   │
│   ├── services
│   │   ├── clientService.py
│   │   └── sendService.py
│   │
│   ├── repositories
│   │   └── caseRepository.py
│   │
│   ├── database
│   │   └── db.py
│   │
│   ├── keyboards
│   │   ├── adminKeyboard.py
│   │   ├── deleteKeyboard.py
│   │   └── sendKeyboard.py
│   │
│   ├── messages
│   │   ├── messageMap.py
│   │   └── user.py
│   │
│   ├── states
│   │   ├── adminSendState.py
│   │   └── createClientState.py
│   │
│   ├── config.py
│   └── main.py
│
└── requirements.txt
```

---

# ⚙️ Tech Stack

| Technology | Purpose |
|------------|--------|
| Python | Main programming language |
| Aiogram | Telegram bot framework |
| SQLite | Database |
| AsyncIO | Asynchronous operations |
| FSM | User interaction flows |

---

# 🚀 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/LicenseBot.git
cd LicenseBot
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Bot

Open:

```
app/config.py
```

Add your Telegram bot token and admin IDs.

Example:

```python
BOT_TOKEN = "your_bot_token"

ADMINS = [
    123456789
]
```

---

## 5️⃣ Run the Bot

```bash
python app/main.py
```

Bot should now be running.

---

# 🧩 Example Workflow

### Create Client

Admin command:

```
/create_client
```

Bot asks for:

```
Full name
US State
```

Client is saved in database.

---

### Send Workflow Message

Admin command:

```
/send
```

Flow:

```
Choose state
Choose message type
Choose client
```

Bot sends predefined template automatically.

---

# 🗂 Message Templates

Templates are stored in:

```
app/messages/user.py
```

Example template:

```python
PAYMENT = """
Отправляю вам данные для оплаты по Zelle.

Оплата первого платежа {amount}$

Вместо номера телефона вводите yulia87andreeva@gmail.com

Бизнес название Andreev life LLC

После оплаты пришлите скриншот
"""
```

Dynamic placeholders:

```
{amount}
{file_number}
{name}
```

---

# 🧑‍💻 Admin Commands

| Command | Description |
|-------|-------------|
| `/admin` | Open admin panel |
| `/send` | Send workflow message |
| `/create_client` | Create client |
| `/delete_client` | Delete client |

---

# ☁️ Deployment

The bot can run on any server:

- Oracle Cloud Free Tier
- Railway
- AWS
- DigitalOcean
- VPS

Example background run:

```bash
nohup python app/main.py &
```

Production deployments should use:

- `systemd`
- `Docker`
- `PM2`

---

# 🔒 Security Recommendations

For production environments:

- Use `.env` for secrets
- Restrict admin access
- Enable logging
- Switch SQLite to PostgreSQL
- Add error monitoring

---

# 📈 Future Improvements

Planned features:

- Web admin dashboard
- Client portal
- Message scheduling
- Payment integrations
- CRM functionality
- Analytics dashboard

---

# 📜 License

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

# 👨‍💻 Author

Developed by **Ivan Makovetskyi**
