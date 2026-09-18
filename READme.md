NexRoute – Smart Transit & Vehicle Hire Platform for India

NexRoute is a full-stack cloud-native transportation platform designed to simplify intercity travel and vehicle rental across India. The platform enables users to search and book bus tickets, hire tourist mini-buses and self-driving cars, while providing dedicated Provider and Admin dashboards for fleet management and operational control.

Built with scalability, modular architecture, and modern web technologies, NexRoute demonstrates practical implementation of authentication, RESTful APIs, pricing engines, role-based access control, and responsive frontend development.

⸻

Key Features

Traveller Portal

* Secure user registration and login
* Search buses across major Indian cities
* Digital ticket generation with booking verification
* Real-time seat availability
* Interactive and responsive user interface
* Personal booking history

Vehicle Hire Platform

* Tourist Mini Bus booking
* Self-Driving Car rental
* Local (80 km / 8 hours) packages
* Outstation trip booking
* Automated fare calculation
* GST-inclusive pricing
* Driver allowance calculations
* Distance estimation between Indian cities

Provider Dashboard

* Provider account registration
* Vehicle listing management
* Submit vehicles for approval
* Track customer bookings
* Fleet management interface

Admin Dashboard

* Role-based administrator access
* Approve or reject provider vehicles
* Publish new bus routes
* Monitor bookings
* View platform statistics
* Manage transportation network

⸻

Technical Highlights

* RESTful API architecture using FastAPI
* SQLAlchemy ORM for database management
* PBKDF2 password hashing with secure session tokens
* Role-Based Access Control (RBAC)
* Responsive frontend using Vanilla JavaScript
* Modular backend architecture
* SQLite support for development
* PostgreSQL support for production
* Dockerized deployment environment

⸻

Technology Stack

Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic

Frontend

* HTML5
* CSS3
* JavaScript (ES6)
* Fetch API

Database

* SQLite (Development)
* PostgreSQL (Production)

DevOps

* Docker
* Docker Compose
* Git & GitHub

⸻

Project Architecture

backend/         FastAPI app, models, seed script, schema, dependencies
frontend/        Traveller/admin HTML and shared static assets
Dockerfile       Production container entrypoint
Docker-compose.yml  Local PostgreSQL deployment

⸻

Installation

Before starting locally, copy `.env.example` to `.env` and replace every
`replace-with-a-strong-password` value. The `.env` file is ignored by Git.
The seed command requires `ADMIN_EMAIL`, `ADMIN_PASSWORD`,
`PROVIDER_PASSWORD`, and `SEED_USER_PASSWORD`; all seeded passwords are
hashed before persistence.

Using Docker

docker compose -f Docker-compose.yml up --build
docker compose -f Docker-compose.yml exec app python -m backend.seed

Open:

* http://localhost:8000 — Traveller Portal
* http://localhost:8000/admin — Provider & Admin Dashboard

⸻

Local Development

pip install -r backend/requirements.txt
python -m backend.seed
uvicorn backend.main:app --reload

⸻

Bootstrap Accounts

The seed script creates one administrator, provider, and traveller account
using the credentials configured in `.env`. It does not print passwords.

⸻

Core Functionalities

* User Authentication
* Bus Reservation System
* Digital Ticket Generation
* Vehicle Rental System
* Dynamic Fare Calculation
* Route Management
* Booking Management
* Admin Approval Workflow
* Provider Fleet Management
* REST API Integration

⸻

Future Enhancements

* Online Payment Gateway Integration
* Live Bus Tracking
* GPS-enabled Vehicle Tracking
* QR Code Ticket Validation
* Email & SMS Notifications
* AI-based Fare Prediction
* Analytics Dashboard
* Mobile Application
* Multi-language Support

⸻

Learning Outcomes

This project demonstrates practical implementation of:

* Backend API Development
* Authentication & Authorization
* Database Design
* SQLAlchemy ORM
* REST API Design
* Responsive UI Development
* Docker Deployment
* Software Architecture
* Git Version Control
* Full Stack Application Development

⸻

Developer

Devesh Pratap

Machine Learning Engineer | Data Analyst | Power BI Developer | Cloud Computing Enthusiast

Portfolio: https://deveshpratap.vercel.app

GitHub: https://github.com/dvs2121

LinkedIn: https://www.linkedin.com/in/devesh-prajapati-8b906b25a
