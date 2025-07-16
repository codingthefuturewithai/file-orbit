#!/usr/bin/env python
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Job, Endpoint, TransferTemplate
from datetime import datetime, timedelta

async def check_chain_jobs():
    async with AsyncSessionLocal() as db:
        # Find recent parent job
        parent_jobs = await db.execute(
            select(Job)
            .filter(Job.parent_job_id.is_(None))
            .filter(Job.created_at > datetime.utcnow() - timedelta(hours=24))
            .order_by(Job.created_at.desc())
            .limit(1)
        )
        parent_job = parent_jobs.scalar_one_or_none()
        
        if parent_job:
            print(f'Parent Job: {parent_job.id}')
            print(f'Status: {parent_job.status}')
            print(f'Source: {parent_job.source_path}')
            print(f'Dest: {parent_job.destination_path}')
            print(f'Source Endpoint ID: {parent_job.source_endpoint_id}')
            print(f'Dest Endpoint ID: {parent_job.destination_endpoint_id}')
            print()
            
            # Find chain jobs
            chain_jobs = await db.execute(
                select(Job)
                .filter(Job.parent_job_id == parent_job.id)
                .order_by(Job.created_at)
            )
            
            for job in chain_jobs.scalars():
                print(f'\nChain Job: {job.id}')
                print(f'Status: {job.status}')
                print(f'Source: {job.source_path}')
                print(f'Dest: {job.destination_path}')
                print(f'Source Endpoint: {job.source_endpoint_id}')
                print(f'Dest Endpoint: {job.destination_endpoint_id}')
                
                # Get endpoint details
                source_endpoint = await db.execute(
                    select(Endpoint).filter(Endpoint.id == job.source_endpoint_id)
                )
                source_ep = source_endpoint.scalar_one_or_none()
                if source_ep:
                    print(f'Source Endpoint Name: {source_ep.name}')
                    print(f'Source Endpoint Type: {source_ep.type}')
                    
                dest_endpoint = await db.execute(
                    select(Endpoint).filter(Endpoint.id == job.destination_endpoint_id)
                )
                dest_ep = dest_endpoint.scalar_one_or_none()
                if dest_ep:
                    print(f'Dest Endpoint Name: {dest_ep.name}')
                    print(f'Dest Endpoint Type: {dest_ep.type}')
                    print(f'Dest Endpoint Config: {dest_ep.config}')
                print('---')
                
        # Check transfers for the parent job
        if parent_job:
            print("\n\nTransfers for parent job:")
            from app.models import Transfer
            transfers = await db.execute(
                select(Transfer).filter(Transfer.job_id == parent_job.id)
            )
            for transfer in transfers.scalars():
                print(f'\nTransfer ID: {transfer.id}')
                print(f'File Name: {transfer.file_name}')
                print(f'File Path: {transfer.file_path}')
                print(f'Destination Path: {transfer.destination_path}')
                print(f'Status: {transfer.status}')
                
        # Also check chain rules
        print("\n\nTransfer Templates with Chain Rules:")
        templates = await db.execute(
            select(TransferTemplate).filter(TransferTemplate.chain_rules.isnot(None))
        )
        for template in templates.scalars():
            print(f'\nTemplate: {template.name} (ID: {template.id})')
            print(f'Chain Rules: {template.chain_rules}')

if __name__ == "__main__":
    asyncio.run(check_chain_jobs())