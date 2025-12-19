# -*- coding: utf-8 -*-
"""
Agent Workbench Product Module

Provides agent backend management features:
- Agent authentication and management
- Session management and takeover
- Ticket system
- Quick replies
- Template management
"""


def get_router():
    """Lazy import router to avoid circular imports"""
    from products.agent_workbench.routes import router
    return router


__all__ = ["get_router"]
