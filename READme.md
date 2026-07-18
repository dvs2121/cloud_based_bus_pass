# NexRoute — Futuristic Indian Transit & Ride-Hire Network

A cloud-native travel platform for India: search & book intercity bus tickets,
and hire tourist mini-buses or self-driving cars, priced with standard Indian
outstation-taxi conventions. Includes full traveller auth and a separate
Provider / Admin operator console.

## What's new in this rebuild

- **Futuristic UI** — dark "control tower" theme, animated transit-grid
  background, split-flap bus results board, and a perforated boarding-pass
  style digital ticket.
- **Vehicle hire marketplace** — book a tourist mini-bus or a self-driving
  car for **local** (80km/8hr package) or **outstation** (round-trip km,
  ₹250 km/day minimum convention, driver allowance, 5% GST) trips.
- **Indian city network** — 29 major Indian cities with a curated corridor
  map (Delhi–Agra, Mumbai–Goa, Bengaluru–Chennai, Chandigarh–Manali, etc.)
  used for both bus routes and hire-distance pricing.
- **Accounts** — traveller registration/login, and a **Provider** account
  type for vehicle owners who want to list mini-buses/cars.
- **Provider / Admin portal** (`/admin`) — providers list vehicles for
  approval and see their bookings; admins approve/reject listings, publish
  new bus routes, and see network-wide stats.
- **Developer popup** — a floating button in the traveller app opens a card
  with the developer's portfolio and contact details.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy
- **Auth**: PBKDF2 password hashing + bearer session tokens (no external
  auth service required)
- **Database**: PostgreSQL (Docker/Cloud), SQLite (local dev, default)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Fetch API) — no build step
- **Infrastructure**: Docker, Docker Compose

## Local Setup (Docker)
```bash
docker-compose up --build
# in a second terminal, seed demo data (buses, hire fleet, demo accounts):
docker-compose exec app python seed.py
```
Visit `http://localhost:8000` for the traveller app and
`http://localhost:8000/admin` for the operator console.

## Local Setup (without Docker)
```bash
pip install -r requirements.txt
python seed.py          # creates local_dev.db and demo data
uvicorn main:app --reload
```

## Demo accounts (created by seed.py)
| Role     
| Admin 
| Provider   
| Traveller

## Hire pricing model
- **Local**: flat per-day package covering 80 km / 8 hours, plus driver
  allowance for mini-buses (self-driving cars carry no driver charge).
- **Outstation**: billed km = max(round-trip distance, 250 km × days) at the
  vehicle's per-km rate, plus driver allowance per day, plus 5% GST — the
  standard convention used by Indian outstation taxi operators.

## Project structure
```
main.py          FastAPI app: auth, bus search/booking, hire quotes/booking, admin & provider APIs
models.py        SQLAlchemy models (User, AuthToken, Bus, Ticket, Vehicle, VehicleBooking)
india_data.py     City list, route/distance matrix, hire pricing calculator
seed.py          Demo data: routes, fleet, accounts
index.html/js     Traveller-facing app
admin.html/js     Provider / Admin console
style.css         Shared design system
schema.sql        Postgres schema (used by docker-entrypoint-initdb.d)
```

## Developer
Built by **Devesh Pratap** — ML Engineer / Power BI Developer / Cloud
Computing Engineer. Portfolio: https://deveshpratap.vercel.app