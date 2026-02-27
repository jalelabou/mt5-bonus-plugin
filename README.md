# MT5 Bonus Plugin

Broker-side bonus campaign management system for MetaTrader 5. Create and manage promotional bonus campaigns, assign bonuses automatically via triggers, and monitor everything through a web admin dashboard.

## Features

### Three Bonus Types
- **Type A - Dynamic Leverage**: Credit posted + leverage reduced proportionally. Formula: `floor(original_leverage / ((bonus% / 100) + 1))`. Leverage restored on removal.
- **Type B - Fixed Leverage**: Credit posted, leverage unchanged. Simple credit add/remove.
- **Type C - Convertible**: Non-withdrawable credit converts to real balance as the client trades. Linear conversion per lot. Withdrawal cancels unconverted credit.

### Campaign Management
- Create campaigns with configurable bonus type, percentage, deposit thresholds, expiry, and targeting rules
- Campaign lifecycle: Draft → Active → Paused → Ended → Archived
- Target by MT5 group, country, deposit range
- One-per-account and max concurrent bonus limits

### Trigger System
- **Auto on Deposit**: Fires when a qualifying deposit is detected
- **Promo Code**: Validated against active campaigns
- **On Registration**: Fires when a new MT5 account is created
- **Agent/Group Code**: IB agent codes trigger bonuses for referred clients

### Admin Dashboard
- **Dashboard**: Overview stats (active campaigns, bonuses, conversions)
- **Campaign Manager**: List, create, edit, duplicate, archive campaigns
- **Bonus Monitor**: Real-time view of all bonuses with cancel/force-convert actions
- **Account Lookup**: Search by MT5 login — view balance, equity, credit, leverage, bonus history, audit trail
- **Reports**: Summary, conversion progress, cancellations, leverage adjustments with CSV/Excel export
- **Audit Log**: Immutable log of all bonus events with before/after state

### Role-Based Access
| Role | Permissions |
|------|------------|
| Super Admin | Full access: campaigns, bonuses, reports, user management |
| Campaign Manager | Create/edit campaigns, view bonus monitor |
| Support Agent | Account lookup, read-only bonus view, manual assign |
| Read-Only | View campaigns, monitor, and reports only |

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- **Frontend**: React 19, TypeScript, Ant Design 6, Vite
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Auth**: JWT with refresh tokens, bcrypt password hashing

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+

### Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py        # Creates DB + test data
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev           # Starts on http://localhost:5173
```

### Default Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@mt5bonus.com | admin123 | Super Admin |
| manager@mt5bonus.com | manager123 | Campaign Manager |
| support@mt5bonus.com | support123 | Support Agent |
| viewer@mt5bonus.com | viewer123 | Read-Only |

### Mock MT5 Accounts

10 test accounts are pre-loaded (logins 10001–10010) with varying balances, leverage, and groups. View them at `GET /api/gateway/accounts`.

## Production Setup

For production, switch to PostgreSQL:

```bash
# docker-compose.yml included for PostgreSQL
docker compose up -d

# Update backend/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mt5_bonus
```

## API Endpoints

### Auth
- `POST /api/auth/login` — Login
- `POST /api/auth/refresh` — Refresh token
- `GET /api/auth/me` — Current user

### Campaigns
- `GET /api/campaigns` — List campaigns
- `POST /api/campaigns` — Create campaign
- `GET /api/campaigns/{id}` — Campaign detail
- `PUT /api/campaigns/{id}` — Update campaign
- `POST /api/campaigns/{id}/duplicate` — Duplicate campaign
- `PATCH /api/campaigns/{id}/status` — Change status

### Bonuses
- `GET /api/bonuses` — List bonuses
- `GET /api/bonuses/{id}` — Bonus detail with lot progress
- `POST /api/bonuses/assign` — Manual assign
- `POST /api/bonuses/{id}/cancel` — Cancel bonus
- `POST /api/bonuses/{id}/force-convert` — Force convert (Type C)
- `POST /api/bonuses/{id}/override-leverage` — Override leverage (Type A)

### Triggers
- `POST /api/triggers/deposit` — Deposit event
- `POST /api/triggers/registration` — Registration event
- `POST /api/triggers/promo-code` — Promo code redemption

### Reports & Audit
- `GET /api/reports/summary` — Bonus summary by campaign
- `GET /api/reports/conversions` — Type C conversion progress
- `GET /api/reports/cancellations` — Cancellation breakdown
- `GET /api/reports/leverage` — Leverage adjustment report
- `GET /api/reports/export` — CSV/Excel export
- `GET /api/audit` — Audit log query

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── config/       # Settings, JWT, security
│   │   ├── db/           # Database engine, base models
│   │   ├── gateway/      # MT5 Gateway interface + mock
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (bonus engine, triggers, lot tracking)
│   │   ├── tasks/        # Background tasks (expiry checker, event processor)
│   │   └── main.py       # FastAPI app entry point
│   ├── alembic/          # Database migrations
│   ├── seed.py           # Test data seeder
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/          # Axios client + endpoint functions
│       ├── components/   # Shared UI (AppLayout)
│       ├── context/      # Auth context
│       ├── pages/        # All dashboard pages
│       └── types/        # TypeScript interfaces
└── docker-compose.yml    # PostgreSQL for production
```

## License

Proprietary — Confidential.
