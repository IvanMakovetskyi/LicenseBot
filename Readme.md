# LicenseBot

Telegram automation bot (Aiogram) for admin-managed client workflows.

## Stack
- Python 3.10+
- Aiogram 3
- Neon PostgreSQL (remote)
- asyncpg

## 1. Install
```bash
git clone https://github.com/yourusername/LicenseBot.git
cd LicenseBot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows activation:
```bash
venv\Scripts\activate
```

## 2. Environment
Copy `.env.example` to `.env` (or keep `app/.env` if that is your deployment pattern) and set:

```env
BOT_TOKEN=your_telegram_bot_token
ADMINS=123456789,987654321
DATABASE_URL=postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
APP_ENV=prod
```

Notes:
- `BOT_TOKEN` is preferred, `TOKEN` is still accepted for backward compatibility.
- Startup fails with a clear error if `DATABASE_URL` or other required vars are missing.

## 3. Create Neon Database
1. Create a project in [Neon](https://neon.tech).
2. Create or select a database.
3. Copy the connection string from Neon dashboard.
4. Put it into `DATABASE_URL` in `.env` (keep `sslmode=require`).

## 4. Initialize and Verify Neon Connection
Run:

```bash
python scripts/test_neon_connection.py
```

This script verifies:
- Neon connection works
- required table exists (`clients`)
- insert/read/update/delete flow works

## 5. Migrate Existing SQLite Data (Optional, one-time)
If `data/clients.db` exists:

```bash
python scripts/migrate_sqlite_to_neon.py
```

Behavior:
- Reads all rows from SQLite `cases`
- Inserts into Neon `clients`
- Skips duplicates by `chat_id`
- Prints migrated/skipped counters

It does not delete local SQLite files and is not auto-run by the bot.

## 6. Run Bot
```bash
python app/main.py
```

At startup, bot runs idempotent DB init (`CREATE TABLE IF NOT EXISTS`) and keeps existing Neon data.
It also seeds message templates/flows into DB if missing and then uses DB templates at runtime.

## 7. Deployment (Oracle Ubuntu / VPS)
Recommended:
- Store secrets in environment or `.env`
- Run with `systemd` or Docker
- Keep outbound access to Neon endpoint (TLS)

Example background run:
```bash
nohup python app/main.py > bot.log 2>&1 &
```
