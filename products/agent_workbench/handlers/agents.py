# -*- coding: utf-8 -*-
"""
Agent Workbench - Agents Handler (Admin)

Endpoints:
- GET /agents - List agents (admin)
- GET /agents/available - Get available agents for transfer
- POST /agents - Create agent (admin)
- PUT /agents/{username} - Update agent (admin)
- PUT /agents/{agent_id}/skills - Update agent skills (admin)
- DELETE /agents/{username} - Delete agent (admin)
- POST /agents/{username}/reset-password - Reset password (admin)
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from infrastructure.security.agent_auth import (
    AgentManager, Agent, AgentStatus, AgentRole, agent_to_dict,
    CreateAgentRequest, UpdateAgentRequest, ResetPasswordRequest,
    UpdateAgentSkillsRequest, PasswordHasher, validate_password
)

from products.agent_workbench.dependencies import (
    get_agent_manager, require_agent, require_admin
)


router = APIRouter(prefix="/agents", tags=["Agents Admin"])


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("")
async def get_agents_list(
    status: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """List all agents (admin only)"""
    agent_manager = get_agent_manager()

    agents = agent_manager.get_all_agents()

    if status:
        agents = [a for a in agents if a.status.value == status]
    if role:
        agents = [a for a in agents if a.role.value == role]

    agents.sort(key=lambda x: x.created_at, reverse=True)

    total = len(agents)
    start = (page - 1) * page_size
    end = start + page_size
    items = agents[start:end]

    items_dict = []
    for agent in items:
        data = agent.dict()
        data.pop("password_hash", None)
        items_dict.append(data)

    return {
        "success": True,
        "data": {
            "items": items_dict,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/available")
async def get_available_agents(agent: Dict[str, Any] = Depends(require_agent)):
    """Get available agents for session transfer"""
    agent_manager = get_agent_manager()

    all_agents = agent_manager.get_all_agents()
    current_agent_id = agent.get("agent_id")
    available = []

    for a in all_agents:
        if a.id != current_agent_id and a.status == AgentStatus.ONLINE:
            available.append({
                "id": a.id,
                "username": a.username,
                "name": a.name,
                "status": a.status.value,
                "role": a.role.value,
                "max_sessions": a.max_sessions
            })

    status_priority = {
        'online': 1, 'busy': 2, 'break': 3,
        'lunch': 4, 'training': 5, 'offline': 6
    }
    available.sort(key=lambda x: status_priority.get(x['status'], 99))

    return {
        "success": True,
        "data": {"items": available, "total": len(available)}
    }


@router.post("")
async def create_agent(
    request: CreateAgentRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Create new agent (admin only)"""
    agent_manager = get_agent_manager()

    if agent_manager.get_agent_by_username(request.username):
        raise HTTPException(
            status_code=400,
            detail="USERNAME_EXISTS: Username already exists"
        )

    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail="INVALID_PASSWORD: Password must be at least 8 characters with letters and numbers"
        )

    agent = agent_manager.create_agent(
        username=request.username,
        password=request.password,
        name=request.name,
        role=request.role,
        max_sessions=request.max_sessions
    )

    if request.avatar_url:
        agent.avatar_url = request.avatar_url
        agent_manager.update_agent(agent)

    agent_dict = agent.dict()
    agent_dict.pop("password_hash", None)

    print(f"Created agent: {agent.username} (role: {agent.role.value})")

    return {"success": True, "agent": agent_dict}


@router.put("/{username}")
async def update_agent(
    username: str,
    request: UpdateAgentRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Update agent info (admin only)"""
    agent_manager = get_agent_manager()

    agent = agent_manager.get_agent_by_username(username)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail="AGENT_NOT_FOUND: Agent not found"
        )

    if request.role == AgentRole.AGENT and agent.role == AgentRole.ADMIN:
        if agent_manager.count_admins() <= 1:
            raise HTTPException(
                status_code=400,
                detail="LAST_ADMIN: Cannot demote the last admin"
            )

    if request.name is not None:
        agent.name = request.name
    if request.role is not None:
        agent.role = request.role
    if request.max_sessions is not None:
        agent.max_sessions = request.max_sessions
    if request.status is not None:
        agent.status = request.status
    if request.avatar_url is not None:
        agent.avatar_url = request.avatar_url

    agent_manager.update_agent(agent)

    agent_dict = agent.dict()
    agent_dict.pop("password_hash", None)

    print(f"Updated agent: {username}")

    return {"success": True, "agent": agent_dict}


@router.put("/{agent_id}/skills")
async def update_agent_skills_endpoint(
    agent_id: str,
    request: UpdateAgentSkillsRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Update agent skills (admin only)"""
    agent_manager = get_agent_manager()

    agent = agent_manager.get_agent_by_id(agent_id)
    if not agent:
        agent = agent_manager.get_agent_by_username(agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="AGENT_NOT_FOUND: Agent not found"
        )

    agent.skills = request.skills
    agent_manager.update_agent(agent)

    agent_dict = agent_to_dict(agent)

    print(f"Updated agent skills: {agent.username} ({len(agent.skills)} skills)")

    return {"success": True, "agent": agent_dict}


@router.delete("/{username}")
async def delete_agent(
    username: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Delete agent (admin only)"""
    agent_manager = get_agent_manager()

    agent = agent_manager.get_agent_by_username(username)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail="AGENT_NOT_FOUND: Agent not found"
        )

    if agent.role == AgentRole.ADMIN and agent_manager.count_admins() <= 1:
        raise HTTPException(
            status_code=400,
            detail="LAST_ADMIN: Cannot delete the last admin"
        )

    result = agent_manager.delete_agent(username)
    if not result:
        raise HTTPException(status_code=500, detail="Delete failed")

    print(f"Deleted agent: {username}")

    return {"success": True, "message": f"Agent {username} deleted"}


@router.post("/{username}/reset-password")
async def reset_agent_password(
    username: str,
    request: ResetPasswordRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Reset agent password (admin only)"""
    agent_manager = get_agent_manager()

    agent = agent_manager.get_agent_by_username(username)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail="AGENT_NOT_FOUND: Agent not found"
        )

    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="INVALID_PASSWORD: Password must be at least 8 characters with letters and numbers"
        )

    agent.password_hash = PasswordHasher.hash_password(request.new_password)
    agent_manager.update_agent(agent)

    print(f"Reset password for agent: {username}")

    return {"success": True, "message": "Password reset successfully"}
