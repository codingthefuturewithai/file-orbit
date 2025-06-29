from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobExecute
from app.services.redis_manager import redis_manager

router = APIRouter()


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all jobs with optional filtering"""
    query = select(Job)
    
    if status is not None:
        query = query.where(Job.status == status)
    if is_active is not None:
        query = query.where(Job.is_active == is_active)
    
    query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific job by ID"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    return job


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new job"""
    # Verify endpoints exist
    from app.models.endpoint import Endpoint
    
    source = await db.execute(
        select(Endpoint).where(Endpoint.id == job.source_endpoint_id)
    )
    if not source.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source endpoint {job.source_endpoint_id} not found"
        )
    
    dest = await db.execute(
        select(Endpoint).where(Endpoint.id == job.destination_endpoint_id)
    )
    if not dest.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destination endpoint {job.destination_endpoint_id} not found"
        )
    
    # Create new job
    db_job = Job(
        id=str(uuid.uuid4()),
        status=JobStatus.PENDING,
        **job.model_dump()
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    return db_job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing job"""
    # Get existing job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    db_job = result.scalar_one_or_none()
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    # Don't allow updates while job is running
    if db_job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update job while it is running"
        )
    
    # Update fields
    update_data = job_update.model_dump(exclude_unset=True)
    if update_data:
        from app.models.endpoint import Endpoint
        
        # Validate source endpoint if being updated
        if "source_endpoint_id" in update_data:
            source = await db.execute(
                select(Endpoint).where(Endpoint.id == update_data["source_endpoint_id"])
            )
            if not source.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Source endpoint {update_data['source_endpoint_id']} not found"
                )
        
        # Validate destination endpoint if being updated
        if "destination_endpoint_id" in update_data:
            dest = await db.execute(
                select(Endpoint).where(Endpoint.id == update_data["destination_endpoint_id"])
            )
            if not dest.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Destination endpoint {update_data['destination_endpoint_id']} not found"
                )
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Refresh to get updated data
        await db.refresh(db_job)
    
    return db_job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a job"""
    # Check if job exists
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    # Don't allow deletion while job is running
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job while it is running"
        )
    
    # Delete job
    await db.execute(
        delete(Job).where(Job.id == job_id)
    )
    await db.commit()
    
    return None


@router.post("/{job_id}/execute", response_model=dict)
async def execute_job(
    job_id: str,
    execute_params: JobExecute = JobExecute(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """Execute a job immediately"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    if not job.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not active"
        )
    
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is already running"
        )
    
    # Queue job for execution
    await redis_manager.enqueue_job(job_id)
    
    # Update job status
    job.status = JobStatus.QUEUED
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "message": "Job queued for execution",
        "job_id": job_id,
        "status": JobStatus.QUEUED.value
    }


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running job"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    if job.status not in [JobStatus.RUNNING, JobStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not running or queued (current status: {job.status.value})"
        )
    
    # TODO: Implement actual cancellation logic
    # For now, just update status
    job.status = JobStatus.CANCELLED
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "message": "Job cancelled",
        "job_id": job_id,
        "status": JobStatus.CANCELLED.value
    }


@router.put("/{job_id}/update-and-execute", response_model=dict)
async def update_and_execute_job(
    job_id: str,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a job and immediately execute it"""
    # First update the job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    db_job = result.scalar_one_or_none()
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    # Don't allow updates while job is running
    if db_job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update job while it is running"
        )
    
    # Update fields
    update_data = job_update.model_dump(exclude_unset=True)
    if update_data:
        from app.models.endpoint import Endpoint
        
        # Validate source endpoint if being updated
        if "source_endpoint_id" in update_data:
            source = await db.execute(
                select(Endpoint).where(Endpoint.id == update_data["source_endpoint_id"])
            )
            if not source.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Source endpoint {update_data['source_endpoint_id']} not found"
                )
        
        # Validate destination endpoint if being updated
        if "destination_endpoint_id" in update_data:
            dest = await db.execute(
                select(Endpoint).where(Endpoint.id == update_data["destination_endpoint_id"])
            )
            if not dest.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Destination endpoint {update_data['destination_endpoint_id']} not found"
                )
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Refresh to get updated data
        await db.refresh(db_job)
    
    # Now execute the job
    if not db_job.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not active"
        )
    
    # Queue job for execution
    await redis_manager.enqueue_job(job_id)
    
    # Update job status
    db_job.status = JobStatus.QUEUED
    db_job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "message": "Job updated and queued for execution",
        "job_id": job_id,
        "status": JobStatus.QUEUED.value
    }