from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.endpoint import Endpoint
from app.schemas.endpoint import EndpointCreate, EndpointUpdate, EndpointResponse
from app.services.rclone_service import RcloneService

router = APIRouter()
rclone_service = RcloneService()


@router.get("/", response_model=List[EndpointResponse])
async def list_endpoints(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all endpoints"""
    result = await db.execute(
        select(Endpoint).offset(skip).limit(limit)
    )
    endpoints = result.scalars().all()
    return endpoints


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific endpoint by ID"""
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint with id {endpoint_id} not found"
        )
    
    return endpoint


@router.post("/", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    endpoint: EndpointCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new endpoint"""
    # Check if endpoint with same name exists
    result = await db.execute(
        select(Endpoint).where(Endpoint.name == endpoint.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Endpoint with name '{endpoint.name}' already exists"
        )
    
    # Create new endpoint
    db_endpoint = Endpoint(
        id=str(uuid.uuid4()),
        **endpoint.model_dump()
    )
    
    # Test connection
    try:
        if await rclone_service.test_remote_connection(db_endpoint.name, db_endpoint.config):
            db_endpoint.connection_status = "connected"
            db_endpoint.last_connected = datetime.now(timezone.utc)
        else:
            db_endpoint.connection_status = "error"
    except Exception:
        db_endpoint.connection_status = "error"
    
    db.add(db_endpoint)
    await db.commit()
    await db.refresh(db_endpoint)
    
    return db_endpoint


@router.put("/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: str,
    endpoint_update: EndpointUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing endpoint"""
    # Get existing endpoint
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    db_endpoint = result.scalar_one_or_none()
    
    if not db_endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint with id {endpoint_id} not found"
        )
    
    # Check if new name conflicts
    if endpoint_update.name and endpoint_update.name != db_endpoint.name:
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == endpoint_update.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Endpoint with name '{endpoint_update.name}' already exists"
            )
    
    # Update fields
    update_data = endpoint_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.execute(
            update(Endpoint)
            .where(Endpoint.id == endpoint_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Refresh to get updated data
        await db.refresh(db_endpoint)
    
    return db_endpoint


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an endpoint"""
    # Check if endpoint exists
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint with id {endpoint_id} not found"
        )
    
    # Delete endpoint
    await db.execute(
        delete(Endpoint).where(Endpoint.id == endpoint_id)
    )
    await db.commit()
    
    return None


@router.post("/{endpoint_id}/test", response_model=dict)
async def test_endpoint_connection(
    endpoint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Test an endpoint's connection"""
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint with id {endpoint_id} not found"
        )
    
    try:
        success = await rclone_service.test_remote_connection(endpoint.name, endpoint.config)
        
        # Update connection status
        if success:
            endpoint.connection_status = "connected"
            endpoint.last_connected = datetime.now(timezone.utc)
        else:
            endpoint.connection_status = "error"
        
        await db.commit()
        
        return {
            "success": success,
            "status": endpoint.connection_status,
            "message": "Connection successful" if success else "Connection failed"
        }
    except Exception as e:
        endpoint.connection_status = "error"
        await db.commit()
        
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }