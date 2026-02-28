# MT5 Bonus Plugin

Broker-side bonus campaign management system for MetaTrader 5. Create and manage promotional bonus campaigns, assign bonuses automatically via triggers, and monitor everything through a web admin dashboard.

## Features

### Three Bonus Types
- **Type A - Dynamic Leverage**: Credit posted + leverage reduced proportionally. Formula: `floor(original_leverage / ((bonus% / 100) + 1))`. Leverage restored on removal.
- **Type B - Fixed Leverage**: Credit posted, leverage unchanged. Simple credit add/remove.
- **Type C - Convertible**: Non-withdrawable credit converts to real balance as the client trades. Linear conversion per lot. Withdrawal cancels unconverted credit.

### Automatic Account Monitoring
The system continuously monitors all MT5 accounts in real-time (every 0.3 seconds):

- **Auto-Discovery**: New MT5 accounts are automatically detected and registered for monitoring. No manual setup needed.
- **Deposit Detection**: Balance increases are detected via snapshot comparison and confirmed through MT5 deal history. Matching `auto_deposit` campaigns automatically assign bonuses.
- **Withdrawal Detection**: Balance decreases trigger **proportional** credit reduction. E.g., withdrawing 10% of balance removes 10% of credit. Type A leverage is recalculated to match the new credit/balance ratio. Full withdrawal cancels everything.
- **Drawdown Protection**: When a trader's equity drops to or below their credit (meaning they've lost all their own funds), the system automatically:
  1. Closes all open positions
  2. Cancels all active bonuses
  3. Removes all credit (with retry logic for MT5 settlement)
- **Type C Trade Tracking**: Trades are automatically fetched and processed for convertible bonus lot requirements.
- **Error Resilience**: Accounts with 5+ consecutive errors are paused. Admins can reset them via the API.

### Campaign Management
- Create campaigns with configurable bonus type, percentage, deposit thresholds, expiry, and targeting rules
- Campaign lifecycle: Draft -> Active -> Paused -> Ended -> Archived
- Target by MT5 group, country, deposit range
- One-per-account and max concurrent bonus limits
- **Scan MT5** button to refresh available groups and countries from the live MT5 server

### Trigger System
- **Auto on Deposit**: Fires automatically when a qualifying deposit is detected by the monitor
- **Promo Code**: Validated against active campaigns
- **On Registration**: Fires when a new MT5 account is created
- **Agent/Group Code**: IB agent codes trigger bonuses for referred clients. The MT5 **Lead Source** field is read automatically from the account — if it matches a campaign's agent codes, the bonus is assigned on deposit. Campaigns with agent codes only fire when Lead Source matches (no match = no bonus).

### Admin Dashboard
- **Dashboard**: Overview stats (active campaigns, bonuses, conversions)
- **Campaign Manager**: List, create, edit, duplicate, archive campaigns
- **Bonus Monitor**: Real-time view of all bonuses with cancel/force-convert actions. Manual assign with **eligibility override** — group/country/trigger mismatches show a confirmation dialog instead of blocking.
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

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler
- **Frontend**: React 19, TypeScript, Ant Design 6, Vite
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Auth**: JWT with refresh tokens, bcrypt password hashing
- **MT5 Gateway**: Pluggable interface — mock gateway for development, real MT5 Manager REST API bridge for production

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

