from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import CallSignal
from schemas import SignalIn

router = APIRouter(prefix="/call", tags=["calls"])

def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/offer")
def offer(data: SignalIn, db: Session = Depends(db)):
    obj = CallSignal(**data.dict())
    db.add(obj)
    db.commit()
    return {"ok": True}

@router.post("/answer")
def answer(data: SignalIn, db: Session = Depends(db)):
    obj = CallSignal(**data.dict())
    db.add(obj)
    db.commit()
    return {"ok": True}

@router.post("/candidate")
def candidate(data: SignalIn, db: Session = Depends(db)):
    obj = CallSignal(**data.dict())
    db.add(obj)
    db.commit()
    return {"ok": True}

@router.get("/poll")
def poll(user_id: int, db: Session = Depends(db)):
    rows = db.query(CallSignal).filter(CallSignal.to_id == user_id).all()
    out = []
    for r in rows:
        out.append({"id": r.id, "from_id": r.from_id, "type": r.type, "payload": r.payload})
        db.delete(r)
    db.commit()
    return {"signals": out}
