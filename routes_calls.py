# routes_calls.py
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from deps import get_db, get_current_user
from models import CallSignal
from schemas import CallSignalIn, CallSignalOut, CallPollResponse

router = APIRouter(tags=["calls"])


@router.post("/offer", response_model=CallSignalOut)
def send_offer(
    body: CallSignalIn,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.type != "offer":
        raise HTTPException(status_code=400, detail="type must be 'offer'")

    signal = CallSignal(
        from_id=current.id,
        to_id=body.to,
        signal_type="offer",
        payload=json.dumps(body.payload),
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return CallSignalOut(
        id=signal.id,
        from_id=signal.from_id,
        to_id=signal.to_id,
        type=signal.signal_type,
        payload=body.payload,
        created_at=signal.created_at,
    )


@router.post("/answer", response_model=CallSignalOut)
def send_answer(
    body: CallSignalIn,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.type != "answer":
        raise HTTPException(status_code=400, detail="type must be 'answer'")

    signal = CallSignal(
        from_id=current.id,
        to_id=body.to,
        signal_type="answer",
        payload=json.dumps(body.payload),
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return CallSignalOut(
        id=signal.id,
        from_id=signal.from_id,
        to_id=signal.to_id,
        type=signal.signal_type,
        payload=body.payload,
        created_at=signal.created_at,
    )


@router.post("/candidate", response_model=CallSignalOut)
def send_candidate(
    body: CallSignalIn,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.type != "candidate":
        raise HTTPException(status_code=400, detail="type must be 'candidate'")

    signal = CallSignal(
        from_id=current.id,
        to_id=body.to,
        signal_type="candidate",
        payload=json.dumps(body.payload),
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return CallSignalOut(
        id=signal.id,
        from_id=signal.from_id,
        to_id=signal.to_id,
        type=signal.signal_type,
        payload=body.payload,
        created_at=signal.created_at,
    )


@router.post("/bye", response_model=CallSignalOut)
def send_bye(
    body: CallSignalIn,
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.type != "bye":
        raise HTTPException(status_code=400, detail="type must be 'bye'")

    signal = CallSignal(
        from_id=current.id,
        to_id=body.to,
        signal_type="bye",
        payload=json.dumps(body.payload),
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return CallSignalOut(
        id=signal.id,
        from_id=signal.from_id,
        to_id=signal.to_id,
        type=signal.signal_type,
        payload=body.payload,
        created_at=signal.created_at,
    )


@router.get("/poll", response_model=CallPollResponse)
def poll_signals(
    since_id: int = Query(0),
    current = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Прибираємо старі сигнали (старші за 2 хвилини)
    cutoff = datetime.utcnow() - timedelta(minutes=2)
    db.query(CallSignal).filter(CallSignal.created_at < cutoff).delete()
    db.commit()

    signals = (
        db.query(CallSignal)
        .filter(
            CallSignal.to_id == current.id,
            CallSignal.id > since_id,
            CallSignal.consumed == 0,
        )
        .order_by(CallSignal.id.asc())
        .all()
    )

    result = []
    for s in signals:
        try:
            payload = json.loads(s.payload)
        except Exception:
            payload = {}

        result.append(
            CallSignalOut(
                id=s.id,
                from_id=s.from_id,to_id=s.to_id,
                type=s.signal_type,
                payload=payload,
                created_at=s.created_at,
            )
        )
        s.consumed = 1

    db.commit()

    return CallPollResponse(signals=result)
