from .db import QCBatch
from .models import QCBatchCreate, QCBatchRead
from sqlalchemy.orm import Session
from uuid import uuid4

class QCBatchService:
    @staticmethod
    def create_qc_batch(db: Session, payload: QCBatchCreate) -> QCBatchRead:
        qcbatch = QCBatch(
            id=uuid4(),
            qc_batch_id=payload.qc_batch_id,
            date_time=payload.date_time,
            product=payload.product,
            location=payload.location,
            process=payload.process,
            process_step=payload.process_step,
            qc_batch_end_time=payload.qc_batch_end_time,
        )
        db.add(qcbatch)
        db.commit()
        db.refresh(qcbatch)
        return QCBatchRead(
            id=qcbatch.id,
            qc_batch_id=qcbatch.qc_batch_id,
            date_time=qcbatch.date_time,
            product=qcbatch.product,
            location=qcbatch.location,
            process=qcbatch.process,
            process_step=qcbatch.process_step,
            qc_batch_end_time=qcbatch.qc_batch_end_time,
        )

    @staticmethod
    def get_qc_batch(db: Session, qc_batch_id: str) -> QCBatchRead:
        qcbatch = db.query(QCBatch).filter(QCBatch.qc_batch_id == qc_batch_id).first()
        if not qcbatch:
            return None
        return QCBatchRead(
            id=qcbatch.id,
            qc_batch_id=qcbatch.qc_batch_id,
            date_time=qcbatch.date_time,
            product=qcbatch.product,
            location=qcbatch.location,
            process=qcbatch.process,
            process_step=qcbatch.process_step,
            qc_batch_end_time=qcbatch.qc_batch_end_time,
        )
