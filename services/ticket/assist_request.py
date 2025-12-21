"""
协助请求模块 (Assist Request Module)

支持坐席之间请求协助，无需转接会话。
坐席A遇到问题时，可以请求坐席B提供帮助，坐席B回复后，坐席A继续处理会话。

功能需求详见: prd/04_任务拆解/L1-1-Part3_协作与工作台优化.md
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum


class AssistStatus(str, Enum):
    """协助请求状态"""
    PENDING = "pending"      # 待处理
    ANSWERED = "answered"    # 已回复


class AssistRequest(BaseModel):
    """协助请求数据模型"""
    id: str                           # 请求ID
    session_name: str                 # 会话ID
    requester: str                    # 请求者（坐席username）
    assistant: str                    # 协助者（坐席username）
    question: str                     # 请求内容
    answer: Optional[str] = None      # 回复内容
    status: AssistStatus              # 状态
    created_at: float                 # 创建时间（UNIX时间戳）
    answered_at: Optional[float] = None  # 回复时间


class CreateAssistRequestRequest(BaseModel):
    """创建协助请求的请求模型"""
    session_name: str    # 会话ID
    assistant: str       # 协助者username
    question: str        # 请求内容


class AnswerAssistRequestRequest(BaseModel):
    """回复协助请求的请求模型"""
    answer: str          # 回复内容


class AssistRequestStore:
    """
    协助请求存储（内存实现）

    生产环境应使用 Redis 或数据库持久化
    """

    def __init__(self):
        self.requests: Dict[str, AssistRequest] = {}  # {request_id: AssistRequest}
        self.session_requests: Dict[str, List[str]] = {}  # {session_name: [request_ids]}
        self.agent_requests: Dict[str, List[str]] = {}  # {assistant: [request_ids]}

    def create(self, request: AssistRequest) -> AssistRequest:
        """创建协助请求"""
        self.requests[request.id] = request

        # 索引：会话 -> 请求列表
        if request.session_name not in self.session_requests:
            self.session_requests[request.session_name] = []
        self.session_requests[request.session_name].append(request.id)

        # 索引：协助者 -> 请求列表
        if request.assistant not in self.agent_requests:
            self.agent_requests[request.assistant] = []
        self.agent_requests[request.assistant].append(request.id)

        return request

    def get(self, request_id: str) -> Optional[AssistRequest]:
        """获取单个协助请求"""
        return self.requests.get(request_id)

    def get_by_session(self, session_name: str) -> List[AssistRequest]:
        """获取会话的所有协助请求"""
        request_ids = self.session_requests.get(session_name, [])
        return [self.requests[rid] for rid in request_ids if rid in self.requests]

    def get_by_assistant(self, assistant: str, status: Optional[AssistStatus] = None) -> List[AssistRequest]:
        """
        获取协助者收到的协助请求

        Args:
            assistant: 协助者username
            status: 可选的状态过滤（pending/answered）
        """
        request_ids = self.agent_requests.get(assistant, [])
        requests = [self.requests[rid] for rid in request_ids if rid in self.requests]

        if status:
            requests = [r for r in requests if r.status == status]

        # 按创建时间倒序排列（最新的在前）
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests

    def get_by_requester(self, requester: str, status: Optional[AssistStatus] = None) -> List[AssistRequest]:
        """
        获取请求者发出的协助请求

        Args:
            requester: 请求者username
            status: 可选的状态过滤（pending/answered）
        """
        requests = [r for r in self.requests.values() if r.requester == requester]

        if status:
            requests = [r for r in requests if r.status == status]

        # 按创建时间倒序排列（最新的在前）
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests

    def answer(self, request_id: str, answer: str) -> Optional[AssistRequest]:
        """回复协助请求"""
        request = self.requests.get(request_id)
        if not request:
            return None

        request.answer = answer
        request.status = AssistStatus.ANSWERED
        request.answered_at = time.time()

        return request

    def count_pending_by_assistant(self, assistant: str) -> int:
        """统计协助者未处理的请求数"""
        return len(self.get_by_assistant(assistant, status=AssistStatus.PENDING))


# 全局单例
assist_request_store = AssistRequestStore()
