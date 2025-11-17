# main.py
from datetime import datetime, timedelta
import secrets

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

import models
import schemas
from database import engine
from deps import get_db, get_current_user
from models import User, Message, EncryptedFile
from routes_calls import router as calls_router


# Створюємо таблиці
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SpySignal E2EE Backend (Railway B)")

# CORS — дозволяємо фронтенду (WebApp / GitHub)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # у продакшені краще обмежити домени
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- HEALTH ----------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- AUTH / REGISTER ----------

@app.post("/api/register")
def register(
    req: schemas.RegisterRequest,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        return {
            "id": existing.id,
            "username": existing.username,
            "token": existing.token,
        }

    token = secrets.token_hex(32)

    user = User(
        username=req.username,
        telegram_id=req.telegram_id,
        token=token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "token": user.token,
    }


# ---------- USERS SEARCH ----------

@app.get("/api/users/search")
def search_users(
    query: str = Query(..., alias="query"),
    db: Session = Depends(get_db),
):
    q = query.strip()
    if not q:
        return {"results": []}

    results = []

    if q.isdigit():
        u = db.query(User).filter(User.id == int(q)).first()
        if u:
            results.append(u)

    by_name = (
        db.query(User)
        .filter(User.username.ilike(f"%{q}%"))
        .all()
    )

    for u in by_name:
        if u not in results:
            results.append(u)

    return {"results": [schemas.UserOut.model_validate(u) for u in results]}


# ---------- PUBKEY ----------

@app.post("/api/pubkey")
def save_pubkey(
    req: schemas.PubKeyUpdate,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current.pubkey = req.pubkey
    db.commit()
    return {"ok": True}


@app.get("/api/pubkey/{user_id}", response_model=schemas.PubKeyOut)
def get_pubkey(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.pubkey:
        raise HTTPException(status_code=404, detail="No pubkey")
    return {"pubkey": user.pubkey}


# ---------- MESSAGES (E2EE TEXT) ----------

@app.post("/api/messages")
def create_message(
    msg: schemas.MessageCreate,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    peer = db.query(User).filter(User.id == msg.to).first()
    if not peer:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db_msg = Message(
        from_id=current.id,
        to_id=peer.id,
        iv=msg.iv,
        ciphertext=msg.ciphertext,
        msg_type=msg.msg_type or "text",
        ttl_sec=msg.ttl_sec,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    return {"ok": True, "id": db_msg.id}


@app.get("/api/messages", response_model=schemas.MessagesResponse)
def get_messages(
    peer_id: int = Query(...),
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()

    msgs = (
        db.query(Message)
        .filter(
            ((Message.from_id == current.id) & (Message.to_id == peer_id))
            | ((Message.from_id == peer_id) & (Message.to_id == current.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    visible = []
    for m in msgs:
        if m.ttl_sec is not None:
            if m.created_at + timedelta(seconds=m.ttl_sec) < now:
                continue
        visible.append(m)

    return {"messages": visible}


# ---------- FILES (E2EE FILES) ----------

@app.post("/api/files")
def upload_file(
    body: schemas.FileUpload,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    peer = db.query(User).filter(User.id == body.to).first()
    if not peer:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db_file = EncryptedFile(
        from_id=current.id,
        to_id=peer.id,
        filename=body.filename,
        mime_type=body.mime_type,
        size=body.size,
        iv=body.iv,
        ciphertext=body.ciphertext,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {"ok": True, "id": db_file.id}


@app.get("/api/files", response_model=schemas.FilesResponse)
def list_files(
    peer_id: int = Query(...),
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    files = (
        db.query(EncryptedFile)
        .filter(
            ((EncryptedFile.from_id == current.id) & (EncryptedFile.to_id == peer_id))
            | ((EncryptedFile.from_id == peer_id) & (EncryptedFile.to_id == current.id))
        )
        .order_by(EncryptedFile.created_at.asc())
        .all()
    )

    return {"files": files}


# ---------- INCLUDE CALL ROUTES ----------

app.include_router(calls_router, prefix="/call")
