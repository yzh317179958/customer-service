"""
快捷回复系统 - 企业级客服工作台功能
支持分类管理、动态变量替换、使用统计、团队共享
参考：拼多多、聚水潭客服工作台

Version: v3.5.0
Created: 2025-11-26
"""

import time
import uuid
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import re


class QuickReplyCategory(str, Enum):
    """快捷回复分类"""
    PRE_SALES = "pre_sales"           # 售前咨询
    AFTER_SALES = "after_sales"       # 售后服务
    LOGISTICS = "logistics"            # 物流相关
    TECHNICAL = "technical"            # 技术支持
    POLICY = "policy"                  # 政策条款


class QuickReply(BaseModel):
    """快捷回复数据模型"""
    id: str
    category: QuickReplyCategory
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    variables: List[str] = Field(default_factory=list)  # 支持的变量列表
    shortcut: Optional[str] = None  # 快捷键 (如 "Ctrl+1")
    is_shared: bool = True  # 是否团队共享
    created_by: str  # 创建者ID
    usage_count: int = 0  # 使用次数统计
    created_at: float = Field(default_factory=time.time)
    updated_at: Optional[float] = None


class CreateQuickReplyRequest(BaseModel):
    """创建快捷回复请求"""
    category: QuickReplyCategory
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    shortcut: Optional[str] = None
    is_shared: bool = True


