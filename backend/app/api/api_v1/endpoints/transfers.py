from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.transfer import Transfer, TransferStatus
from app.schemas.transfer import TransferResponse, TransferStats

router = APIRouter()


@router.get("/dashboard-stats", response_model=dict)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for the dashboard"""
    # Get transfer counts
    result = await db.execute(
        select(
            Transfer.status,
            func.count(Transfer.id).label("count")
        )
        .group_by(Transfer.status)
    )
    status_counts = {row.status: row.count for row in result}
    
    total = sum(status_counts.values())
    completed = status_counts.get(TransferStatus.COMPLETED, 0)
    failed = status_counts.get(TransferStatus.FAILED, 0)
    active = status_counts.get(TransferStatus.IN_PROGRESS, 0)
    
    success_rate = 0
    if total > 0:
        success_rate = (completed / total) * 100
    
    return {
        "totalTransfers": total,
        "activeTransfers": active,
        "failedTransfers": failed,
        "successRate": success_rate
    }


@router.get("/active", response_model=List[TransferResponse])
async def get_active_transfers(
    db: AsyncSession = Depends(get_db)
):
    """Get all currently active transfers"""
    result = await db.execute(
        select(Transfer)
        .where(Transfer.status == TransferStatus.IN_PROGRESS)
        .order_by(Transfer.started_at.desc())
    )
    transfers = result.scalars().all()
    return transfers


@router.get("/stats", response_model=TransferStats)
async def get_transfer_stats(
    hours: Optional[int] = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get transfer statistics"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get counts by status
    result = await db.execute(
        select(
            Transfer.status,
            func.count(Transfer.id).label("count")
        )
        .where(Transfer.created_at >= since)
        .group_by(Transfer.status)
    )
    status_counts = {row.status: row.count for row in result}
    
    # Get total bytes transferred
    result = await db.execute(
        select(func.sum(Transfer.bytes_transferred))
        .where(
            Transfer.created_at >= since,
            Transfer.status == TransferStatus.COMPLETED
        )
    )
    total_bytes = result.scalar() or 0
    
    # Calculate average transfer rate
    result = await db.execute(
        select(func.avg(Transfer.transfer_rate))
        .where(
            Transfer.created_at >= since,
            Transfer.status == TransferStatus.COMPLETED,
            Transfer.transfer_rate.isnot(None)
        )
    )
    avg_rate = result.scalar()
    
    return TransferStats(
        total_transfers=sum(status_counts.values()),
        active_transfers=status_counts.get(TransferStatus.IN_PROGRESS, 0),
        completed_transfers=status_counts.get(TransferStatus.COMPLETED, 0),
        failed_transfers=status_counts.get(TransferStatus.FAILED, 0),
        total_bytes_transferred=total_bytes,
        average_transfer_rate=avg_rate
    )


@router.get("/", response_model=List[TransferResponse])
async def list_transfers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TransferStatus] = None,
    job_id: Optional[str] = None,
    hours: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all transfers with optional filtering"""
    query = select(Transfer)
    
    if status is not None:
        query = query.where(Transfer.status == status)
    
    if job_id is not None:
        query = query.where(Transfer.job_id == job_id)
    
    if hours is not None:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(Transfer.created_at >= since)
    
    query = query.order_by(Transfer.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    transfers = result.scalars().all()
    return transfers


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transfer by ID"""
    result = await db.execute(
        select(Transfer).where(Transfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer with id {transfer_id} not found"
        )
    
    return transfer


@router.post("/{transfer_id}/retry", response_model=dict)
async def retry_transfer(
    transfer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed transfer"""
    result = await db.execute(
        select(Transfer).where(Transfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer with id {transfer_id} not found"
        )
    
    if transfer.status != TransferStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer is not in failed state (current status: {transfer.status.value})"
        )
    
    # Reset transfer for retry
    transfer.status = TransferStatus.PENDING
    transfer.error_message = None
    transfer.progress = 0.0
    transfer.bytes_transferred = 0
    transfer.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # TODO: Queue transfer for execution
    
    return {
        "message": "Transfer queued for retry",
        "transfer_id": transfer_id,
        "status": TransferStatus.PENDING.value
    }