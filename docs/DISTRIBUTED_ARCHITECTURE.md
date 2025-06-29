# Distributed Architecture for Cross-Server Transfers

## Executive Summary

The current MVP architecture assumes all transfers happen locally on the server hosting the UI. The production architecture must support a **centralized control plane** that can orchestrate transfers between any servers in the enterprise network.

## Current MVP Limitations

```
Current Architecture (MVP):
┌─────────────────────────────┐
│     Server A                │
│  ┌─────┐ ┌──────┐ ┌──────┐ │
│  │ UI  │ │ API  │ │Worker│ │
│  └─────┘ └──────┘ └──────┘ │
│           ↓                 │
│      Local Transfers Only   │
└─────────────────────────────┘
```

**Problems**:
- UI, API, and Worker all run on same server
- Can only transfer files accessible to that server
- Cannot orchestrate transfers between remote servers
- Each server needs its own UI instance

## Required Production Architecture

```
Target Architecture (Post-MVP):
┌─────────────────────────────┐
│   Control Plane (Server A)  │
│  ┌─────┐ ┌──────┐          │
│  │ UI  │ │ API  │          │
│  └─────┘ └──────┘          │
└───────────┬─────────────────┘
            │ Commands/Status
    ┌───────┴────────┬────────────┐
    ↓                ↓            ↓
┌─────────┐    ┌─────────┐   ┌─────────┐
│Server B │    │Server C │   │Server D │
│ ┌─────┐ │    │ ┌─────┐ │   │ ┌─────┐ │
│ │Agent│ │───>│ │Agent│ │   │ │Agent│ │
│ └─────┘ │    │ └─────┘ │   │ └─────┘ │
│  Files  │    │  Files  │   │  Files  │
└─────────┘    └─────────┘   └─────────┘
```

## Key Architectural Components

### 1. Control Plane (Central UI/API)
- **Location**: Single server or HA cluster
- **Components**:
  - Web UI for all transfer management
  - Central API for orchestration
  - Central database (PostgreSQL)
  - Message broker (RabbitMQ/Kafka)
  - Authentication/Authorization service

### 2. Transfer Agents (On Each Server)
- **Location**: Every server that participates in transfers
- **Components**:
  - Lightweight agent service
  - Local rclone installation
  - Secure communication with control plane
  - Local file system access
  - Transfer execution engine

### 3. Communication Layer
- **Requirements**:
  - Secure agent registration
  - Bidirectional communication (commands down, status up)
  - Heartbeat/health monitoring
  - Transfer progress streaming

## Use Case Examples

### Example 1: Cross-Data Center Transfer
```
User Action: From UI on Server A
Create Transfer: 
  Source: Server B:/data/videos/raw/
  Destination: Server C:/archive/processed/
  
Flow:
1. UI (Server A) → API (Server A) → Message Queue
2. Agent (Server B) receives command
3. Agent (Server B) initiates transfer to Server C
4. Progress updates flow back to UI
```

### Example 2: Cloud to Multiple On-Premise
```
User Action: From UI on Server A
Create Transfer Template:
  Source: S3://bucket/new-videos/
  Destinations: 
    - Server B:/primary/storage/
    - Server D:/backup/storage/
  
Flow:
1. S3 event triggers control plane
2. Control plane sends commands to Server B agent
3. Server B pulls from S3
4. On completion, Server B transfers to Server D
```

## Implementation Approach

### Phase 1: Agent Communication Framework
```python
# Agent Service (runs on each server)
class TransferAgent:
    def __init__(self, agent_id: str, control_plane_url: str):
        self.agent_id = agent_id
        self.control_plane = control_plane_url
        self.rclone = RcloneService()
        
    async def register(self):
        """Register with control plane"""
        payload = {
            "agent_id": self.agent_id,
            "hostname": socket.gethostname(),
            "capabilities": self.get_capabilities(),
            "endpoints": self.scan_local_endpoints()
        }
        await self.send_to_control_plane("/agents/register", payload)
    
    async def process_transfer_command(self, command: dict):
        """Execute transfer command from control plane"""
        if command["source_agent"] == self.agent_id:
            # This agent is the source
            await self.execute_push_transfer(command)
        elif command["dest_agent"] == self.agent_id:
            # This agent is the destination
            await self.execute_pull_transfer(command)
```

