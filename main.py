from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from models import Base, User, Bus, Ticket
from datetime import datetime, time
import os
from pathlib import Path

# --- PATH CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cloud Bus Pass System")

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

class BookingRequest(BaseModel):
    user_name: str
    user_email: str
    user_phone: str
    bus_id: int

class TicketResponse(BaseModel):
    ticket_id: str
    route: str
    price: float
    status: str

@app.get("/")
def serve_frontend():
    return FileResponse(BASE_DIR / "index.html")

# NEW: Search endpoint with filters
@app.get("/api/search")
def search_buses(
    source: str = Query(...),
    destination: str = Query(...),
    date: str = Query(...),
    time_period: str = Query(None),
    db: Session = Depends(get_db)
):
    # Parse date
    try:
        travel_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Base query
    query = db.query(Bus).filter(
        and_(
            Bus.source == source,
            Bus.destination == destination,
            Bus.departure_date == travel_date,
            Bus.available_seats > 0
        )
    )
    
    # Filter by time period if specified
    if time_period:
        if time_period == "morning":
            query = query.filter(Bus.departure_time >= time(6, 0), Bus.departure_time < time(12, 0))
        elif time_period == "afternoon":
            query = query.filter(Bus.departure_time >= time(12, 0), Bus.departure_time < time(18, 0))
        elif time_period == "evening":
            query = query.filter(Bus.departure_time >= time(18, 0), Bus.departure_time < time(23, 59))
    
    buses = query.all()
    return buses

@app.get("/api/buses")
def get_buses(db: Session = Depends(get_db)):
    return db.query(Bus).all()

@app.post("/api/book", response_model=TicketResponse)
def book_ticket(booking: BookingRequest, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == booking.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    if bus.available_seats <= 0:
        raise HTTPException(status_code=400, detail="No seats available")

    final_price = float(bus.base_price)

    user = db.query(User).filter(User.email == booking.user_email).first()
    if not user:
        user = User(name=booking.user_name, email=booking.user_email, phone=booking.user_phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    ticket = Ticket(
        user_id=user.id,
        bus_id=bus.id,
        final_price=final_price,
        qr_payload=f"BUS_PASS:{bus.source}-{bus.destination}:{user.email}"
    )
    
    bus.available_seats -= 1
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketResponse(
        ticket_id=ticket.id,
        route=f"{bus.source} → {bus.destination}",
        price=final_price,
        status=ticket.status
    )

@app.get("/api/verify/{ticket_id}")
def verify_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid Ticket")
    return {"ticket_id": ticket.id, "status": ticket.status, "valid": ticket.status == "ACTIVE"}

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")