By default, the backend starts in **mock mode** with 10 simulated MT5 accounts. To connect to a real MT5 server, see [Production Setup](#production-setup).

### Frontend

```bash
cd frontend
npm install
npm run dev           # Starts on http://localhost:5174
```

### Default Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@mt5bonus.com | admin123 | Super Admin |
| manager@mt5bonus.com | manager123 | Campaign Manager |
| support@mt5bonus.com | support123 | Support Agent |
| viewer@mt5bonus.com | viewer123 | Read-Only |

### Mock MT5 Accounts

10 test accounts are pre-loaded (logins 10001-10010) with varying balances, leverage, and groups. View them at `GET /api/gateway/accounts`.

## Production Setup

### Connecting to a Real MT5 Server

The plugin connects to MT5 via a **Manager REST API bridge** (mtapi-style HTTP wrapper around the MT5 Manager API). Set the following environment variables in `backend/.env`:

```bash
# MT5 Manager REST API Bridge
MT5_BRIDGE_URL=http://your-bridge-server:5000
MT5_SERVER=your-mt5-server-ip
MT5_MANAGER_LOGIN=your-manager-login
MT5_MANAGER_PASSWORD=your-manager-password
MT5_REQUEST_TIMEOUT_SECONDS=30
```

When these are set, the backend automatically uses the real gateway instead of the mock. The gateway includes:
- **Auto-reconnect**: If the MT5 token expires or is invalidated, the gateway automatically reconnects and retries the request.
- **Error handling**: All MT5 API errors are caught and logged without crashing the monitor.

### PostgreSQL (Recommended for Production)

```bash
# docker-compose.yml included for PostgreSQL
docker compose up -d

# Update backend/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mt5_bonus
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./mt5_bonus.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-key-not-for-production` | JWT signing key (change in production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token lifetime |
| `CORS_ORIGINS` | `["http://localhost:5174"]` | Allowed CORS origins |
| `MT5_BRIDGE_URL` | (empty) | MT5 Manager REST API bridge URL |
| `MT5_SERVER` | (empty) | MT5 server IP address |
| `MT5_MANAGER_LOGIN` | (empty) | MT5 Manager login |
| `MT5_MANAGER_PASSWORD` | (empty) | MT5 Manager password |
| `MT5_REQUEST_TIMEOUT_SECONDS` | `30` | MT5 API request timeout |

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
- `POST /api/bonuses/check-eligibility` — Check eligibility (returns all failures with overridable flag)
- `POST /api/bonuses/assign` — Manual assign (supports `override_eligibility: true` to bypass overridable checks)
- `POST /api/bonuses/{id}/cancel` — Cancel bonus
- `POST /api/bonuses/{id}/force-convert` — Force convert (Type C)
- `POST /api/bonuses/{id}/override-leverage` — Override leverage (Type A)

### Triggers
- `POST /api/triggers/deposit` — Deposit event
- `POST /api/triggers/registration` — Registration event
- `POST /api/triggers/promo-code` — Promo code redemption

### Accounts
- `GET /api/accounts/mt5-metadata` — All MT5 groups, countries, and accounts for form dropdowns
- `GET /api/accounts/{login}` — Account lookup with bonus history and audit logs

### Monitoring
- `GET /api/monitoring/status` — System health (active/errored account counts, scheduler status)
- `GET /api/monitoring/accounts` — List all monitored accounts with snapshots
- `POST /api/monitoring/accounts/{login}/register` — Manually register an account for deposit monitoring
- `POST /api/monitoring/accounts/{login}/reset-errors` — Reset error counter for a stuck account
- `POST /api/monitoring/accounts/{login}/test-deposit` — Test deposit (triggers auto-detection)
- `POST /api/monitoring/accounts/{login}/test-withdraw` — Test withdrawal (triggers auto-detection)

### Reports & Audit
- `GET /api/reports/summary` — Bonus summary by campaign
- `GET /api/reports/conversions` — Type C conversion progress
- `GET /api/reports/cancellations` — Cancellation breakdown
- `GET /api/reports/leverage` — Leverage adjustment report
- `GET /api/reports/export` — CSV/Excel export
- `GET /api/audit` — Audit log query

## Background Jobs

The backend runs two background jobs via APScheduler:

| Job | Interval | Description |
|-----|----------|-------------|
| `account_monitor` | 0.3s | Polls all active MT5 accounts for deposits, withdrawals, drawdown, and trades |
| `expiry_checker` | 1 hour | Cancels bonuses that have exceeded their expiry date |

Both jobs are coalesced (`max_instances=1`) to prevent overlap if a cycle takes longer than the interval.

## Manual Bonus Assignment & Eligibility Override

Admins can manually assign bonuses from the **Bonus Monitor** page. When eligibility checks fail, the system supports overriding certain checks with a confirmation dialog.

### How It Works

1. **Admin opens Assign Bonus** modal, selects an MT5 account and campaign.
2. Backend runs all eligibility checks via `check_eligibility_all()` and returns every failure (not just the first).
3. Each failure is classified as **overridable** or **non-overridable**:

| Check | Overridable | Description |
|-------|-------------|-------------|
| `campaign_status` | No | Campaign is not active |
| `campaign_ended` | No | Campaign has passed its end date |
| `account_not_found` | No | MT5 account does not exist |
| `group_mismatch` | Yes | Account group not in campaign target groups |
| `country_mismatch` | Yes | Account country not in campaign target countries |
| `deposit_below_min` | Yes | Deposit below campaign minimum |
| `deposit_above_max` | Yes | Deposit above campaign maximum |
| `duplicate_bonus` | Yes | Account already received this campaign bonus |
| `max_concurrent` | Yes | Account has max concurrent active bonuses |

4. If there are only **overridable** failures, the frontend shows a red confirmation dialog listing all mismatches. Admin can click **"Override & Assign"** to proceed anyway.
5. If there are any **non-overridable** failures, the assignment is blocked completely.
6. When overriding, the backend re-sends the request with `override_eligibility: true`, which skips overridable checks but still enforces non-overridable ones.

### API Flow

- `POST /api/bonuses/assign` with `override_eligibility: false` (default) -- returns HTTP 409 with all failures if ineligible
- `POST /api/bonuses/assign` with `override_eligibility: true` -- skips overridable checks, blocks on non-overridable ones
- `POST /api/bonuses/check-eligibility` -- standalone check that returns all failures without assigning

### Key Files

- `backend/app/services/bonus_engine.py` -- `check_eligibility_all()` returns all failures with overridable flag
- `backend/app/api/bonuses.py` -- `/assign` endpoint with 409 override flow
- `backend/app/schemas/bonus.py` -- `BonusAssign` schema with `override_eligibility` field
- `frontend/src/pages/bonuses/BonusMonitor.tsx` -- `handleAssign()` with confirmation dialog

## How Auto-Deposit Bonus Works

1. **Campaign setup**: Create a campaign with trigger type "Auto on Deposit", set the bonus percentage, target groups/countries, and deposit thresholds.
2. **Account discovery**: The monitor automatically discovers all MT5 accounts and registers them for polling.
3. **Deposit detection**: Every 0.3s, the monitor compares each account's current balance against its stored snapshot. If balance increased (and credit didn't), it's a deposit.
4. **Deal confirmation**: The system fetches balance deal history from MT5 to get exact deposit amounts.
5. **Agent code matching**: The account's MT5 Lead Source field is read. If it matches a campaign's agent codes, that campaign is also triggered alongside any `auto_deposit` campaigns. Campaigns with agent codes configured will only fire when the Lead Source matches.
6. **Bonus assignment**: For each matching campaign, `process_deposit_trigger` checks eligibility rules (group, country, amount range). If eligible, the bonus is assigned automatically.
6. **Credit posted**: The bonus credit is posted to the MT5 account via the Manager API, and the snapshot is updated.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints (auth, campaigns, bonuses, triggers, accounts, monitoring)
│   │   ├── config/       # Settings, JWT, security
│   │   ├── db/           # Database engine, base models
│   │   ├── gateway/      # MT5 Gateway interface + mock + real implementation
│   │   ├── models/       # SQLAlchemy models (bonus, campaign, user, audit_log, monitored_account)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (bonus engine, triggers, lot tracking, monitor)
│   │   ├── tasks/        # Background tasks (expiry checker, event processor, scheduler)
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
