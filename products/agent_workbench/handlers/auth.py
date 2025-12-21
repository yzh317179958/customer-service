# -*- coding: utf-8 -*-
"""
Agent Workbench - Auth Handler

Endpoints:
- POST /agent/login - Agent login
- POST /agent/logout - Agent logout
- GET /agent/profile - Get agent profile
- GET /agent/status - Get agent status
- PUT /agent/status - Update agent status
- POST /agent/refresh - Refresh token
- POST /agent/change-password - Change password
- PUT /agent/profile - Update profile
"""
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from infrastructure.security.agent_auth import (
    AgentManager,
    AgentTokenManager,
    Agent,
    AgentStatus,
    LoginRequest,
    LoginResponse,
    agent_to_dict,
    ChangePasswordRequest,
    UpdateProfileRequest,
    PasswordHasher,
    validate_password,
)
from services.session.state import SessionStatus

from products.agent_workbench.dependencies import (
    get_agent_manager, get_agent_token_manager, get_session_store,
    require_agent
)


# ============================================================================
# Request Models
# ============================================================================

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UpdateAgentStatusRequest(BaseModel):
    """Agent status update request"""
    status: AgentStatus
    status_note: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Status note (optional)"
    )

# Config
AGENT_AUTO_BUSY_SECONDS = int(os.getenv("AGENT_AUTO_BUSY_SECONDS", "300"))

router = APIRouter(prefix="/agent", tags=["Agent Auth"])


# ============================================================================
# Helper Functions
# ============================================================================

def _agent_stats_key(agent_identifier: str) -> str:
    """Build Redis key for agent daily stats"""
    date_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"agent_stats:{agent_identifier}:{date_key}"


def _parse_float(value: Optional[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: Optional[str]) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _load_agent_stats(agent_identifier: str) -> Dict[str, Any]:
    """Load agent daily stats from Redis"""
    try:
        agent_manager = get_agent_manager()
    except RuntimeError:
        return {}

    if not hasattr(agent_manager, "redis"):
        return {}
    redis_client = getattr(agent_manager, "redis", None)
    if not redis_client:
        return {}
    key = _agent_stats_key(agent_identifier)
    try:
        return redis_client.hgetall(key) or {}
    except Exception as exc:
        print(f"Warning: Failed to load agent stats: {exc}")
        return {}


def _compose_today_stats(agent_identifier: str) -> Dict[str, Any]:
    """Compose today's stats for agent"""
    raw = _load_agent_stats(agent_identifier)
    total_response = _parse_float(raw.get("total_response_time"))
    response_samples = _parse_int(raw.get("response_samples"))
    total_duration = _parse_float(raw.get("total_duration"))
    duration_samples = _parse_int(raw.get("duration_samples"))
    satisfaction_total = _parse_float(raw.get("satisfaction_total"))
    satisfaction_samples = _parse_int(raw.get("satisfaction_samples"))
    processed = _parse_int(raw.get("processed_count"))

    avg_response = total_response / response_samples if response_samples else 0.0
    avg_duration = total_duration / duration_samples if duration_samples else 0.0
    satisfaction = satisfaction_total / satisfaction_samples if satisfaction_samples else 0.0

    return {
        "processed_count": processed,
        "avg_response_time": round(avg_response, 2),
        "avg_duration": round(avg_duration, 2),
        "satisfaction_score": round(satisfaction, 2)
    }


async def _count_agent_live_sessions(agent_identifier: str) -> int:
    """Count agent's current live sessions"""
    try:
        session_store = get_session_store()
    except RuntimeError:
        return 0

    try:
        live_sessions = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=500
        )
        return sum(
            1
            for session in live_sessions
            if session.assigned_agent and session.assigned_agent.id == agent_identifier
        )
    except Exception as exc:
        print(f"Warning: Failed to count live sessions: {exc}")
        return 0


async def _build_agent_status_payload(agent_obj: Agent, agent_identifier: str) -> Dict[str, Any]:
    """Build status payload for frontend"""
    today_stats = _compose_today_stats(agent_identifier)
    current_sessions = await _count_agent_live_sessions(agent_identifier)
    return {
        "status": agent_obj.status.value if isinstance(agent_obj.status, AgentStatus) else agent_obj.status,
        "status_note": agent_obj.status_note or "",
        "status_updated_at": agent_obj.status_updated_at,
        "last_active_at": agent_obj.last_active_at,
        "current_sessions": current_sessions,
        "max_sessions": agent_obj.max_sessions,
        "today_stats": today_stats
    }


def _auto_adjust_agent_status(agent_obj: Agent) -> Agent:
    """Auto-adjust agent status based on last active time"""
    try:
        agent_manager = get_agent_manager()
    except RuntimeError:
        return agent_obj

    last_active = agent_obj.last_active_at or 0
    now = time.time()
    if (
        agent_obj.status == AgentStatus.ONLINE
        and AGENT_AUTO_BUSY_SECONDS > 0
        and now - last_active > AGENT_AUTO_BUSY_SECONDS
    ):
        agent_obj.status = AgentStatus.BUSY
        if not agent_obj.status_note:
            agent_obj.status_note = "System detected no activity for 5+ minutes, auto-set to busy"
        agent_obj.status_updated_at = now
        try:
            agent_manager.update_agent(agent_obj)
        except Exception as exc:
            print(f"Warning: Failed to auto-update agent status: {exc}")
    return agent_obj


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/login")
async def agent_login(request: LoginRequest):
    """
    Agent login endpoint

    Returns:
        LoginResponse with token, refresh_token, expires_in, agent info
    """
    try:
        agent_manager = get_agent_manager()
        agent_token_manager = get_agent_token_manager()

        # Authenticate
        agent = agent_manager.authenticate(
            username=request.username,
            password=request.password
        )

        if not agent:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        # Generate tokens
        access_token = agent_token_manager.create_access_token(agent)
        refresh_token = agent_token_manager.create_refresh_token(agent)

        return LoginResponse(
            success=True,
            token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            agent=agent_to_dict(agent)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Agent login failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def agent_logout(username: str):
    """
    Agent logout endpoint
    """
    try:
        agent_manager = get_agent_manager()
        agent_manager.update_status(username, AgentStatus.OFFLINE)

        return {
            "success": True,
            "message": "Logout successful"
        }

    except Exception as e:
        print(f"Error: Agent logout failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/profile")
async def get_agent_profile(username: str):
    """
    Get agent profile
    """
    try:
        agent_manager = get_agent_manager()
        agent = agent_manager.get_agent_by_username(username)

        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )

        return {
            "success": True,
            "agent": agent_to_dict(agent)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Get agent profile failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Get profile failed: {str(e)}"
        )


