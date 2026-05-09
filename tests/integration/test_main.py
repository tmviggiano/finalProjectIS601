# ======================================================================================
# tests/integration/test_main.py
# ======================================================================================
# Purpose: Integration tests for all FastAPI routes in app/main.py using TestClient.
#          Covers auth, calculations (BREAD), web pages, and health endpoints.
# ======================================================================================

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db, get_engine, get_sessionmaker
from app.core.config import settings
from app.database_init import init_db
from unittest.mock import patch

# ======================================================================================
# Test Database Setup
# ======================================================================================

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


def override_get_db():
    """Override the default DB dependency to use the test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)

# ======================================================================================
# Shared Test Data
# ======================================================================================

VALID_USER = {
    "first_name": "Test",
    "last_name": "User",
    "email": "testmain@example.com",
    "username": "testmainuser",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
}

VALID_USER_2 = {
    "first_name": "Second",
    "last_name": "User",
    "email": "testmain2@example.com",
    "username": "testmainuser2",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
}

# ======================================================================================
# Helpers
# ======================================================================================

def register_and_login(user_data: dict = None) -> str:
    """
    Register a user and return a valid Bearer token.
    Uses VALID_USER by default; pass a different dict for a unique user.
    """
    if user_data is None:
        user_data = VALID_USER
    # Ignore 400 in case the user already exists from a prior test
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Return Authorization header dict for a given token."""
    return {"Authorization": f"Bearer {token}"}


# ======================================================================================
# Health Endpoint
# ======================================================================================

class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ======================================================================================
# Web (HTML) Routes
# ======================================================================================

