from sqlalchemy import Column, Integer, String, DECIMAL, Date, Time, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)
    destination = Column(String)
    departure_date = Column(Date)
    departure_time = Column(Time)
    base_price = Column(DECIMAL)
    total_seats = Column(Integer)
    available_seats = Column(Integer)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    user_id = Column(Integer, ForeignKey("users.id"))
    bus_id = Column(Integer, ForeignKey("buses.id"))
    final_price = Column(DECIMAL)
    status = Column(String, default="ACTIVE")
    qr_payload = Column(String)
    booked_at = Column(DateTime, server_default=func.now())