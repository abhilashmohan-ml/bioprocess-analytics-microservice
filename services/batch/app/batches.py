from typing import Optional, List                  # ← NEW
from .db import Batch
from .models import BatchCreate, BatchRead
from sqlalchemy.orm import Session
from uuid import uuid4
import logging
import sys
from datetime import datetime

# Import centralized configuration
sys.path.append('../../..')
from shared.config import settings
from shared.event_bus import event_bus, EventType

logger = logging.getLogger(__name__)

class BatchService:
    """Batch service with centralized configuration and event emission"""
    
    @staticmethod
    def create_batch(db: Session, payload: BatchCreate) -> BatchRead:
        """Create batch with centralized validation and event emission"""
        
        # Validate batch ID format using centralized validation
        if not payload.batch_id or len(payload.batch_id.strip()) == 0:
            raise ValueError("Batch ID cannot be empty")
        
        # Sanitize batch data using centralized sanitizer
        from shared.security import security_manager
        sanitized_batch_id = security_manager.sanitize_input(payload.batch_id)
        sanitized_product = security_manager.sanitize_input(payload.product)
        sanitized_location = security_manager.sanitize_input(payload.location)
        sanitized_process = security_manager.sanitize_input(payload.process)
        sanitized_process_step = security_manager.sanitize_input(payload.process_step)
        
        # Create batch with centralized configuration
        batch = Batch(
            id=uuid4(),
            batch_id=sanitized_batch_id,
            date_time=payload.date_time,
            product=sanitized_product,
            location=sanitized_location,
            process=sanitized_process,
            process_step=sanitized_process_step,
            qc_batch_id=payload.qc_batch_id,
            process_batch_end_date=payload.process_batch_end_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch created successfully: {batch.batch_id} (ID: {batch.id})")
        
        # Emit batch creation event
        event_bus.publish_event(EventType.BATCH_CREATED, {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_id,
            "product": batch.product,
            "location": batch.location,
            "process": batch.process,
            "process_step": batch.process_step,
            "timestamp": datetime.utcnow().isoformat()
        })
        
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
    def get_batch(db: Session, batch_id: str) -> Optional[BatchRead]:
        """Get batch by batch_id with centralized logging"""
        logger.debug(f"Looking up batch by batch_id: {batch_id}")
        batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
        
        if not batch:
            logger.warning(f"Batch not found: {batch_id}")
            return None
        
        logger.debug(f"Batch found: {batch.batch_id} (ID: {batch.id})")
        
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
    def update_batch(db: Session, batch_id: str, updates: dict) -> Optional[BatchRead]:
        """Update batch with centralized validation"""
        batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
        
        if not batch:
            logger.warning(f"Update failed - batch not found: {batch_id}")
            return None
        
        # Sanitize updates using centralized sanitizer
        from shared.security import security_manager
        for key, value in updates.items():
            if isinstance(value, str):
                updates[key] = security_manager.sanitize_input(value)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(batch, key):
                setattr(batch, key, value)
        
        batch.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch updated successfully: {batch.batch_id} (ID: {batch.id})")
        
        # Emit batch update event
        event_bus.publish_event(EventType.BATCH_UPDATED, {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_id,
            "updates": list(updates.keys()),
            "timestamp": datetime.utcnow().isoformat()
        })
        
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
    def delete_batch(db: Session, batch_id: str) -> bool:
        """Delete batch (soft delete)"""
        batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
        
        if not batch:
            logger.warning(f"Delete failed - batch not found: {batch_id}")
            return False
        
        # Soft delete by setting qc_batch_id to None (breaks relationship)
        batch.qc_batch_id = None
        batch.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Batch deleted: {batch.batch_id} (ID: {batch.id})")
        
        # Emit batch deletion event
        event_bus.publish_event(EventType.BATCH_DELETED, {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True

    @staticmethod
    def list_batches(db: Session, skip: int = 0, limit: int = 100) -> list[BatchRead]:
        """List batches with pagination"""
        logger.debug(f"Listing batches (skip={skip}, limit={limit})")
        batches = db.query(Batch).offset(skip).limit(limit).all()
        
        return [
            BatchRead(
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
            for batch in batches
        ]

    @staticmethod
    def get_batches_by_product(db: Session, product: str) -> list[BatchRead]:
        """Get batches by product name"""
        logger.debug(f"Looking up batches by product: {product}")
        batches = db.query(Batch).filter(Batch.product == product).all()
        
        return [
            BatchRead(
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
            for batch in batches
        ]