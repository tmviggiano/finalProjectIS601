# IS601 Final Project — Calculator API

A full-stack web application built with **FastAPI**, **PostgreSQL**, and **Docker** that allows authenticated users to perform and manage calculations. Features include user registration and JWT-based authentication, a full BREAD interface for calculation history, and support for five operation types including the **Modulus** operation added as the final project feature.

**Docker Hub:** https://hub.docker.com/repository/docker/tomviggiano/601_finalproject 
**GitHub:** https://github.com/tmviggiano/finalProjectIS601

---

## 🧮 Features

- **User Authentication** — Register, login, and JWT-secured sessions
- **BREAD Operations** — Browse, Read, Edit, Add, and Delete calculations
- **Five Calculation Types:**
  - Addition
  - Subtraction
  - Multiplication
  - Division (with zero-division protection)
  - **Modulus** *(Final Project Feature — see below)*
- **Responsive Dashboard** — Web UI for managing calculations
- **Containerized** — Full Docker + PostgreSQL setup

---

## ✨ Final Project Feature: Modulus

The modulus operation (`%`) returns the remainder after division and was added as the new calculation type for this project.

**What was implemented:**
- `Modulus` model class in `app/models/calculation.py` with full input validation
- `modulus` operation in `app/operations/__init__.py`
- `CalculationType.MODULUS` added to the Pydantic schema in `app/schemas/calculation.py`
- `modulus` option added to the dropdown in the dashboard UI
- Full BREAD support — modulus calculations can be created, viewed, edited, and deleted like any other type

**Behavior:**
- Supports two or more inputs, chaining left-to-right: `17 % 5 % 3 = 2`
- Raises a `ValueError` if any divisor is zero
- Returns a `float` result

**Tests added:**
- Unit tests in `tests/unit/test_calculator.py`
- Integration tests in `tests/integration/test_calculation.py`
- Schema tests in `tests/integration/test_calculation_schema.py`
- Route tests in `tests/integration/test_main.py`
- E2E tests in `tests/e2e/test_fastapi_calculator.py`

---

## 🚀 Running the Application

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/downloads)

### 1. Clone the Repository

```bash
git clone https://github.com/tmviggiano/finalProjectIS601.git
cd finalProjectIS601
```

### 2. Start the Application

```bash
docker compose up -d
```

This starts three services:
- `web` — FastAPI app on http://localhost:8000
- `db` — PostgreSQL on port 5432
- `pgadmin` — Database UI on http://localhost:5050

The database tables are created automatically on first startup via the SQLAlchemy lifespan event.

### 3. Open the App

Navigate to **http://localhost:8000** in your browser. Register an account and log in to start using the calculator.

### pgAdmin (Optional)

Access the database UI at http://localhost:5050  
- Email: `admin@example.com`  
- Password: `admin`

### Stop the Application

```bash
docker compose down
```

To also remove stored data:

```bash
docker compose down -v
```

---

## 🧪 Running Tests Locally

### Prerequisites

- Python 3.10+
- Docker (database must be running for integration and E2E tests)

### 1. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate.bat     # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Database

```bash
docker compose up -d db
```

Wait a few seconds for PostgreSQL to become healthy before running tests.

### 4. Run All Tests

```bash
pytest
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# With coverage report
pytest --cov=app --cov-report=term-missing

# Run slow tests (disabled by default)
pytest --run-slow
```

### Preserve the Test Database Between Runs

```bash
pytest --preserve-db
```

---

## 🔐 Security

- Passwords are hashed using **bcrypt** before storage — plain-text passwords are never saved
- Authentication uses **JWT access tokens** (Bearer) and **refresh tokens**
- All calculation endpoints require a valid token — unauthenticated requests return `401`
- Users can only access their own calculations — cross-user access returns `404`
- Input validation is enforced by **Pydantic** schemas before any data reaches the database
- Division and modulus by zero are caught at both the schema and model layers

---

## 🗂️ Project Structure

```
├── app/
│   ├── auth/               # JWT dependencies and Redis auth helpers
│   ├── core/               # App configuration and settings
│   ├── models/             # SQLAlchemy models (User, Calculation, and subtypes)
│   ├── operations/         # Pure calculation functions (add, subtract, multiply, divide, modulus)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── database.py         # Database engine and session setup
│   ├── database_init.py    # DB initialization helpers
│   └── main.py             # FastAPI app and all route definitions
├── static/                 # CSS and JavaScript
├── templates/              # Jinja2 HTML templates
├── tests/
│   ├── unit/               # Pure logic tests (no DB)
│   ├── integration/        # DB and route tests using TestClient
│   ├── e2e/                # End-to-end API and model tests
│   └── conftest.py         # Shared fixtures and session setup
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🌐 API Reference

All calculation endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive tokens |
| `POST` | `/auth/token` | Login via form (Swagger UI) |
| `GET` | `/calculations` | List all calculations for current user |
| `POST` | `/calculations` | Create a new calculation |
| `GET` | `/calculations/{id}` | Get a single calculation |
| `PUT` | `/calculations/{id}` | Update a calculation's inputs |
| `DELETE` | `/calculations/{id}` | Delete a calculation |
| `GET` | `/health` | Health check |

Interactive API docs are available at **http://localhost:8000/docs** when the app is running.

### Example: Create a Modulus Calculation

```bash
curl -X POST http://localhost:8000/calculations \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"type": "modulus", "inputs": [17, 5, 3]}'
```

Response:
```json
{
  "id": "...",
  "type": "modulus",
  "inputs": [17.0, 5.0, 3.0],
  "result": 2.0,
  "user_id": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 🐳 Docker Hub

The Docker image is published at:  
**https://hub.docker.com/repository/docker/tomviggiano/601_module13/general**

To pull and run the image directly:

```bash
docker pull tomviggiano/601_module13:latest
```

---

## ⚡ Quick Reference

| Action | Command |
|--------|---------|
| Start app | `docker compose up -d` |
| Stop app | `docker compose down` |
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=app --cov-report=term-missing` |
| Run unit tests | `pytest tests/unit/` |
| Run integration tests | `pytest tests/integration/` |
| Run E2E tests | `pytest tests/e2e/` |
| View logs | `docker compose logs -f web` |
| Rebuild image | `docker compose up -d --build` |