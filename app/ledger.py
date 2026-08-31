import hashlib
import json
from sqlalchemy.orm import Session
from . import models

def _compute_hash(prev_hash: str, event_type: str, payload: str) -> str:
    combined = f"{prev_hash}{event_type}{payload}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

def add_entry(db: Session, crop_id: int, event_type: str, payload: dict) -> models.LedgerEntry:
    last_entry = (
        db.query(models.LedgerEntry)
        .filter(models.LedgerEntry.crop_id == crop_id)
        .order_by(models.LedgerEntry.id.desc())
        .first()
    )
    prev_hash = last_entry.entry_hash if last_entry else "GENESIS"

    payload_str = json.dumps(payload, sort_keys=True, default=str)
    entry_hash = _compute_hash(prev_hash, event_type, payload_str)

    entry = models.LedgerEntry(
        crop_id=crop_id,
        event_type=event_type,
        payload=payload_str,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def verify_chain(db: Session, crop_id: int) -> dict:
    entries = (
        db.query(models.LedgerEntry)
        .filter(models.LedgerEntry.crop_id == crop_id)
        .order_by(models.LedgerEntry.id.asc())
        .all()
    )

    expected_prev_hash = "GENESIS"
    for entry in entries:
        recomputed_hash = _compute_hash(expected_prev_hash, entry.event_type, entry.payload)

        if entry.prev_hash != expected_prev_hash:
            return {"chain_valid": False, "broken_at_entry_id": entry.id, "reason": "prev_hash mismatch"}

        if entry.entry_hash != recomputed_hash:
            return {"chain_valid": False, "broken_at_entry_id": entry.id, "reason": "entry_hash mismatch — data was tampered"}

        expected_prev_hash = entry.entry_hash

    return {"chain_valid": True, "entries_checked": len(entries)}
