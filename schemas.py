# schemas.py
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict


# ---------- User / Auth ----------

class RegisterRequest(BaseModel):
    username: str
    telegram_id: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


# ---------- PubKey ----------

class PubKeyUpdate(BaseModel):
    pubkey: str


class PubKeyOut(BaseModel):
    pubkey: str


# ---------- Messages ----------

class MessageCreate(BaseModel):
    to: int
    iv: str
    ciphertext: str
    msg_type: Optional[str] = "text"
    ttl_sec: Optional[int] = None


class MessageOut(BaseModel):
    id: int
    from_id: int
    to_id: int
    iv: str
    ciphertext: str
    msg_type: str
    ttl_sec: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessagesResponse(BaseModel):
    messages: List[MessageOut]


# ---------- Files ----------

class FileUpload(BaseModel):
    to: int
    filename: str
    mime_type: Optional[str] = None
    size: Optional[int] = None
    iv: str
    ciphertext: str       # base64 шифр-файлу, клієнт шифрує сам


class FileOut(BaseModel):
    id: int
    from_id: int
    to_id: int
    filename: str
    mime_type: Optional[str] = None
    size: Optional[int] = None
    iv: str
    ciphertext: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilesResponse(BaseModel):
    files: List[FileOut]


# ---------- Calls (WebRTC signaling) ----------

class CallSignalIn(BaseModel):
    to: int
    type: str            # offer / answer / candidate / bye
    payload: Dict[str, Any]


class CallSignalOut(BaseModel):
    id: int
    from_id: int
    to_id: int
    type: str
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallPollResponse(BaseModel):
    signals: List[CallSignalOut]
