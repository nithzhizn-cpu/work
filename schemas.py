from pydantic import BaseModel

class SignalIn(BaseModel):
    from_id: int
    to_id: int
    type: str
    payload: str

class SignalOut(SignalIn):
    id: int
