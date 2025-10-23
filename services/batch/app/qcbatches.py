"""QC Batch service logic with centralized configuration"""
from .db import QCBatch
from .models import QCBatchCreate, QCBatchRead
from sqlalchemy.orm import Session
from uuid import uuid4
import logging
import sys
from datetime import datetime
from typing import Optional
# Import centralized configuration
sys.path.append('../../..')
from shared.config import settings
from shared.event_bus import event_bus, EventType

logger = logging.getLogger(__name__)

class QCBatchService:
    """QC Batch service with centralized configuration and event emission"""
    
    @staticmethod
    def create_qc_batch(db: Session, payload: QCBatchCreate) -> QCBatchRead:
        """Create QC batch with centralized validation and event emission"""
        
        # Validate QC batch ID format
        if not payload.qc_batch_id or len(payload.qc_batch_id.strip()) == 0:
            raise ValueError("QC Batch ID cannot be empty")
        
        # Sanitize QC batch data using centralized sanitizer
        from shared.security import security_manager
        sanitized_qc_batch_id = security_manager.sanitize_input(payload.qc_batch_id)
        sanitized_product = security_manager.sanitize_input(payload.product)
        sanitized_location = security_manager.sanitize_input(payload.location)
        sanitized_process = security_manager.sanitize_input(payload.process)
        sanitized_process_step = security_manager.sanitize_input(payload.process_step)
        
        # Create QC batch with centralized configuration
        qcbatch = QCBatch(
            id=uuid4(),
            qc_batch_id=sanitized_qc_batch_id,
            date_time=payload.date_time,
            product=sanitized_product,
            location=sanitized_location,
            process=sanitized_process,
            process_step=sanitized_process_step,
            qc_batch_end_time=payload.qc_batch_end_time,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(qcbatch)
        db.commit()
        db.refresh(qcbatch)
        
        logger.info(f"✅ QC Batch created successfully: {qcbatch.qc_batch_id} (ID: {qcbatch.id})")
        
        # Emit QC batch creation event
        event_bus.publish_event(EventType.QC_BATCH_CREATED, {
            "qc_batch_id": str(qcbatch.id),
            "qc_batch_number": qcbatch.qc_batch_id,
            "product": qcbatch.product,
            "location": qcbatch.location,
            "process": qcbatch.process,
            "process_step": qcbatch.process_step,
            "timestamp": datetime.utcnow().isoformat()
        })
        
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
    def get_qc_batch(db: Session, qc_batch_id: str) -> Optional[QCBatchRead]:
        """Get QC batch by qc_batch_id with centralized logging"""
        logger.debug(f"Looking up QC batch by qc_batch_id: {qc_batch_id}")
        qcbatch = db.query(QCBatch).filter(QCBatch.qc_batch_id == qc_batch_id).first()
        
        if not qcbatch:
            logger.warning(f"QC Batch not found: {qc_batch_id}")
            return None
        
        logger.debug(f"QC Batch found: {qcbatch.qc_batch_id} (ID: {qcbatch.id})")
        
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
    def approve_qc_batch(db: Session, qc_batch_id: str) -> bool:
        """Approve QC batch and emit approval event"""
        qcbatch = db.query(QCBatch).filter(QCBatch.qc_batch_id == qc_batch_id).first()
        
        if not qcbatch:
            logger.warning(f"QC Batch approval failed - not found: {qc_batch_id}")
            return False
        
        # Set approval time
        qcbatch.qc_batch_end_time = datetime.utcnow()
        qcbatch.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ QC Batch approved: {qcbatch.qc_batch_id} (ID: {qcbatch.id})")
        
        # Emit QC batch approval event
        event_bus.publish_event(EventType.QC_BATCH_APPROVED, {
            "qc_batch_id": str(qcbatch.id),
            "qc_batch_number": qcbatch.qc_batch_id,
            "approval_time": qcbatch.qc_batch_end_time.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True

    @staticmethod
    def reject_qc_batch(db: Session, qc_batch_id: str, reason: str) -> bool:
        """Reject QC batch and emit rejection event"""
        qcbatch = db.query(QCBatch).filter(QCBatch.qc_batch_id == qc_batch_id).first()
        
        if not qcbatch:
            logger.warning(f"QC Batch rejection failed - not found: {qc_batch_id}")
            return False
        
        # Set rejection time
        qcbatch.qc_batch_end_time = datetime.utcnow()
        qcbatch.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"❌ QC Batch rejected: {qcbatch.qc_batch_id} (ID: {qcbatch.id}) - Reason: {reason}")
        
        # Emit QC batch rejection event
        event_bus.publish_event(EventType.QC_BATCH_REJECTED, {
            "qc_batch_id": str(qcbatch.id),
            "qc_batch_number": qcbatch.qc_batch_id,
            "rejection_time": qcbatch.qc_batch_end_time.isoformat(),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True

    @staticmethod
    def list_qc_batches(db: Session, skip: int = 0, limit: int = 100) -> list[QCBatchRead]:
        """List QC batches with pagination"""
        logger.debug(f"Listing QC batches (skip={skip}, limit={limit})")
        qcbatches = db.query(QCBatch).offset(skip).limit(limit).all()
        
        return [
            QCBatchRead(
                id=qcbatch.id,
                qc_batch_id=qcbatch.qc_batch_id,
                date_time=qcbatch.date_time,
                product=qcbatch.product,
                location=qcbatch.location,
                process=qcbatch.process,
                process_step=qcbatch.process_step,
                qc_batch_end_time=qcbatch.qc_batch_end_time,
            )
            for qcbatch in qcbatches
        ]

    @staticmethod
    def get_qc_batches_by_status(db: Session, approved: bool = True) -> list[QCBatchRead]:
        """Get QC batches by approval status"""
        logger.debug(f"Looking up QC batches by status: {'approved' if approved else 'pending'}")
        
        if approved:
            qcbatches = db.query(QCBatch).filter(QCBatch.qc_batch_end_time.isnot(None)).all()
        else:
            qcbatches = db.query(QCBatch).filter(QCBatch.qc_batch_end_time.is_(None)).all()
        
        return [
            QCBatchRead(
                id=qcbatch.id,
                qc_batch_id=qcbatch.qc_batch_id,
                date_time=qcbatch.date_time,
                product=qcbatch.product,
                location=qcbatch.location,
                process=qcbatch.process,
                process_step=qcbatch.process_step,
                qc_batch_end_time=qcbatch.qc_batch_end_time,
            )
            for qcbatch in qcbatches
        ]