### Phase 2: Control Plane API Extensions
```python
# New API endpoints for distributed control
@router.post("/agents/register")
async def register_agent(agent: AgentRegistration):
    """Register new transfer agent"""
    
@router.get("/agents")
async def list_agents():
    """List all registered agents and their status"""
    
@router.post("/transfers/distributed")
async def create_distributed_transfer(transfer: DistributedTransfer):
    """Create transfer between two remote agents"""
    # Validates both agents are online
    # Sends command to source agent
    # Monitors progress through message queue
```

### Phase 3: UI Enhancements
- Agent selector dropdowns in transfer creation
- Agent health status dashboard
- Cross-server transfer monitoring
- Agent management (register, remove, update)

## Security Considerations

### Agent Authentication
- **mTLS**: Mutual TLS between agents and control plane
- **API Keys**: Unique keys per agent
- **JWT Tokens**: Short-lived tokens for commands

### Authorization
- **RBAC**: Who can initiate transfers between which servers
- **Path Restrictions**: Limit accessible paths per agent
- **Transfer Policies**: Enforce business rules

### Network Security
- **VPN/Private Network**: Agents communicate over secure network
- **Firewall Rules**: Whitelist control plane IPs
- **Encrypted Transfers**: TLS for all communications

## Database Schema Changes

### New Tables Required
```sql
-- Transfer agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    hostname VARCHAR(255),
    ip_address INET,
    status VARCHAR(50),
    last_heartbeat TIMESTAMP,
    capabilities JSONB,
    registered_at TIMESTAMP
);

-- Distributed transfers table
CREATE TABLE distributed_transfers (
    id UUID PRIMARY KEY,
    source_agent_id UUID REFERENCES agents(id),
    dest_agent_id UUID REFERENCES agents(id),
    source_path VARCHAR(1024),
    dest_path VARCHAR(1024),
    status VARCHAR(50),
    created_by VARCHAR(255),
    created_at TIMESTAMP
);
```

## Migration Path from MVP

### Step 1: Current MVP (Local Only)
- Everything runs on single server
- Transfers limited to local paths

### Step 2: Agent Mode (Hybrid)
- Add agent service alongside existing worker
- Existing transfers continue to work
- New distributed transfers available

### Step 3: Full Distribution
- Separate control plane from agents
- All transfers go through agent framework
- Deprecate local-only mode

## Benefits of Distributed Architecture

1. **Centralized Management**: Single pane of glass for all transfers
2. **Scalability**: Add new servers without deploying full stack
3. **Flexibility**: Transfer between any connected servers
4. **Security**: Centralized auth and audit logging
5. **Efficiency**: Direct server-to-server transfers
6. **Resilience**: Control plane failure doesn't stop in-progress transfers

## Technical Challenges

1. **Network Complexity**: Agents must reach each other
2. **Firewall Rules**: Many ports/connections to manage
3. **Error Handling**: More failure points
4. **Progress Tracking**: Aggregating from multiple sources
5. **Consistency**: Ensuring distributed state consistency

## Recommended Technology Stack

### Message Queue Options
1. **RabbitMQ**: Good for command/control patterns
2. **Apache Kafka**: Better for high-volume event streaming
3. **Redis Streams**: Simpler but less feature-rich

### Agent Communication
1. **gRPC**: Efficient binary protocol with streaming
2. **WebSockets**: For real-time updates
3. **REST + SSE**: Simpler but less efficient

### Service Discovery
1. **Consul**: Dynamic service registry
2. **etcd**: Distributed configuration
3. **DNS-based**: Simpler but less dynamic