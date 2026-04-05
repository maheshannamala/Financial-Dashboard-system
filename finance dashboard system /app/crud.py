from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas, auth

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pwd, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_record(db: Session, record: schemas.RecordCreate, user_id: int):
    db_record = models.FinancialRecord(**record.model_dump(), created_by_id=user_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_records(db: Session, skip: int = 0, limit: int = 100, record_type: str = None, search: str = None):
    # Ignore soft-deleted records
    query = db.query(models.FinancialRecord).filter(models.FinancialRecord.is_deleted == 0)
    
    if record_type:
        query = query.filter(models.FinancialRecord.type == record_type)
        
    # Enhancement: Keyword search
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (models.FinancialRecord.category.ilike(search_fmt)) |
            (models.FinancialRecord.notes.ilike(search_fmt))
        )
        
    return query.offset(skip).limit(limit).all()

def delete_record(db: Session, record_id: int):
    record = db.query(models.FinancialRecord).filter(
        models.FinancialRecord.id == record_id, 
        models.FinancialRecord.is_deleted == 0
    ).first()
    
    # Enhancement: Soft Delete
    if record:
        record.is_deleted = 1
        db.commit()
    return record

def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
    # Subquery to ignore soft-deleted records in analytics
    active_records = db.query(models.FinancialRecord).filter(models.FinancialRecord.is_deleted == 0).subquery()
    
    income = db.query(func.sum(active_records.c.amount)).filter(active_records.c.type == "income").scalar() or 0.0
    expense = db.query(func.sum(active_records.c.amount)).filter(active_records.c.type == "expense").scalar() or 0.0
    
    category_data = db.query(
        active_records.c.category, 
        func.sum(active_records.c.amount).label("total")
    ).filter(active_records.c.type == "expense").group_by(active_records.c.category).all()
    
    categories = [{"category": row.category, "total": row.total} for row in category_data]

    return schemas.DashboardSummary(
        total_income=income,
        total_expenses=expense,
        net_balance=income - expense,
        category_expenses=categories
    )