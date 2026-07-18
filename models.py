from sqlalchemy import (
    Column, Integer, String, DECIMAL, Date, Time, ForeignKey, DateTime, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    # role: "user" (traveller), "provider" (mini-bus/car owner), "admin"
    role = Column(String, default="user", nullable=False)
    is_approved_provider = Column(Boolean, default=False)  # providers need admin sign-off
    created_at = Column(DateTime, server_default=func.now())


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    token = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    operator_name = Column(String, default="RailYatra Express")
    bus_type = Column(String, default="AC Sleeper")  # AC Sleeper / AC Seater / Non-AC / Volvo Multi-Axle
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_time = Column(Time, nullable=False)
    arrival_time = Column(Time, nullable=True)
    distance_km = Column(Integer, default=0)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    rating = Column(DECIMAL(2, 1), default=4.2)


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    passenger_name = Column(String)
    passenger_email = Column(String)
    passenger_phone = Column(String)
    final_price = Column(DECIMAL(10, 2))
    status = Column(String, default="ACTIVE")
    qr_payload = Column(String)
    booked_at = Column(DateTime, server_default=func.now())


class Vehicle(Base):
    """Tourist mini-buses & self-driving cars listed by providers for hire."""
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # "mini_bus" or "self_driving_car"
    name = Column(String, nullable=False)
    base_city = Column(String, nullable=False)
    seats = Column(Integer, nullable=False)
    price_per_km = Column(DECIMAL(6, 2), nullable=False)
    price_per_day_local = Column(DECIMAL(8, 2), nullable=False)  # 80km/8hr package
    driver_allowance_per_day = Column(DECIMAL(6, 2), default=0)  # 0 for self-driving cars
    description = Column(String, default="")
    emoji = Column(String, default="🚐")
    status = Column(String, default="pending")  # pending / approved / rejected
    created_at = Column(DateTime, server_default=func.now())


class VehicleBooking(Base):
    __tablename__ = "vehicle_bookings"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    trip_type = Column(String, nullable=False)  # "local" or "outstation"
    pickup_city = Column(String, nullable=False)
    drop_city = Column(String, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    distance_km = Column(Integer, default=0)
    days = Column(Integer, default=1)
    base_fare = Column(DECIMAL(10, 2))
    driver_charges = Column(DECIMAL(10, 2))
    gst = Column(DECIMAL(10, 2))
    total_price = Column(DECIMAL(10, 2))
    status = Column(String, default="CONFIRMED")
    created_at = Column(DateTime, server_default=func.now())