class TestWebRoutes:
    def test_index_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_login_page_returns_html(self):
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_register_page_returns_html(self):
        response = client.get("/register")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_page_returns_html(self):
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_view_calculation_page_returns_html(self):
        fake_id = str(uuid4())
        response = client.get(f"/dashboard/view/{fake_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_edit_calculation_page_returns_html(self):
        fake_id = str(uuid4())
        response = client.get(f"/dashboard/edit/{fake_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


# ======================================================================================
# Auth: Registration
# ======================================================================================

class TestAuthRegister:
    def test_register_new_user_returns_201(self):
        unique_user = {
            "first_name": "New",
            "last_name": "User",
            "email": f"newuser_{uuid4().hex[:6]}@example.com",
            "username": f"newuser_{uuid4().hex[:6]}",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        response = client.post("/auth/register", json=unique_user)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_user["email"]
        assert data["username"] == unique_user["username"]
        assert "id" in data
        # Password should never be returned
        assert "password" in data or "password" not in data  # just check no crash
        assert "password" not in data

    def test_register_duplicate_email_returns_400(self):
        user = {
            "first_name": "Dup",
            "last_name": "User",
            "email": "duplicate@example.com",
            "username": f"dupuser_{uuid4().hex[:6]}",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        client.post("/auth/register", json=user)
        # Register again with same email but different username
        user["username"] = f"dupuser2_{uuid4().hex[:6]}"
        response = client.post("/auth/register", json=user)
        assert response.status_code == 400

    def test_register_mismatched_passwords_returns_422(self):
        response = client.post("/auth/register", json={
            "first_name": "Bad",
            "last_name": "Pass",
            "email": "badpass@example.com",
            "username": "badpassuser",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!"
        })
        assert response.status_code == 422

    def test_register_weak_password_returns_422(self):
        response = client.post("/auth/register", json={
            "first_name": "Weak",
            "last_name": "Pass",
            "email": "weakpass@example.com",
            "username": "weakpassuser",
            "password": "short",
            "confirm_password": "short"
        })
        assert response.status_code == 422

    def test_register_missing_fields_returns_422(self):
        response = client.post("/auth/register", json={
            "first_name": "Incomplete"
        })
        assert response.status_code == 422


# ======================================================================================
# Auth: Login (JSON)
# ======================================================================================

class TestAuthLogin:
    def test_login_valid_credentials_returns_token(self):
        unique_user = {
            "first_name": "Login",
            "last_name": "Test",
            "email": f"logintest_{uuid4().hex[:6]}@example.com",
            "username": f"logintest_{uuid4().hex[:6]}",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        client.post("/auth/register", json=unique_user)
        response = client.post("/auth/login", json={
            "username": unique_user["username"],
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert data["username"] == unique_user["username"]

    def test_login_invalid_password_returns_401(self):
        response = client.post("/auth/login", json={
            "username": VALID_USER["username"],
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"

    def test_login_nonexistent_user_returns_401(self):
        response = client.post("/auth/login", json={
            "username": "doesnotexist",
            "password": "SecurePass123!"
        })
        assert response.status_code == 401

    def test_login_with_email_returns_token(self):
        unique_user = {
            "first_name": "Email",
            "last_name": "Login",
            "email": f"emaillogin_{uuid4().hex[:6]}@example.com",
            "username": f"emaillogin_{uuid4().hex[:6]}",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        client.post("/auth/register", json=unique_user)
        response = client.post("/auth/login", json={
            "username": unique_user["email"],  # login with email
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


# ======================================================================================
# Auth: Token (Form Login)
# ======================================================================================

class TestAuthToken:
    def test_form_login_returns_access_token(self):
        unique_user = {
            "first_name": "Form",
            "last_name": "Login",
            "email": f"formlogin_{uuid4().hex[:6]}@example.com",
            "username": f"formlogin_{uuid4().hex[:6]}",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        client.post("/auth/register", json=unique_user)
        response = client.post("/auth/token", data={
            "username": unique_user["username"],
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_form_login_invalid_credentials_returns_401(self):
        response = client.post("/auth/token", data={
            "username": "nobody",
            "password": "BadPass123!"
        })
        assert response.status_code == 401


# ======================================================================================
# Calculations: Create (POST /calculations)
# ======================================================================================

class TestCreateCalculation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = register_and_login(VALID_USER)
        self.headers = auth_headers(self.token)

    def test_create_addition_calculation(self):
        response = client.post("/calculations",
            json={"type": "addition", "inputs": [10, 5, 3]},
            headers=self.headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "addition"
        assert data["result"] == 18.0
        assert "id" in data
        assert "user_id" in data

    def test_create_subtraction_calculation(self):
        response = client.post("/calculations",
            json={"type": "subtraction", "inputs": [20, 5, 3]},
            headers=self.headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 12.0

    def test_create_multiplication_calculation(self):
        response = client.post("/calculations",
            json={"type": "multiplication", "inputs": [2, 3, 4]},
            headers=self.headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 24.0

    def test_create_division_calculation(self):
        response = client.post("/calculations",
            json={"type": "division", "inputs": [100, 4]},
            headers=self.headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 25.0

    def test_create_modulus_calculation(self):
        response = client.post("/calculations",
            json={"type": "modulus", "inputs": [10, 3]},
            headers=self.headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 1.0

    def test_create_calculation_division_by_zero_returns_422(self):
        # Schema validator catches division by zero before the route runs
        response = client.post("/calculations",
            json={"type": "division", "inputs": [10, 0]},
            headers=self.headers
        )
        assert response.status_code == 422

    def test_create_calculation_invalid_type_returns_422(self):
        response = client.post("/calculations",
            json={"type": "exponent", "inputs": [2, 3]},
            headers=self.headers
        )
        assert response.status_code == 422

    def test_create_calculation_single_input_returns_422(self):
        response = client.post("/calculations",
            json={"type": "addition", "inputs": [5]},
            headers=self.headers
        )
        assert response.status_code == 422

    def test_create_calculation_unauthenticated_returns_401(self):
        response = client.post("/calculations",
            json={"type": "addition", "inputs": [1, 2]}
        )
        assert response.status_code == 401

    def test_create_calculation_invalid_token_returns_401(self):
        response = client.post("/calculations",
            json={"type": "addition", "inputs": [1, 2]},
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401


# ======================================================================================
# Calculations: List (GET /calculations)
# ======================================================================================

class TestListCalculations:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = register_and_login(VALID_USER)
        self.headers = auth_headers(self.token)

    def test_list_calculations_returns_200(self):
        response = client.get("/calculations", headers=self.headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_calculations_only_returns_own(self):
        # Create a calculation for VALID_USER
        client.post("/calculations",
            json={"type": "addition", "inputs": [1, 2]},
            headers=self.headers
        )
        # Create a second user and their calculation
        token2 = register_and_login(VALID_USER_2)
        client.post("/calculations",
            json={"type": "multiplication", "inputs": [3, 4]},
            headers=auth_headers(token2)
        )
        # VALID_USER should not see VALID_USER_2's calculations
        response = client.get("/calculations", headers=self.headers)
        assert response.status_code == 200
        for calc in response.json():
            assert calc["type"] != "multiplication" or calc["inputs"] != [3.0, 4.0]

    def test_list_calculations_unauthenticated_returns_401(self):
        response = client.get("/calculations")
        assert response.status_code == 401


# ======================================================================================
# Calculations: Get by ID (GET /calculations/{calc_id})
# ======================================================================================

class TestGetCalculation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = register_and_login(VALID_USER)
        self.headers = auth_headers(self.token)
        # Create a calculation to retrieve
        resp = client.post("/calculations",
            json={"type": "addition", "inputs": [7, 8]},
            headers=self.headers
        )
        assert resp.status_code == 201
        self.calc_id = resp.json()["id"]

    def test_get_calculation_by_id_returns_200(self):
        response = client.get(f"/calculations/{self.calc_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.calc_id
        assert data["result"] == 15.0

    def test_get_calculation_not_found_returns_404(self):
        fake_id = str(uuid4())
        response = client.get(f"/calculations/{fake_id}", headers=self.headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Calculation not found."

    def test_get_calculation_invalid_uuid_returns_400(self):
        response = client.get("/calculations/not-a-uuid", headers=self.headers)
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid calculation id format."

    def test_get_calculation_unauthenticated_returns_401(self):
        response = client.get(f"/calculations/{self.calc_id}")
        assert response.status_code == 401

    def test_get_calculation_other_users_calc_returns_404(self):
        """A user should not be able to access another user's calculation."""
        token2 = register_and_login(VALID_USER_2)
        response = client.get(f"/calculations/{self.calc_id}",
            headers=auth_headers(token2)
        )
        assert response.status_code == 404


# ======================================================================================
# Calculations: Update (PUT /calculations/{calc_id})
# ======================================================================================

class TestUpdateCalculation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = register_and_login(VALID_USER)
        self.headers = auth_headers(self.token)
        resp = client.post("/calculations",
            json={"type": "addition", "inputs": [1, 2]},
            headers=self.headers
        )
        assert resp.status_code == 201
        self.calc_id = resp.json()["id"]

    def test_update_calculation_inputs(self):
        response = client.put(f"/calculations/{self.calc_id}",
            json={"inputs": [10, 20, 30]},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 60.0
        assert data["inputs"] == [10.0, 20.0, 30.0]

    def test_update_calculation_not_found_returns_404(self):
        response = client.put(f"/calculations/{uuid4()}",
            json={"inputs": [5, 5]},
            headers=self.headers
        )
        assert response.status_code == 404

    def test_update_calculation_invalid_uuid_returns_400(self):
        response = client.put("/calculations/bad-uuid",
            json={"inputs": [5, 5]},
            headers=self.headers
        )
        assert response.status_code == 400

    def test_update_calculation_unauthenticated_returns_401(self):
        response = client.put(f"/calculations/{self.calc_id}",
            json={"inputs": [5, 5]}
        )
        assert response.status_code == 401

    def test_update_calculation_other_users_calc_returns_404(self):
        token2 = register_and_login(VALID_USER_2)
        response = client.put(f"/calculations/{self.calc_id}",
            json={"inputs": [9, 9]},
            headers=auth_headers(token2)
        )
        assert response.status_code == 404


# ======================================================================================
# Calculations: Delete (DELETE /calculations/{calc_id})
# ======================================================================================

class TestDeleteCalculation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = register_and_login(VALID_USER)
        self.headers = auth_headers(self.token)

    def _create_calc(self) -> str:
        resp = client.post("/calculations",
            json={"type": "subtraction", "inputs": [100, 1]},
            headers=self.headers
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_delete_calculation_returns_204(self):
        calc_id = self._create_calc()
        response = client.delete(f"/calculations/{calc_id}", headers=self.headers)
        assert response.status_code == 204

    def test_delete_calculation_is_gone_after_deletion(self):
        calc_id = self._create_calc()
        client.delete(f"/calculations/{calc_id}", headers=self.headers)
        response = client.get(f"/calculations/{calc_id}", headers=self.headers)
        assert response.status_code == 404

    def test_delete_calculation_not_found_returns_404(self):
        response = client.delete(f"/calculations/{uuid4()}", headers=self.headers)
        assert response.status_code == 404

    def test_delete_calculation_invalid_uuid_returns_400(self):
        response = client.delete("/calculations/not-a-uuid", headers=self.headers)
        assert response.status_code == 400

    def test_delete_calculation_unauthenticated_returns_401(self):
        calc_id = self._create_calc()
        response = client.delete(f"/calculations/{calc_id}")
        assert response.status_code == 401

    def test_delete_calculation_other_users_calc_returns_404(self):
        calc_id = self._create_calc()
        token2 = register_and_login(VALID_USER_2)
        response = client.delete(f"/calculations/{calc_id}",
            headers=auth_headers(token2)
        )
        assert response.status_code == 404
        # Confirm calc still exists for the original user
        check = client.get(f"/calculations/{calc_id}", headers=self.headers)
        assert check.status_code == 200




def test_login_expires_at_branch():
    """Covers the expires_at timezone branch in /auth/login (line 204)."""
    unique_user = {
        "first_name": "Exp",
        "last_name": "Test",
        "email": f"exptest_{uuid4().hex[:6]}@example.com",
        "username": f"exptest_{uuid4().hex[:6]}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    client.post("/auth/register", json=unique_user)
    response = client.post("/auth/login", json={
        "username": unique_user["username"],
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "expires_at" in response.json()

def test_create_calculation_model_value_error_returns_400():
    """Covers the ValueError except block in create_calculation (lines 274-276)."""
    token = register_and_login()
    with patch("app.main.Calculation.create", side_effect=ValueError("Mocked model error")):
        response = client.post(
            "/calculations",
            json={"type": "addition", "inputs": [1, 2]},
            headers=auth_headers(token)
        )
    assert response.status_code == 400
    assert "Mocked model error" in response.json()["detail"]