from main import engine, SessionLocal
from models import Base, Bus
from datetime import date, time

Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.query(Bus).delete()
db.commit()

routes = [
    Bus(source="New York", destination="Boston", departure_date=date(2026, 7, 5), departure_time=time(8, 30), base_price=45.00, total_seats=40, available_seats=40),
    Bus(source="New York", destination="Boston", departure_date=date(2026, 7, 5), departure_time=time(14, 0), base_price=45.00, total_seats=40, available_seats=40),
    Bus(source="Los Angeles", destination="San Francisco", departure_date=date(2026, 7, 6), departure_time=time(9, 0), base_price=60.00, total_seats=35, available_seats=35),
    Bus(source="Los Angeles", destination="San Francisco", departure_date=date(2026, 7, 6), departure_time=time(18, 30), base_price=60.00, total_seats=35, available_seats=35),
    Bus(source="Chicago", destination="Detroit", departure_date=date(2026, 7, 7), departure_time=time(10, 15), base_price=35.50, total_seats=50, available_seats=50),
    Bus(source="Miami", destination="Orlando", departure_date=date(2026, 7, 8), departure_time=time(11, 45), base_price=40.00, total_seats=45, available_seats=45),
    Bus(source="Seattle", destination="Chicago", departure_date=date(2026, 7, 9), departure_time=time(7, 0), base_price=85.00, total_seats=30, available_seats=30),
    Bus(source="Boston", destination="New York", departure_date=date(2026, 7, 10), departure_time=time(16, 0), base_price=45.00, total_seats=40, available_seats=40),
]

db.add_all(routes)
db.commit()
db.close()

print("✅ Database seeded successfully!")