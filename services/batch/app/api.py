from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .models import BatchCreate, BatchRead, QCBatchCreate, QCBatchRead
from .batches import BatchService
from .qcbatches import QCBatchService
from .db import get_db

router = APIRouter()

# CRUD for batches
@router.post("/batches/", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db)):
    return BatchService.create_batch(db, payload)

@router.get("/batches/{batch_id}", response_model=BatchRead)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    return BatchService.get_batch(db, batch_id)

# CRUD for QC batches
@router.post("/qc-batches/", response_model=QCBatchRead, status_code=status.HTTP_201_CREATED)
def create_qcbatch(payload: QCBatchCreate, db: Session = Depends(get_db)):
    return QCBatchService.create_qc_batch(db, payload)

@router.get("/qc-batches/{qc_batch_id}", response_model=QCBatchRead)
def get_qcbatch(qc_batch_id: str, db: Session = Depends(get_db)):
    return QCBatchService.get_qc_batch(db, qc_batch_id)

@router.get("/healthz")
def healthz():
    return {"status": "ok"}
