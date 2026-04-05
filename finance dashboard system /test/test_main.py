import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash
from app.models import User, RoleEnum

# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    # Seed an Admin user
    db = TestingSessionLocal()
    admin_user = User(
        username="admin_test", 
        hashed_password=get_password_hash("testpass"), 
        role=RoleEnum.admin
    )
    db.add(admin_user)
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_token():
    response = client.post("/login", data={"username": "admin_test", "password": "testpass"})
    return response.json()["access_token"]

def test_login_success():
    response = client.post("/login", data={"username": "admin_test", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_rate_limit():
    for _ in range(5):
        client.post("/login", data={"username": "wrong", "password": "wrong"})
    
    response = client.post("/login", data={"username": "wrong", "password": "wrong"})
    assert response.status_code == 429

def test_create_and_soft_delete_record():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    record_data = {"amount": 500, "type": "income", "category": "Salary", "notes": "Bonus"}
    response = client.post("/records", json=record_data, headers=headers)
    assert response.status_code == 200
    record_id = response.json()["id"]
    
    get_response = client.get("/records", headers=headers)
    assert len(get_response.json()) == 1
    
    delete_response = client.delete(f"/records/{record_id}", headers=headers)
    assert delete_response.status_code == 200
    
    get_response_after = client.get("/records", headers=headers)
    assert len(get_response_after.json()) == 0

def test_dashboard_calculations():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    client.post("/records", json={"amount": 1000, "type": "income", "category": "Salary"}, headers=headers)
    client.post("/records", json={"amount": 200, "type": "expense", "category": "Food"}, headers=headers)
    
    response = client.get("/dashboard/summary", headers=headers)
    data = response.json()
    
    assert data["total_income"] == 1000.0
    assert data["total_expenses"] == 200.0
    assert data["net_balance"] == 800.0