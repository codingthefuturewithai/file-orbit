from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.transfer import Transfer, TransferStatus
from app.models.job import Job, JobStatus

router = APIRouter()


@router.get("/")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get overall system statistics"""
    # Get job counts by status
    result = await db.execute(
        select(
            Job.status,
            func.count(Job.id).label("count")
        )
        .group_by(Job.status)
    )
    status_counts = {row.status: row.count for row in result}
    
    total = sum(status_counts.values())
    completed = status_counts.get(JobStatus.COMPLETED, 0)
    failed = status_counts.get(JobStatus.FAILED, 0)
    active = status_counts.get(JobStatus.RUNNING, 0) + status_counts.get(JobStatus.QUEUED, 0)
    
    success_rate = 0
    if total > 0 and (completed + failed) > 0:
        success_rate = (completed / (completed + failed)) * 100
    
    return {
        "totalTransfers": total,
        "activeTransfers": active,
        "failedTransfers": failed,
        "successRate": success_rate
    }