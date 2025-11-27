"""
快捷回复系统 - 数据模型

模块3: L1-1-Part2-模块3 - 快捷回复系统
版本: v3.7.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal
import time

QuickReplyCategory = Literal[
    'greeting',      # 欢迎语
    'pre_sales',     # 售前咨询
    'after_sales',   # 售后服务
    'logistics',     # 物流查询
    'technical',     # 技术支持
    'closing',       # 结束语
    'custom'         # 自定义
]


@dataclass
class QuickReply:
    """快捷回复数据模型"""

    id: str                                    # 唯一ID
    title: str                                 # 标题
    content: str                               # 内容（包含变量占位符）
    category: QuickReplyCategory               # 分类
    variables: List[str] = field(default_factory=list)  # 使用的变量列表
    shortcut_key: Optional[str] = None         # 快捷键（Ctrl+1~9）
    is_shared: bool = False                    # 是否团队共享
    created_by: str = ""                       # 创建者ID
    usage_count: int = 0                       # 使用次数
    created_at: float = field(default_factory=time.time)  # 创建时间
    updated_at: float = field(default_factory=time.time)  # 更新时间

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "variables": self.variables,
            "shortcut_key": self.shortcut_key,
            "is_shared": self.is_shared,
            "created_by": self.created_by,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QuickReply':
        """从字典创建对象"""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            category=data["category"],
            variables=data.get("variables", []),
            shortcut_key=data.get("shortcut_key"),
            is_shared=data.get("is_shared", False),
            created_by=data.get("created_by", ""),
            usage_count=data.get("usage_count", 0),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = time.time()


# 预定义分类信息
QUICK_REPLY_CATEGORIES = {
    'greeting': {
        'name': '欢迎语',
        'description': '接入会话时的欢迎语',
        'example': '您好，我是XX客服，很高兴为您服务'
    },
    'pre_sales': {
        'name': '售前咨询',
        'description': '产品咨询、售前问题',
        'example': 'Fiido D4S续航50公里，最高时速25km/h'
    },
    'after_sales': {
        'name': '售后服务',
        'description': '退换货、维修等售后问题',
        'example': '请您提供订单号，我帮您查询...'
    },
    'logistics': {
        'name': '物流查询',
        'description': '查询物流、快递信息',
        'example': '您的订单已发货，物流单号...'
    },
    'technical': {
        'name': '技术支持',
        'description': '故障排查、技术问题',
        'example': '请您尝试以下步骤...'
    },
    'closing': {
        'name': '结束语',
        'description': '结束会话时的告别语',
        'example': '感谢您的咨询，祝您生活愉快'
    },
    'custom': {
        'name': '自定义',
        'description': '其他自定义场景',
        'example': ''
    }
}

# 支持的变量列表
SUPPORTED_VARIABLES = {
    'customer_name': {
        'name': '客户昵称',
        'source': 'user_profile.nickname',
        'example': '张三'
    },
    'agent_name': {
        'name': '坐席姓名',
        'source': 'agent.name',
        'example': '李客服'
    },
    'order_id': {
        'name': '订单号',
        'source': 'shopify.order_id',
        'example': 'ORD123456'
    },
    'order_status': {
        'name': '订单状态',
        'source': 'shopify.order_status',
        'example': '已发货'
    },
    'tracking_number': {
        'name': '物流单号',
        'source': 'shopify.tracking_number',
        'example': 'SF123456789'
    },
    'product_name': {
        'name': '产品名称',
        'source': 'shopify.product_name',
        'example': 'Fiido D4S'
    },
    'current_time': {
        'name': '当前时间',
        'source': 'system.time',
        'example': '14:30'
    },
    'current_date': {
        'name': '当前日期',
        'source': 'system.date',
        'example': '2025-01-27'
    }
}
