import os
import hashlib
import hmac
import secrets
from datetime import datetime, time, date
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr

from models import Base, User, AuthToken, Bus, Ticket, Vehicle, VehicleBooking
from india_data import (
    CITIES, BUS_ROUTES, get_distance, estimate_distance, calculate_hire_price,
)

# --- PATH CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NexRoute — Futuristic Indian Transit Network")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Password hashing (PBKDF2 — no extra native deps needed for the container)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest_hex = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
        return hmac.compare_digest(check.hex(), digest_hex)
    except Exception:
        return False


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    row = db.query(AuthToken).filter(AuthToken.token == token).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


def require_role(*roles):
    def dep(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You don't have access to this area")
        return user
    return dep


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: str = "user"  # "user" or "provider"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BookingRequest(BaseModel):
    passenger_name: str
    passenger_email: EmailStr
    passenger_phone: str
    bus_id: int


class TicketResponse(BaseModel):
    ticket_id: str
    route: str
    price: float
    status: str


class VehicleCreateRequest(BaseModel):
    type: str  # mini_bus / self_driving_car
    name: str
    base_city: str
    seats: int
    price_per_km: float
    price_per_day_local: float
    driver_allowance_per_day: float = 0
    description: str = ""
    emoji: str = "🚐"


class QuoteRequest(BaseModel):
    vehicle_id: int
    trip_type: str  # local / outstation
    pickup_city: str
    drop_city: Optional[str] = None
    days: int = 1


class HireBookingRequest(BaseModel):
    vehicle_id: int
    trip_type: str
    pickup_city: str
    drop_city: Optional[str] = None
    start_date: date
    end_date: date


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
@app.get("/")
def serve_frontend():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/admin")
def serve_admin():
    return FileResponse(BASE_DIR / "admin.html")


@app.get("/api/cities")
def list_cities():
    return {"cities": CITIES, "routes": [{"source": s, "destination": d} for s, d in BUS_ROUTES]}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role not in ("user", "provider"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'provider'")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_approved_provider=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthToken(user_id=user.id)
    db.add(token)
    db.commit()

    return {
        "token": token.token,
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    }


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = AuthToken(user_id=user.id)
    db.add(token)
    db.commit()

    return {
        "token": token.token,
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    }


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        db.query(AuthToken).filter(AuthToken.token == token).delete()
        db.commit()
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "is_approved_provider": user.is_approved_provider}


# ---------------------------------------------------------------------------
# Bus search & booking
# ---------------------------------------------------------------------------
@app.get("/api/search")
def search_buses(
    source: str = Query(...),
    destination: str = Query(...),
    date: str = Query(...),
    time_period: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        travel_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    query = db.query(Bus).filter(
        and_(
            Bus.source == source,
            Bus.destination == destination,
            Bus.departure_date == travel_date,
            Bus.available_seats > 0,
        )
    )

    if time_period:
        if time_period == "morning":
            query = query.filter(Bus.departure_time >= time(6, 0), Bus.departure_time < time(12, 0))
        elif time_period == "afternoon":
            query = query.filter(Bus.departure_time >= time(12, 0), Bus.departure_time < time(18, 0))
        elif time_period == "evening":
            query = query.filter(Bus.departure_time >= time(18, 0), Bus.departure_time < time(23, 59))

    return query.order_by(Bus.departure_time).all()


@app.get("/api/buses")
def get_buses(db: Session = Depends(get_db)):
    return db.query(Bus).all()


@app.post("/api/book", response_model=TicketResponse)
def book_ticket(booking: BookingRequest, db: Session = Depends(get_db),
                 authorization: Optional[str] = Header(None)):
    bus = db.query(Bus).filter(Bus.id == booking.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    if bus.available_seats <= 0:
        raise HTTPException(status_code=400, detail="No seats available")

    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        row = db.query(AuthToken).filter(AuthToken.token == token).first()
        if row:
            user_id = row.user_id

    final_price = float(bus.base_price)

    ticket = Ticket(
        user_id=user_id,
        bus_id=bus.id,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        passenger_phone=booking.passenger_phone,
        final_price=final_price,
        qr_payload=f"NEXROUTE:{bus.source}-{bus.destination}:{booking.passenger_email}",
    )

    bus.available_seats -= 1

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketResponse(
        ticket_id=ticket.id,
        route=f"{bus.source} → {bus.destination}",
        price=final_price,
        status=ticket.status,
    )


@app.get("/api/verify/{ticket_id}")
def verify_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid Ticket")
    return {"ticket_id": ticket.id, "status": ticket.status, "valid": ticket.status == "ACTIVE"}


# ---------------------------------------------------------------------------
# Vehicle hire — mini buses & self-driving cars
# ---------------------------------------------------------------------------
@app.get("/api/vehicles")
def list_vehicles(type: Optional[str] = None, city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Vehicle).filter(Vehicle.status == "approved")
    if type:
        query = query.filter(Vehicle.type == type)
    if city:
        query = query.filter(Vehicle.base_city == city)
    return query.all()


@app.post("/api/vehicles/quote")
def quote_vehicle(payload: QuoteRequest, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id, Vehicle.status == "approved").first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    distance_km = 0
    if payload.trip_type == "outstation":
        if not payload.drop_city:
            raise HTTPException(status_code=400, detail="Drop city is required for outstation trips")
        distance_km = estimate_distance(payload.pickup_city, payload.drop_city)

    breakdown = calculate_hire_price(
        vehicle.price_per_km, vehicle.price_per_day_local, vehicle.driver_allowance_per_day,
        payload.trip_type, distance_km, payload.days,
    )
    breakdown["distance_km"] = distance_km
    breakdown["vehicle"] = {
        "id": vehicle.id, "name": vehicle.name, "type": vehicle.type,
        "emoji": vehicle.emoji, "seats": vehicle.seats,
    }
    return breakdown


@app.post("/api/vehicle-bookings")
def create_vehicle_booking(payload: HireBookingRequest, db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id, Vehicle.status == "approved").first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    days = max(1, (payload.end_date - payload.start_date).days + 1)
    distance_km = 0
    if payload.trip_type == "outstation":
        if not payload.drop_city:
            raise HTTPException(status_code=400, detail="Drop city is required for outstation trips")
        distance_km = estimate_distance(payload.pickup_city, payload.drop_city)

    breakdown = calculate_hire_price(
        vehicle.price_per_km, vehicle.price_per_day_local, vehicle.driver_allowance_per_day,
        payload.trip_type, distance_km, days,
    )

    booking = VehicleBooking(
        user_id=user.id,
        vehicle_id=vehicle.id,
        trip_type=payload.trip_type,
        pickup_city=payload.pickup_city,
        drop_city=payload.drop_city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        distance_km=distance_km,
        days=days,
        base_fare=breakdown["base_fare"],
        driver_charges=breakdown["driver_charges"],
        gst=breakdown["gst"],
        total_price=breakdown["total_price"],
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "booking_id": booking.id,
        "vehicle": vehicle.name,
        "route": f"{payload.pickup_city} → {payload.drop_city}" if payload.drop_city else payload.pickup_city,
        "total_price": float(booking.total_price),
        "status": booking.status,
    }


@app.get("/api/vehicle-bookings/mine")
def my_hire_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(VehicleBooking).filter(VehicleBooking.user_id == user.id).all()


# ---------------------------------------------------------------------------
# Provider portal
# ---------------------------------------------------------------------------
@app.post("/api/provider/vehicles")
def provider_add_vehicle(payload: VehicleCreateRequest, db: Session = Depends(get_db),
                          user: User = Depends(require_role("provider", "admin"))):
    if payload.type not in ("mini_bus", "self_driving_car"):
        raise HTTPException(status_code=400, detail="type must be 'mini_bus' or 'self_driving_car'")
    if payload.base_city not in CITIES:
        raise HTTPException(status_code=400, detail="Unrecognized city")

    vehicle = Vehicle(
        provider_id=user.id,
        type=payload.type,
        name=payload.name,
        base_city=payload.base_city,
        seats=payload.seats,
        price_per_km=payload.price_per_km,
        price_per_day_local=payload.price_per_day_local,
        driver_allowance_per_day=payload.driver_allowance_per_day,
        description=payload.description,
        emoji=payload.emoji,
        status="pending",
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.get("/api/provider/vehicles/mine")
def provider_my_vehicles(db: Session = Depends(get_db), user: User = Depends(require_role("provider", "admin"))):
    return db.query(Vehicle).filter(Vehicle.provider_id == user.id).all()


@app.get("/api/provider/bookings")
def provider_bookings(db: Session = Depends(get_db), user: User = Depends(require_role("provider", "admin"))):
    vehicle_ids = [v.id for v in db.query(Vehicle).filter(Vehicle.provider_id == user.id).all()]
    if not vehicle_ids:
        return []
    return db.query(VehicleBooking).filter(VehicleBooking.vehicle_id.in_(vehicle_ids)).all()


# ---------------------------------------------------------------------------
# Admin portal
# ---------------------------------------------------------------------------
@app.get("/api/admin/stats")
def admin_stats(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return {
        "total_users": db.query(User).filter(User.role == "user").count(),
        "total_providers": db.query(User).filter(User.role == "provider").count(),
        "total_bus_tickets": db.query(Ticket).count(),
        "total_hire_bookings": db.query(VehicleBooking).count(),
        "pending_vehicles": db.query(Vehicle).filter(Vehicle.status == "pending").count(),
        "approved_vehicles": db.query(Vehicle).filter(Vehicle.status == "approved").count(),
        "total_buses": db.query(Bus).count(),
    }


@app.get("/api/admin/vehicles")
def admin_list_vehicles(status: Optional[str] = None, db: Session = Depends(get_db),
                         user: User = Depends(require_role("admin"))):
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status)
    return query.all()


@app.post("/api/admin/vehicles/{vehicle_id}/approve")
def admin_approve_vehicle(vehicle_id: int, db: Session = Depends(get_db),
                           user: User = Depends(require_role("admin"))):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.status = "approved"
    db.commit()
    return {"ok": True}


@app.post("/api/admin/vehicles/{vehicle_id}/reject")
def admin_reject_vehicle(vehicle_id: int, db: Session = Depends(get_db),
                          user: User = Depends(require_role("admin"))):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.status = "rejected"
    db.commit()
    return {"ok": True}


@app.get("/api/admin/bookings")
def admin_bookings(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return {
        "bus_tickets": db.query(Ticket).order_by(Ticket.booked_at.desc()).limit(100).all(),
        "hire_bookings": db.query(VehicleBooking).order_by(VehicleBooking.created_at.desc()).limit(100).all(),
    }


class BusCreateRequest(BaseModel):
    operator_name: str = "RailYatra Express"
    bus_type: str = "AC Sleeper"
    source: str
    destination: str
    departure_date: date
    departure_time: str  # HH:MM
    base_price: float
    total_seats: int


@app.post("/api/admin/buses")
def admin_create_bus(payload: BusCreateRequest, db: Session = Depends(get_db),
                      user: User = Depends(require_role("admin"))):
    if payload.source not in CITIES or payload.destination not in CITIES:
        raise HTTPException(status_code=400, detail="Unrecognized city")
    hh, mm = [int(x) for x in payload.departure_time.split(":")]
    dist = get_distance(payload.source, payload.destination) or estimate_distance(payload.source, payload.destination)
    bus = Bus(
        operator_name=payload.operator_name,
        bus_type=payload.bus_type,
        source=payload.source,
        destination=payload.destination,
        departure_date=payload.departure_date,
        departure_time=time(hh, mm),
        distance_km=dist,
        base_price=payload.base_price,
        total_seats=payload.total_seats,
        available_seats=payload.total_seats,
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")