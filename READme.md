# Cloud-Based Bus Pass & Ticket Booking System

A scalable, cloud-native bus ticketing system designed to handle high traffic, prevent ticket theft/loss, and ensure 100% accurate pricing.

## Features
- **Cloud-Native**: Containerized with Docker for dynamic provisioning and auto-scaling.
- **Theft & Loss Prevention**: Uses cryptographic UUIDs for digital tickets. No physical tickets.
- **Accurate Pricing**: Server-side price calculation prevents client-side price manipulation.
- **High Traffic**: Asynchronous Python (FastAPI) backend capable of handling thousands of concurrent requests.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (Cloud), SQLite (Local Dev)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Fetch API)
- **Infrastructure**: Docker, Docker Compose

## Local Setup
1. Install Python 3.9+ and Docker.
2. Run the application using Docker Compose:
   ```bash
   docker-compose up --build