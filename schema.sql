CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',       -- user / provider / admin
    is_approved_provider BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth_tokens (
    token UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buses (
    id SERIAL PRIMARY KEY,
    operator_name VARCHAR(100) DEFAULT 'RailYatra Express',
    bus_type VARCHAR(40) DEFAULT 'AC Sleeper',
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME,
    distance_km INT DEFAULT 0,
    base_price DECIMAL(10, 2) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    rating DECIMAL(2, 1) DEFAULT 4.2
);

CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(id),
    bus_id INT REFERENCES buses(id),
    passenger_name VARCHAR(100),
    passenger_email VARCHAR(120),
    passenger_phone VARCHAR(20),
    final_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    qr_payload TEXT NOT NULL,
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    provider_id INT REFERENCES users(id) NOT NULL,
    type VARCHAR(30) NOT NULL,                       -- mini_bus / self_driving_car
    name VARCHAR(120) NOT NULL,
    base_city VARCHAR(100) NOT NULL,
    seats INT NOT NULL,
    price_per_km DECIMAL(6, 2) NOT NULL,
    price_per_day_local DECIMAL(8, 2) NOT NULL,
    driver_allowance_per_day DECIMAL(6, 2) DEFAULT 0,
    description TEXT DEFAULT '',
    emoji VARCHAR(10) DEFAULT '🚐',
    status VARCHAR(20) DEFAULT 'pending',             -- pending / approved / rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicle_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(id) NOT NULL,
    vehicle_id INT REFERENCES vehicles(id) NOT NULL,
    trip_type VARCHAR(20) NOT NULL,                   -- local / outstation
    pickup_city VARCHAR(100) NOT NULL,
    drop_city VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    distance_km INT DEFAULT 0,
    days INT DEFAULT 1,
    base_fare DECIMAL(10, 2),
    driver_charges DECIMAL(10, 2),
    gst DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'CONFIRMED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);