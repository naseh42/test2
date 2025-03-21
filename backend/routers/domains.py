from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.models import Domain
from backend.database.database import get_db

router = APIRouter()

# دریافت لیست دامنه‌ها
@router.get("/")
def get_domains(db: Session = Depends(get_db)):
    domains = db.query(Domain).all()
    return domains

# دریافت اطلاعات یک دامنه خاص
@router.get("/{domain_id}")
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

# اضافه کردن دامنه جدید
@router.post("/")
def create_domain(domain: Domain, db: Session = Depends(get_db)):
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain

# به‌روزرسانی اطلاعات دامنه
@router.put("/{domain_id}")
def update_domain(domain_id: int, updated_domain: Domain, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    for key, value in updated_domain.dict().items():
        setattr(domain, key, value)
    db.commit()
    return domain

# حذف دامنه
@router.delete("/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(domain)
    db.commit()
    return {"message": "Domain deleted successfully"}
