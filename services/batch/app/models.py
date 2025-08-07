from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class BatchCreate(BaseModel):
    batch_id: str
    date_time: datetime
    product: str
    location: str
    process: str
    process_step: str
    qc_batch_id: Optional[str]
    process_batch_end_date: Optional[datetime] = None

class BatchRead(BatchCreate):
    id: UUID

class QCBatchCreate(BaseModel):
    qc_batch_id: str
    date_time: datetime
    product: str
    location: str
    process: str
    process_step: str
    qc_batch_end_time: Optional[datetime] = None

class QCBatchRead(QCBatchCreate):
    id: UUID
