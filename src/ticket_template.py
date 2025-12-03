import json
import time
import uuid
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field

from src.ticket import TicketType, TicketPriority


class TicketTemplate(BaseModel):
    id: str
    name: str
    ticket_type: TicketType
    category: str
    priority: TicketPriority
    title_template: str
    description_template: str
    created_by: str
    created_at: float = Field(default_factory=lambda: time.time())
    updated_at: float = Field(default_factory=lambda: time.time())


class TicketTemplateStore:
    def __init__(self, redis_client: Optional["redis.Redis"] = None, max_templates: int = 200):
        self.redis = redis_client
        self.max_templates = max_templates
        self.key_prefix = "ticket_template"
        self.index_key = f"{self.key_prefix}:index"
        self._memory_store: Dict[str, str] = {} if redis_client is None else None  # type: ignore

    def _template_key(self, template_id: str) -> str:
        return f"{self.key_prefix}:{template_id}"

    def create(
        self,
        *,
        name: str,
        ticket_type: TicketType,
        category: str,
        priority: TicketPriority,
        title_template: str,
        description_template: str,
        created_by: str
    ) -> TicketTemplate:
        template = TicketTemplate(
            id=f"tmpl_{uuid.uuid4().hex[:12]}",
            name=name,
            ticket_type=ticket_type,
            category=category,
            priority=priority,
            title_template=title_template,
            description_template=description_template,
            created_by=created_by
        )
        self._save(template)
        return template

    def _save(self, template: TicketTemplate):
        template.updated_at = time.time()
        data = json.dumps(template.dict(), ensure_ascii=False)
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.set(self._template_key(template.id), data)
            pipe.sadd(self.index_key, template.id)
            pipe.execute()
        else:
            self._memory_store[template.id] = data  # type: ignore

    def list(self) -> List[TicketTemplate]:
        if self.redis:
            ids = self.redis.smembers(self.index_key) or []
            templates: List[TicketTemplate] = []
            for raw_id in ids:
                template_id = raw_id.decode("utf-8")
                data = self.redis.get(self._template_key(template_id))
                if not data:
                    continue
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                templates.append(TicketTemplate(**json.loads(data)))
            return sorted(templates, key=lambda t: t.updated_at, reverse=True)

        return sorted(
            [TicketTemplate(**json.loads(value)) for value in (self._memory_store or {}).values()],
            key=lambda t: t.updated_at,
            reverse=True
        )

    def get(self, template_id: str) -> Optional[TicketTemplate]:
        if self.redis:
            data = self.redis.get(self._template_key(template_id))
            if not data:
                return None
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return TicketTemplate(**json.loads(data))

        raw = (self._memory_store or {}).get(template_id)
        if not raw:
            return None
        return TicketTemplate(**json.loads(raw))

    def update(self, template_id: str, **updates: Any) -> Optional[TicketTemplate]:
        template = self.get(template_id)
        if not template:
            return None
        for key, value in updates.items():
            if value is None:
                continue
            if hasattr(template, key):
                setattr(template, key, value)
        self._save(template)
        return template

    def delete(self, template_id: str) -> bool:
        if self.redis:
            removed = self.redis.delete(self._template_key(template_id))
            self.redis.srem(self.index_key, template_id)
            return bool(removed)

        if self._memory_store and template_id in self._memory_store:
            del self._memory_store[template_id]
            return True
        return False

    @staticmethod
    def render(content: str, context: Dict[str, Any]) -> str:
        result = content
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", value or "")
        return result

    def render_template(self, template: TicketTemplate, context: Dict[str, Any]):
        safe_context = {
            "customer_name": context.get("customer_name", "")
        }
        return {
            "title": self.render(template.title_template, safe_context),
            "description": self.render(template.description_template, safe_context)
        }