class UpdateQuickReplyRequest(BaseModel):
    """更新快捷回复请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    shortcut: Optional[str] = None
    is_shared: Optional[bool] = None


# 支持的动态变量定义（12+变量）
QUICK_REPLY_VARIABLES = {
    # 客户信息
    "{customer_name}": "客户姓名",
    "{customer_email}": "客户邮箱",
    "{customer_country}": "客户国家",

    # 订单信息
    "{order_id}": "订单号",
    "{order_amount}": "订单金额",
    "{order_status}": "订单状态",
    "{payment_method}": "支付方式",

    # 商品信息
    "{product_name}": "商品名称",
    "{product_sku}": "商品SKU",
    "{product_price}": "商品价格",
    "{product_stock}": "库存数量",

    # 物流信息
    "{tracking_number}": "物流单号",
    "{delivery_days}": "配送天数",
    "{carrier}": "物流公司",

    # 其他
    "{agent_name}": "坐席姓名",
    "{current_date}": "当前日期",
    "{current_time}": "当前时间"
}


class QuickReplyManager:
    """快捷回复管理器 - 使用 Redis 存储"""

    def __init__(self, redis_store):
        """
        初始化快捷回复管理器

        Args:
            redis_store: RedisSessionStore 实例
        """
        self.redis = redis_store.redis
        self.key_prefix = "quick_reply:"
        self.shortcuts_key = "quick_reply:shortcuts"  # 快捷键映射

    def _generate_id(self) -> str:
        """生成快捷回复ID"""
        timestamp = int(time.time() * 1000)
        return f"reply_{timestamp}_{uuid.uuid4().hex[:8]}"

    def _extract_variables(self, content: str) -> List[str]:
        """
        从内容中提取变量

        Args:
            content: 快捷回复内容

        Returns:
            变量列表
        """
        pattern = r'\{[a-z_]+\}'
        variables = re.findall(pattern, content)
        return list(set(variables))  # 去重

    def create_quick_reply(
        self,
        category: QuickReplyCategory,
        title: str,
        content: str,
        created_by: str,
        shortcut: Optional[str] = None,
        is_shared: bool = True
    ) -> QuickReply:
        """
        创建快捷回复

        Args:
            category: 分类
            title: 标题
            content: 内容
            created_by: 创建者ID
            shortcut: 快捷键（可选）
            is_shared: 是否团队共享

        Returns:
            QuickReply 对象

        Raises:
            ValueError: 快捷键已被占用
        """
        # 检查快捷键冲突
        if shortcut:
            existing_shortcuts = self.redis.hgetall(self.shortcuts_key)
            if shortcut.encode() in existing_shortcuts:
                raise ValueError(f"SHORTCUT_CONFLICT: 快捷键 {shortcut} 已被占用")

        # 自动提取变量
        variables = self._extract_variables(content)

        # 创建快捷回复对象
        reply_id = self._generate_id()
        quick_reply = QuickReply(
            id=reply_id,
            category=category,
            title=title,
            content=content,
            variables=variables,
            shortcut=shortcut,
            is_shared=is_shared,
            created_by=created_by,
            usage_count=0,
            created_at=time.time()
        )

        # 保存到 Redis
        key = f"{self.key_prefix}{reply_id}"
        self.redis.set(key, quick_reply.model_dump_json(), ex=86400 * 365)  # 1年过期

        # 保存快捷键映射
        if shortcut:
            self.redis.hset(self.shortcuts_key, shortcut, reply_id)

        return quick_reply

    def get_quick_reply(self, reply_id: str) -> Optional[QuickReply]:
        """
        获取快捷回复

        Args:
            reply_id: 快捷回复ID

        Returns:
            QuickReply 对象或 None
        """
        key = f"{self.key_prefix}{reply_id}"
        data = self.redis.get(key)
        if not data:
            return None

        return QuickReply.model_validate_json(data)

    def get_all_quick_replies(
        self,
        category: Optional[QuickReplyCategory] = None
    ) -> List[QuickReply]:
        """
        获取所有快捷回复

        Args:
            category: 分类筛选（可选）

        Returns:
            QuickReply 列表，按使用次数倒序排序
        """
        pattern = f"{self.key_prefix}reply_*"  # 只匹配 quick_reply:reply_* 格式的键
        keys = self.redis.keys(pattern)

        replies = []
        for key in keys:
            # 确保key类型是string（快捷回复数据），跳过hash等其他类型
            key_type = self.redis.type(key)
            # decode_responses=True 时返回 'string'，False 时返回 b'string'
            if key_type not in ('string', b'string'):
                continue

            data = self.redis.get(key)
            if data:
                reply = QuickReply.model_validate_json(data)

                # 分类筛选
                if category and reply.category != category:
                    continue

                replies.append(reply)

        # 按使用次数倒序排序
        replies.sort(key=lambda r: r.usage_count, reverse=True)

        return replies

    def update_quick_reply(
        self,
        reply_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        shortcut: Optional[str] = None,
        is_shared: Optional[bool] = None
    ) -> Optional[QuickReply]:
        """
        更新快捷回复

        Args:
            reply_id: 快捷回复ID
            title: 新标题（可选）
            content: 新内容（可选）
            shortcut: 新快捷键（可选）
            is_shared: 是否团队共享（可选）

        Returns:
            更新后的 QuickReply 对象或 None

        Raises:
            ValueError: 快捷键已被占用
        """
        quick_reply = self.get_quick_reply(reply_id)
        if not quick_reply:
            return None

        # 检查快捷键冲突
        if shortcut and shortcut != quick_reply.shortcut:
            existing_shortcuts = self.redis.hgetall(self.shortcuts_key)
            if shortcut.encode() in existing_shortcuts:
                raise ValueError(f"SHORTCUT_CONFLICT: 快捷键 {shortcut} 已被占用")

            # 删除旧快捷键映射
            if quick_reply.shortcut:
                self.redis.hdel(self.shortcuts_key, quick_reply.shortcut)

            # 添加新快捷键映射
            self.redis.hset(self.shortcuts_key, shortcut, reply_id)

        # 更新字段
        if title is not None:
            quick_reply.title = title
        if content is not None:
            quick_reply.content = content
            # 重新提取变量
            quick_reply.variables = self._extract_variables(content)
        if shortcut is not None:
            quick_reply.shortcut = shortcut
        if is_shared is not None:
            quick_reply.is_shared = is_shared

        quick_reply.updated_at = time.time()

        # 保存到 Redis
        key = f"{self.key_prefix}{reply_id}"
        self.redis.set(key, quick_reply.model_dump_json(), ex=86400 * 365)

        return quick_reply

    def delete_quick_reply(self, reply_id: str) -> bool:
        """
        删除快捷回复

        Args:
            reply_id: 快捷回复ID

        Returns:
            是否删除成功
        """
        quick_reply = self.get_quick_reply(reply_id)
        if not quick_reply:
            return False

        # 删除快捷键映射
        if quick_reply.shortcut:
            self.redis.hdel(self.shortcuts_key, quick_reply.shortcut)

        # 删除数据
        key = f"{self.key_prefix}{reply_id}"
        self.redis.delete(key)

        return True

    def increment_usage(self, reply_id: str) -> Optional[int]:
        """
        增加使用次数

        Args:
            reply_id: 快捷回复ID

        Returns:
            更新后的使用次数或 None
        """
        quick_reply = self.get_quick_reply(reply_id)
        if not quick_reply:
            return None

        quick_reply.usage_count += 1
        quick_reply.updated_at = time.time()

        # 保存到 Redis
        key = f"{self.key_prefix}{reply_id}"
        self.redis.set(key, quick_reply.model_dump_json(), ex=86400 * 365)

        return quick_reply.usage_count

    def replace_variables(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """
        替换内容中的变量

        Args:
            content: 快捷回复内容
            context: 上下文数据字典
                - customer_name: 客户姓名
                - customer_email: 客户邮箱
                - customer_country: 客户国家
                - order_id: 订单号
                - order_amount: 订单金额
                - agent_name: 坐席姓名
                - ... 等等

        Returns:
            替换后的内容
        """
        result = content

        # 客户信息
        result = result.replace("{customer_name}", context.get("customer_name", "尊敬的客户"))
        result = result.replace("{customer_email}", context.get("customer_email", ""))
        result = result.replace("{customer_country}", context.get("customer_country", ""))

        # 订单信息
        result = result.replace("{order_id}", context.get("order_id", ""))
        result = result.replace("{order_amount}", context.get("order_amount", ""))
        result = result.replace("{order_status}", context.get("order_status", ""))
        result = result.replace("{payment_method}", context.get("payment_method", ""))

        # 商品信息
        result = result.replace("{product_name}", context.get("product_name", ""))
        result = result.replace("{product_sku}", context.get("product_sku", ""))
        result = result.replace("{product_price}", context.get("product_price", ""))
        result = result.replace("{product_stock}", context.get("product_stock", ""))

        # 物流信息
        result = result.replace("{tracking_number}", context.get("tracking_number", ""))
        result = result.replace("{delivery_days}", context.get("delivery_days", ""))
        result = result.replace("{carrier}", context.get("carrier", ""))

        # 其他
        result = result.replace("{agent_name}", context.get("agent_name", "客服"))

        # 时间信息 - 实时生成
        from datetime import datetime
        now = datetime.now()
        result = result.replace("{current_date}", now.strftime("%Y-%m-%d"))
        result = result.replace("{current_time}", now.strftime("%H:%M:%S"))

        return result

    def get_categories(self) -> List[Dict[str, str]]:
        """
        获取所有分类

        Returns:
            分类列表
        """
        return [
            {"key": "pre_sales", "label": "售前咨询", "icon": "MessageCircle", "color": "#3B82F6"},
            {"key": "after_sales", "label": "售后服务", "icon": "Tool", "color": "#8B5CF6"},
            {"key": "logistics", "label": "物流相关", "icon": "Truck", "color": "#10B981"},
            {"key": "technical", "label": "技术支持", "icon": "Cpu", "color": "#F59E0B"},
            {"key": "policy", "label": "政策条款", "icon": "FileText", "color": "#6B7280"}
        ]

    def get_supported_variables(self) -> Dict[str, str]:
        """
        获取所有支持的变量

        Returns:
            变量字典 {变量名: 说明}
        """
        return QUICK_REPLY_VARIABLES
