from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app import models, schemas, crud, auth, database
from app.models import RoleEnum

models.Base.metadata.create_all(bind=database.engine)

# Enhancement: Rich API Metadata
tags_metadata = [
    {"name": "Auth", "description": "Operations with user authentication and token generation."},
    {"name": "Users", "description": "Manage user accounts and roles."},
    {"name": "Records", "description": "Manage financial entries (income/expense)."},
    {"name": "Dashboard", "description": "Aggregated analytics for the frontend."}
]

app = FastAPI(
    title="Finance Dashboard API",
    description="A robust backend for managing financial records, roles, and generating aggregated analytics.",
    version="1.1.0",
    openapi_tags=tags_metadata
)

# Enhancement: Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login", response_model=schemas.Token, tags=["Auth"])
@limiter.limit("5/minute") # Protects against brute-force login attempts
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """Authenticate a user and return a JWT bearer token."""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=schemas.UserResponse, tags=["Users"], status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Register a new user in the system."""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/records", response_model=schemas.RecordResponse, tags=["Records"])
def create_record(
    record: schemas.RecordCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_roles([RoleEnum.admin]))
):
    """Create a new financial record. (Requires Admin role)"""
    return crud.create_record(db, record, current_user.id)

@app.get("/records", response_model=List[schemas.RecordResponse], tags=["Records"])
def read_records(
    skip: int = 0, 
    limit: int = 100, 
    type: models.RecordTypeEnum = None,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_roles([RoleEnum.admin, RoleEnum.analyst]))
):
    """Retrieve financial records. Supports pagination, filtering by type, and keyword search. (Requires Admin or Analyst role)"""
    return crud.get_records(db, skip=skip, limit=limit, record_type=type, search=search)

@app.delete("/records/{record_id}", tags=["Records"])
def delete_record(
    record_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_roles([RoleEnum.admin]))
):
    """Soft-delete a specific record. (Requires Admin role)"""
    record = crud.delete_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"detail": "Record deleted successfully"}

@app.get("/dashboard/summary", response_model=schemas.DashboardSummary, tags=["Dashboard"])
def get_dashboard(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_roles([RoleEnum.admin, RoleEnum.analyst, RoleEnum.viewer]))
):
    """Retrieve aggregated dashboard analytics. (Available to all roles)"""
    return crud.get_dashboard_summary(db)