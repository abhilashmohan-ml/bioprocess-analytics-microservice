from .db import Batch
from .models import BatchCreate, BatchRead
from sqlalchemy.orm import Session
from uuid import uuid4

class BatchService:
    @staticmethod
    def create_batch(db: Session, payload: BatchCreate) -> BatchRead:
        batch = Batch(
            id=uuid4(),
            batch_id=payload.batch_id,
            date_time=payload.date_time,
            product=payload.product,
            location=payload.location,
            process=payload.process,
            process_step=payload.process_step,
            qc_batch_id=payload.qc_batch_id,
            process_batch_end_date=payload.process_batch_end_date,
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return BatchRead(
            id=batch.id,
            batch_id=batch.batch_id,
            date_time=batch.date_time,
            product=batch.product,
            location=batch.location,
            process=batch.process,
            process_step=batch.process_step,
            qc_batch_id=batch.qc_batch_id,
            process_batch_end_date=batch.process_batch_end_date,
        )

    @staticmethod
    def get_batch(db: Session, batch_id: str) -> BatchRead:
        batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
        if not batch:
            return None
        return BatchRead(
            id=batch.id,
            batch_id=batch.batch_id,
            date_time=batch.date_time,
            product=batch.product,
            location=batch.location,
            process=batch.process,
            process_step=batch.process_step,
            qc_batch_id=batch.qc_batch_id,
            process_batch_end_date=batch.process_batch_end_date,
        )
