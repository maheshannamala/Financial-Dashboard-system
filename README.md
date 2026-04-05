# Financial-Dashboard-system
A robust backend for a Finance Dashboard system. Built with Python and FastAPI, featuring JWT auth, strict role-based access (Admin/Analyst/Viewer), rate limiting, and soft deletes.
Finance Dashboard REST API

> A robust, production-ready backend service for managing financial records, generating dashboard analytics, and enforcing strict role-based access control (RBAC).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-e92063.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Core Features](#-core-features)
3. [Tech Stack](#-tech-stack)
4. [Architecture & Design](#-architecture--design)
5. [Assumptions & Trade-offs](#-assumptions--trade-offs)
6. [Directory Structure](#-directory-structure)
7. [Environment Variables](#-environment-variables)
8. [Getting Started (Local Setup)](#-getting-started-local-setup)
9. [Docker Deployment](#-docker-deployment-optional)
10. [Roles & Permissions Matrix](#-roles--permissions-matrix)
11. [API Usage & Examples](#-api-usage--examples)
12. [Running Tests](#-running-tests)
13. [Contribution Guidelines](#-contribution-guidelines)

---

## 🚀 Project Overview
This project provides the backend infrastructure for a Finance Dashboard. It is designed to handle user authentication, securely manage income and expense entries, and serve aggregated financial summaries to a frontend client. 

The system goes beyond basic CRUD operations by implementing **Soft Deletes**, **Rate Limiting** (to prevent brute-force attacks), **Keyword Search**, and an automated **Unit Testing Suite**.

---

## ✨ Core Features
* **Authentication & Authorization:** Secure JWT-based login system with `bcrypt` password hashing.
* **Role-Based Access Control (RBAC):** Three distinct tiers (`Admin`, `Analyst`, `Viewer`) with strict dependency-injected endpoint guards.
* **Financial Management:** Full CRUD capabilities for tracking income and expenses.
* **Aggregated Analytics:** High-performance dashboard endpoints utilizing SQL aggregate functions to calculate net balances and category breakdowns.
* **Soft Deletes:** Records are flagged as deleted rather than permanently dropped from the database, ensuring historical data integrity.
* **Advanced Querying:** Support for pagination, filtering by transaction type, and keyword searches across categories and notes.
* **Rate Limiting:** Endpoints (like `/login`) are protected against abuse using `slowapi`.

---

## 🛠️ Tech Stack
* **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High performance, automatic Swagger documentation)
* **Data Validation:** [Pydantic V2](https://docs.pydantic.dev/) (Strict type hinting and payload serialization)
* **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Modern relational database management)
* **Database:** SQLite (Default, effortlessly swappable to PostgreSQL)
* **Security:** `passlib` (Hashing), `python-jose` (JWT), `slowapi` (Rate Limiting)
* **Testing:** `pytest`, `httpx` (Integration testing with dynamic in-memory databases)

---

## 🏛️ Architecture & Design Decisions
This application strictly adheres to the **Separation of Concerns (SoC)** principle to ensure maintainability and testability.
* **`main.py` (Routers):** Handles only HTTP requests, route definitions, and rate limiting.
* **`crud.py` (Data Access Layer):** Isolates all SQLAlchemy database queries. Routers call these functions rather than querying the database directly.
* **`schemas.py` (Validation Layer):** Defines Pydantic models to validate incoming JSON payloads and format outgoing API responses.
* **`auth.py` (Security Layer):** Centralizes token generation and RBAC logic using FastAPI's `Depends()` injection system.

**Trade-off Note:** SQLite was chosen for this iteration to provide a zero-config setup for evaluators. Because all database interactions are routed through SQLAlchemy, migrating to a production database like PostgreSQL requires changing a single connection string variable.

---

## 🧠 Assumptions & Trade-offs
In building this application, several engineering decisions were made to balance complexity, maintainability, and the specific needs of a backend assessment.

### Assumptions Made
1. **Single Currency:** For the scope of this dashboard, it is assumed that all financial records are logged in a single base currency (e.g., USD). Currency conversion and localization logic were omitted to keep the focus on core CRUD and RBAC mechanics.
2. **Internal User Management:** It is assumed this is an internal company tool. Therefore, there is no public "Sign Up" flow with email verification. Instead, Admins are responsible for creating and provisioning Analyst and Viewer accounts.
3. **Dashboard Aggregation:** It is assumed the frontend requires real-time calculations. The `/dashboard/summary` endpoint calculates totals on the fly using SQL aggregate functions. If the dataset grows to millions of rows, this assumption would change, and a caching layer (like Redis) or materialized views would be introduced.

### Trade-offs Considered
* **SQLite vs. PostgreSQL:** * *The Trade-off:* I chose SQLite over a robust database like PostgreSQL. 
  * *The Reasoning:* This prioritizes a zero-configuration, frictionless setup for the reviewer. To mitigate the downsides, all database interactions are abstracted behind **SQLAlchemy ORM**. Moving to PostgreSQL in production simply requires swapping the `DATABASE_URL` string.
* **Dependency Injection vs. Global Middleware for RBAC:** * *The Trade-off:* I implemented access control at the route level using FastAPI's `Depends()` rather than a global application middleware.
  * *The Reasoning:* While middleware requires less code repetition, Dependency Injection makes the permission requirements for each endpoint explicitly visible in the documentation (Swagger UI), improves type hinting, and makes individual routes significantly easier to unit test.
* **Soft Deletes vs. Hard Deletes:**
  * *The Trade-off:* I chose to implement soft deletes (flagging `is_deleted = 1`) rather than permanently dropping records from the database.
  * *The Reasoning:* This trades a minor amount of database storage space in exchange for data integrity, historical auditing, and the ability to restore accidentally deleted financial records.
* **Monolithic Architecture vs. Microservices:**
  * *The Trade-off:* The application is built as a single monolith rather than splitting Auth and Finance into separate microservices.
  * *The Reasoning:* For a dashboard of this scope, microservices would introduce unnecessary infrastructure complexity (network latency, distributed data). The monolithic approach ensures fast iteration and simple deployment.

 ---


## 📂 Directory Structure

```text
├── app/
│   ├── __init__.py      # Package initializer
│   ├── main.py          # FastAPI application & endpoints
│   ├── database.py      # Engine and SessionLocal configuration
│   ├── models.py        # SQLAlchemy database tables
│   ├── schemas.py       # Pydantic validation models
│   ├── crud.py          # Database operations (Create, Read, Update, Delete)
│   └── auth.py          # JWT, hashing, and RBAC dependencies
├── tests/
│   ├── __init__.py
│   └── test_main.py     # Pytest integration test suite
├── requirements.txt     # Dependency list
└── README.md            # Project documentation
