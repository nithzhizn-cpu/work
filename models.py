# models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    tablename = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    telegram_id = Column(String(100), nullable=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    pubkey = Column(Text, nullable=True)

    messages_sent = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.from_id",
        cascade="all, delete-orphan",
    )
    messages_received = relationship(
        "Message",
        back_populates="recipient",
        foreign_keys="Message.to_id",
        cascade="all, delete-orphan",
    )

    files_sent = relationship(
        "EncryptedFile",
        back_populates="sender",
        foreign_keys="EncryptedFile.from_id",
        cascade="all, delete-orphan",
    )
    files_received = relationship(
        "EncryptedFile",
        back_populates="recipient",
        foreign_keys="EncryptedFile.to_id",
        cascade="all, delete-orphan",
    )

    call_signals_sent = relationship(
        "CallSignal",
        back_populates="sender",
        foreign_keys="CallSignal.from_id",
        cascade="all, delete-orphan",
    )
    call_signals_received = relationship(
        "CallSignal",
        back_populates="recipient",
        foreign_keys="CallSignal.to_id",
        cascade="all, delete-orphan",
    )


class Message(Base):
    tablename = "messages"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    iv = Column(String(255), nullable=False)          # base64 IV для AES-GCM
    ciphertext = Column(Text, nullable=False)         # base64 зашифрований текст
    msg_type = Column(String(20), default="text")     # "text" / "system" / ...
    ttl_sec = Column(Integer, nullable=True)          # час життя (для авто-видалення)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", foreign_keys=[from_id], back_populates="messages_sent")
    recipient = relationship("User", foreign_keys=[to_id], back_populates="messages_received")


class EncryptedFile(Base):
    tablename = "files"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)

    iv = Column(String(255), nullable=False)          # IV для файлу
    ciphertext = Column(Text, nullable=False)         # base64-шифрований файл (blob/ciphertext)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", foreign_keys=[from_id], back_populates="files_sent")
    recipient = relationship("User", foreign_keys=[to_id], back_populates="files_received")


class CallSignal(Base):
    """
    Черга сигналів WebRTC:
      - offer
      - answer
      - candidate
      - bye
    """
    tablename = "call_signals"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    signal_type = Column(String(20), nullable=False)  # offer/answer/candidate/bye
    payload = Column(Text, nullable=False)            # JSON-строка (SDP/candidate)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    consumed = Column(Integer, default=0, index=True)  # 0 = новий, 1 = доставлений
    sender = relationship("User", foreign_keys=[from_id], back_populates="call_signals_sent")
recipient = relationship("User", foreign_keys=[to_id], back_populates="call_signals_received")

    sender = relationship("User", foreign_keys=[from_id], back_populates="call_signals_sent")
