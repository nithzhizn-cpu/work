from sqlalchemy import Column, Integer, Text, DateTime
from database import Base
from datetime import datetime

class CallSignal(Base):
    __tablename__ = "call_signals"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer)
    to_id = Column(Integer)
    type = Column(Text)  # offer, answer, candidate
    payload = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
