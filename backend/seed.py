import os
from datetime import date, time, timedelta

from backend.main import engine, SessionLocal, hash_password
from backend.models import Base, Bus, User, Vehicle
from backend.india_data import BUS_ROUTES, get_distance

Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.query(Bus).delete()
db.query(Vehicle).delete()
db.query(User).delete()
db.commit()

# --- Local bootstrap accounts ------------------------------------------
admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")
provider_password = os.getenv("PROVIDER_PASSWORD")
seed_user_password = os.getenv("SEED_USER_PASSWORD")
if not all((admin_email, admin_password, provider_password, seed_user_password)):
                raise RuntimeError("ADMIN_EMAIL, ADMIN_PASSWORD, PROVIDER_PASSWORD, and SEED_USER_PASSWORD are required to seed")

admin = User(name="NexRoute Admin", email=admin_email, phone="9999900000",
                                                 password_hash=hash_password(admin_password), role="admin", is_approved_provider=True)
provider = User(name="Ganga Travels", email="provider@nexroute.in", phone="9999900001",
                                                                password_hash=hash_password(provider_password), role="provider", is_approved_provider=True)
traveller = User(name="Aarav Sharma", email="user@nexroute.in", phone="9999900002",
                                                                        password_hash=hash_password(seed_user_password), role="user")

db.add_all([admin, provider, traveller])
db.commit()
db.refresh(admin)
db.refresh(provider)
db.refresh(traveller)

# --- Bus routes across curated Indian corridors -------------------------
OPERATORS = ["RailYatra Express", "Shivshahi Volvo", "Ganga Travels", "IntrCity SmartBus", "Vayu Connect"]
BUS_TYPES = ["AC Sleeper", "AC Seater", "Non-AC Seater", "Volvo Multi-Axle"]
DEPARTURES = [time(6, 30), time(9, 0), time(13, 15), time(17, 45), time(21, 30), time(23, 0)]

base_date = date.today() + timedelta(days=2)
buses = []
for i, (source, destination) in enumerate(BUS_ROUTES):
    dist = get_distance(source, destination) or 300
    # 3 departures across the next few days for each corridor
    for d_offset in range(3):
        dep_time = DEPARTURES[(i + d_offset) % len(DEPARTURES)]
        price = round(dist * 1.35 + 150, -1)  # rough per-km fare + base
        buses.append(Bus(
            operator_name=OPERATORS[(i + d_offset) % len(OPERATORS)],
            bus_type=BUS_TYPES[(i + d_offset) % len(BUS_TYPES)],
            source=source,
            destination=destination,
            departure_date=base_date + timedelta(days=d_offset * 2),
            departure_time=dep_time,
            distance_km=dist,
            base_price=price,
            total_seats=40,
            available_seats=40 - ((i + d_offset) % 6) * 3,
            rating=round(3.8 + ((i + d_offset) % 12) * 0.1, 1),
        ))

db.add_all(buses)
db.commit()

# --- Demo hire fleet (mini buses & self-driving cars) --------------------
vehicles = [
    Vehicle(provider_id=provider.id, type="mini_bus", name="Tempo Traveller 17-Seater",
            base_city="New Delhi", seats=17, price_per_km=22, price_per_day_local=3500,
            driver_allowance_per_day=400, description="Ideal for group temple tours & family trips.",
            emoji="🚐", status="approved"),
    Vehicle(provider_id=provider.id, type="mini_bus", name="Force Urbania 12-Seater",
            base_city="Jaipur", seats=12, price_per_km=24, price_per_day_local=3800,
            driver_allowance_per_day=400, description="Comfortable AC mini-coach for Rajasthan circuits.",
            emoji="🚌", status="approved"),
    Vehicle(provider_id=provider.id, type="self_driving_car", name="Self-Drive Hyundai Creta",
            base_city="Mumbai", seats=5, price_per_km=11, price_per_day_local=2500,
            driver_allowance_per_day=0, description="Automatic SUV, unlimited local hours, full tank pickup.",
            emoji="🚗", status="approved"),
    Vehicle(provider_id=provider.id, type="self_driving_car", name="Self-Drive Maruti Swift",
            base_city="Bengaluru", seats=5, price_per_km=9, price_per_day_local=1900,
            driver_allowance_per_day=0, description="Fuel-efficient hatchback, GPS included.",
            emoji="🚗", status="approved"),
    Vehicle(provider_id=provider.id, type="mini_bus", name="Traveller 26-Seater Volvo Mini",
            base_city="Goa", seats=26, price_per_km=28, price_per_day_local=5200,
            driver_allowance_per_day=450, description="Beach-hopping coach with music system & recliners.",
            emoji="🚐", status="approved"),
    Vehicle(provider_id=provider.id, type="self_driving_car", name="Self-Drive Tata Nexon EV",
            base_city="New Delhi", seats=5, price_per_km=10, price_per_day_local=2800,
            driver_allowance_per_day=0, description="Electric SUV — zero emission outstation trips.",
            emoji="🔋", status="approved"),
    Vehicle(provider_id=provider.id, type="mini_bus", name="Tempo Traveller 14-Seater",
            base_city="Lucknow", seats=14, price_per_km=20, price_per_day_local=3200,
            driver_allowance_per_day=350, description="Popular for UP heritage circuits.",
            emoji="🚐", status="pending"),
]

db.add_all(vehicles)
db.commit()
db.close()

print("Seeded NexRoute: buses across", len(BUS_ROUTES), "Indian corridors,",
        len(vehicles), "hire vehicles, and bootstrap accounts.")
print("Admin email:", admin_email)