"""
快捷回复变量替换工具

模块3: L1-1-Part2-模块3 - 快捷回复系统
版本: v3.7.0
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any


class VariableReplacer:
    """变量替换器"""

    def __init__(self):
        # 变量正则表达式：匹配 {变量名}
        self.variable_pattern = re.compile(r'\{(\w+)\}')

    def replace(
        self,
        template: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        替换模板中的变量

        Args:
            template: 包含变量占位符的模板文本
            context: 变量上下文数据

        Returns:
            替换后的文本

        示例:
            template = "您好{customer_name}，我是{agent_name}"
            context = {
                "customer_name": "张三",
                "agent_name": "李客服"
            }
            result = "您好张三，我是李客服"
        """
        if not context:
            context = {}

        def replace_variable(match):
            var_name = match.group(1)
            return self._get_variable_value(var_name, context)

        return self.variable_pattern.sub(replace_variable, template)

    def _get_variable_value(self, var_name: str, context: Dict[str, Any]) -> str:
        """
        获取变量值

        优先级：
        1. context中的直接值
        2. 系统变量（当前时间、日期）
        3. 保留占位符（数据缺失时）
        """
        # 1. 尝试从context获取
        if var_name in context and context[var_name] is not None:
            return str(context[var_name])

        # 2. 系统变量
        system_vars = self._get_system_variables()
        if var_name in system_vars:
            return system_vars[var_name]

        # 3. 数据缺失，保留占位符
        return f"{{{var_name}}}"

    def _get_system_variables(self) -> Dict[str, str]:
        """获取系统变量（当前时间、日期等）"""
        now = datetime.now()
        return {
            'current_time': now.strftime('%H:%M'),
            'current_date': now.strftime('%Y-%m-%d')
        }

    def extract_variables(self, template: str) -> list:
        """
        从模板中提取所有变量名

        Args:
            template: 模板文本

        Returns:
            变量名列表

        示例:
            template = "您好{customer_name}，您的订单{order_id}已发货"
            result = ["customer_name", "order_id"]
        """
        matches = self.variable_pattern.findall(template)
        return list(set(matches))  # 去重


def build_variable_context(
    session_data: Optional[Dict] = None,
    agent_data: Optional[Dict] = None,
    shopify_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    构建变量替换的上下文数据

    Args:
        session_data: 会话数据（包含user_profile）
        agent_data: 坐席数据
        shopify_data: Shopify订单数据

    Returns:
        变量上下文字典

    示例:
        context = build_variable_context(
            session_data={"user_profile": {"nickname": "张三"}},
            agent_data={"name": "李客服"}
        )
        # 返回: {"customer_name": "张三", "agent_name": "李客服"}
    """
    context = {}

    # 从session_data提取客户信息
    if session_data:
        user_profile = session_data.get('user_profile', {})
        if user_profile:
            context['customer_name'] = user_profile.get('nickname', '')

    # 从agent_data提取坐席信息
    if agent_data:
        context['agent_name'] = agent_data.get('name', '')

    # 从shopify_data提取订单信息（未集成时为空）
    if shopify_data:
        context['order_id'] = shopify_data.get('order_id', '')
        context['order_status'] = shopify_data.get('order_status', '')
        context['tracking_number'] = shopify_data.get('tracking_number', '')
        context['product_name'] = shopify_data.get('product_name', '')

    return context