@router.get("/status")
async def get_agent_status(agent: Dict[str, Any] = Depends(require_agent)):
    """Get current agent status"""
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        current_agent = _auto_adjust_agent_status(current_agent)
        payload = await _build_agent_status_payload(current_agent, username)

        return {
            "success": True,
            "data": payload
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error: Get agent status failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.put("/status")
async def update_agent_status_api(
    request: UpdateAgentStatusRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """Update agent status"""
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        updated_agent = agent_manager.update_status(
            username=username,
            status=request.status,
            status_note=request.status_note
        )

        if not updated_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        payload = await _build_agent_status_payload(updated_agent, username)
        return {
            "success": True,
            "data": payload
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error: Update agent status failed: {exc}")
        raise HTTPException(status_code=500, detail="Update failed")


@router.post("/refresh")
async def refresh_agent_token(request: RefreshTokenRequest):
    """
    Refresh access token
    """
    try:
        agent_manager = get_agent_manager()
        agent_token_manager = get_agent_token_manager()

        # Verify refresh token
        payload = agent_token_manager.verify_token(request.refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        # Get agent info
        username = payload.get("username")
        agent = agent_manager.get_agent_by_username(username)

        if not agent:
            raise HTTPException(
                status_code=401,
                detail="Agent not found"
            )

        # Generate new access token
        new_access_token = agent_token_manager.create_access_token(agent)

        return {
            "success": True,
            "token": new_access_token,
            "expires_in": 3600
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Refresh token failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Refresh failed: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """
    Change own password
    """
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: Agent not found"
            )

        # Verify old password
        if not PasswordHasher.verify_password(request.old_password, current_agent.password_hash):
            raise HTTPException(
                status_code=400,
                detail="OLD_PASSWORD_INCORRECT: Old password incorrect"
            )

        # Validate new password strength
        if not validate_password(request.new_password):
            raise HTTPException(
                status_code=400,
                detail="INVALID_PASSWORD: Password must be at least 8 characters with letters and numbers"
            )

        # Verify new password is different
        if PasswordHasher.verify_password(request.new_password, current_agent.password_hash):
            raise HTTPException(
                status_code=400,
                detail="PASSWORD_SAME: New password cannot be same as old password"
            )

        # Update password
        current_agent.password_hash = PasswordHasher.hash_password(request.new_password)
        agent_manager.update_agent(current_agent)

        print(f"Agent changed password: {username}")

        return {
            "success": True,
            "message": "Password changed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Change password failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Change failed: {str(e)}"
        )


@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    agent: Dict[str, Any] = Depends(require_agent)
):
    """
    Update own profile
    """
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        current_agent = agent_manager.get_agent_by_username(username)

        if not current_agent:
            raise HTTPException(
                status_code=404,
                detail="AGENT_NOT_FOUND: Agent not found"
            )

        # Check at least one field to update
        if request.name is None and request.avatar_url is None:
            raise HTTPException(
                status_code=400,
                detail="NO_FIELDS_TO_UPDATE: At least one field required"
            )

        # Update allowed fields
        if request.name is not None:
            current_agent.name = request.name

        if request.avatar_url is not None:
            current_agent.avatar_url = request.avatar_url

        agent_manager.update_agent(current_agent)

        # Return result (hide password)
        agent_dict = current_agent.dict()
        agent_dict.pop("password_hash", None)

        print(f"Agent updated profile: {username}")

        return {
            "success": True,
            "agent": agent_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: Update profile failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/status/heartbeat")
async def heartbeat_agent_status(agent: Dict[str, Any] = Depends(require_agent)):
    """Update agent heartbeat for auto status detection"""
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        last_active = agent_manager.update_last_active(username)

        return {
            "success": True,
            "last_active_at": last_active
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error: Agent heartbeat failed: {exc}")
        raise HTTPException(status_code=500, detail="Heartbeat failed")


@router.get("/stats/today")
async def get_agent_today_stats(agent: Dict[str, Any] = Depends(require_agent)):
    """Get agent today's statistics"""
    try:
        agent_manager = get_agent_manager()
        username = agent.get("username")
        today_stats = _compose_today_stats(username)
        current_sessions = await _count_agent_live_sessions(username)
        current_agent = agent_manager.get_agent_by_username(username)

        today_stats.update({
            "current_sessions": current_sessions,
            "max_sessions": current_agent.max_sessions if current_agent else 0
        })

        return {
            "success": True,
            "data": today_stats
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error: Get agent stats failed: {exc}")
        raise HTTPException(status_code=500, detail="Stats retrieval failed")
