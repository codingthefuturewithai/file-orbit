from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.transfer_template import TransferTemplate, EventType
from app.models.job import Job, JobType, JobStatus
from app.schemas.transfer_template import TransferTemplateCreate, TransferTemplateUpdate, TransferTemplateResponse
from app.schemas.job import JobCreate, JobResponse
from app.services.chain_job_service import ChainJobService
from app.services.redis_manager import redis_manager

router = APIRouter()


@router.get("/", response_model=List[TransferTemplateResponse])
async def list_transfer_templates(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[EventType] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all transfer templates with optional filtering"""
    query = select(TransferTemplate)
    
    if event_type is not None:
        query = query.where(TransferTemplate.event_type == event_type)
    if is_active is not None:
        query = query.where(TransferTemplate.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    return templates


@router.get("/{template_id}", response_model=TransferTemplateResponse)
async def get_transfer_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transfer template by ID"""
    result = await db.execute(
        select(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer template with id {template_id} not found"
        )
    
    return template


@router.post("/", response_model=TransferTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer_template(
    template: TransferTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new transfer template"""
    # Verify endpoints exist
    from app.models.endpoint import Endpoint
    
    # Check source endpoint
    source = await db.execute(
        select(Endpoint).where(Endpoint.id == template.source_endpoint_id)
    )
    if not source.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source endpoint {template.source_endpoint_id} not found"
        )
    
    # Check destination endpoint
    dest = await db.execute(
        select(Endpoint).where(Endpoint.id == template.destination_endpoint_id)
    )
    if not dest.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destination endpoint {template.destination_endpoint_id} not found"
        )
    
    # Check chain rule endpoints
    if template.chain_rules:
        for chain_rule in template.chain_rules:
            chain_endpoint = await db.execute(
                select(Endpoint).where(Endpoint.id == chain_rule.endpoint_id)
            )
            if not chain_endpoint.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Chain endpoint {chain_rule.endpoint_id} not found"
                )
    
    # Create new transfer template
    template_data = template.model_dump()
    db_template = TransferTemplate(
        id=str(uuid.uuid4()),
        **template_data
    )
    
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    
    return db_template


@router.put("/{template_id}", response_model=TransferTemplateResponse)
async def update_transfer_template(
    template_id: str,
    template_update: TransferTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing transfer template"""
    # Get existing template
    result = await db.execute(
        select(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    db_template = result.scalar_one_or_none()
    
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer template with id {template_id} not found"
        )
    
    # Update fields
    update_data = template_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        await db.execute(
            update(TransferTemplate)
            .where(TransferTemplate.id == template_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Refresh to get updated data
        await db.refresh(db_template)
    
    return db_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transfer_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an transfer template"""
    # Check if template exists
    result = await db.execute(
        select(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer template with id {template_id} not found"
        )
    
    # Delete template
    await db.execute(
        delete(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    await db.commit()
    
    return None


@router.post("/{template_id}/toggle", response_model=TransferTemplateResponse)
async def toggle_transfer_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Toggle an transfer template's active status"""
    result = await db.execute(
        select(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer template with id {template_id} not found"
        )
    
    # Toggle active status
    template.is_active = not template.is_active
    template.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(template)
    
    return template


@router.post("/{template_id}/execute", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def execute_transfer_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Execute a transfer template, creating a job and any associated chain jobs"""
    # Get the template
    result = await db.execute(
        select(TransferTemplate).where(TransferTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer template with id {template_id} not found"
        )
    
    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer template {template.name} is not active"
        )
    
    # Create the primary job from the template
    job_data = JobCreate(
        name=f"{template.name} - Manual",
        type=JobType.MANUAL,
        source_endpoint_id=template.source_endpoint_id,
        source_path=template.source_config.get('path', ''),  # For manual execution, use the base path
        destination_endpoint_id=template.destination_endpoint_id,
        destination_path=template.destination_path_template.replace('{filename}', '*'),  # Simple substitution for now
        file_pattern=template.file_pattern or '*',
        delete_source_after_transfer=template.delete_source_after_transfer,
        is_active=True,
        config={
            'transfer_template_id': template.id,
            'transfer_template_name': template.name,
            'manual_execution': True
        }
    )
    
    # Create the job
    job = Job(
        id=str(uuid.uuid4()),
        **job_data.model_dump(),
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Create chain jobs if template has chain rules
    chain_jobs = []
    if template.chain_rules:
        chain_jobs = await ChainJobService.create_chain_jobs(job, template.chain_rules, db)
    
    # Queue the primary job for execution
    await redis_manager.enqueue_job(job.id)
    
    # Update template statistics
    template.total_triggers += 1
    template.last_triggered = datetime.now(timezone.utc)
    await db.commit()
    
    # Include chain job info in response
    job_response = JobResponse.model_validate(job)
    if chain_jobs:
        job_response.config = job_response.config or {}
        job_response.config['chain_job_ids'] = [cj.id for cj in chain_jobs]
        job_response.config['chain_job_count'] = len(chain_jobs)
    
    return job_response