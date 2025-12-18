"""
邮件服务模块

功能：
- 封装 SMTP 邮件发送
- 提供人工接管邮件通知
- 支持 HTML 模板
- 重试机制和错误处理

配置环境变量：
- SMTP_HOST: SMTP服务器地址
- SMTP_PORT: SMTP端口（默认465 SSL）
- SMTP_USERNAME: 发件人邮箱
- SMTP_PASSWORD: 邮箱密码/授权码
- SMTP_USE_TLS: 是否使用TLS（默认true）
- EMAIL_RECIPIENTS: 收件人邮箱（逗号分隔）
- EMAIL_FROM_NAME: 发件人名称
"""

import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class EmailConfig:
    """邮件配置"""

    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.qq.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 465))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Fiido客服系统')

        # 收件人列表
        recipients_str = os.getenv('EMAIL_RECIPIENTS', '')
        self.recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]

    def is_configured(self) -> bool:
        """检查邮件是否已配置"""
        return bool(self.smtp_username and self.smtp_password and self.recipients)


class EmailService:
    """邮件发送服务"""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self.max_retries = 3
        self.retry_delay = 2  # 秒

    def _create_connection(self):
        """创建 SMTP 连接"""
        if self.config.smtp_port == 465:
            # SSL 连接
            server = smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=30
            )
        else:
            # 普通连接，可选 TLS
            server = smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=30
            )
            if self.config.use_tls:
                server.starttls()

        server.login(self.config.smtp_username, self.config.smtp_password)
        return server

    def send_email(
        self,
        subject: str,
        html_content: str,
        recipients: Optional[List[str]] = None
    ) -> dict:
        """
        发送邮件

        Args:
            subject: 邮件主题
            html_content: HTML内容
            recipients: 收件人列表（默认使用配置）

        Returns:
            dict: {success: bool, message_id: str, error: str}
        """
        if not self.config.is_configured():
            return {
                'success': False,
                'message_id': None,
                'error': '邮件服务未配置'
            }

        recipients = recipients or self.config.recipients
        if not recipients:
            return {
                'success': False,
                'message_id': None,
                'error': '没有收件人'
            }

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((self.config.from_name, self.config.smtp_username))
        msg['To'] = ', '.join(recipients)

        # 添加 HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 重试发送
        last_error = None
        for attempt in range(self.max_retries):
            try:
                server = self._create_connection()
                server.sendmail(
                    self.config.smtp_username,
                    recipients,
                    msg.as_string()
                )
                server.quit()

                message_id = f"mail_{int(time.time() * 1000)}"
                print(f"✅ 邮件发送成功: {subject} -> {', '.join(recipients)}")

                return {
                    'success': True,
                    'message_id': message_id,
                    'error': None
                }

            except smtplib.SMTPException as e:
                last_error = str(e)
                print(f"⚠️  邮件发送失败 (尝试 {attempt + 1}/{self.max_retries}): {last_error}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

            except Exception as e:
                last_error = str(e)
                print(f"❌ 邮件发送异常: {last_error}")
                break

        return {
            'success': False,
            'message_id': None,
            'error': last_error
        }

    def send_manual_escalation_email(self, session_state) -> dict:
        """
        发送人工接管通知邮件

        Args:
            session_state: SessionState 对象

        Returns:
            dict: 发送结果
        """
        # 生成邮件内容
        subject = f"[Fiido客服] 人工接管请求 - {session_state.session_name}"
        html_content = self._generate_escalation_email_html(session_state)

        result = self.send_email(subject, html_content)

        # 记录发送结果
        if result['success']:
            print(f"📧 人工接管邮件已发送: {session_state.session_name}")
        else:
            print(f"❌ 人工接管邮件发送失败: {result['error']}")

        return result

    def _generate_escalation_email_html(self, session_state) -> str:
        """生成人工接管邮件 HTML 内容"""

        # 格式化时间
        now = datetime.now()
        trigger_time = datetime.fromtimestamp(
            session_state.escalation.trigger_at if session_state.escalation else time.time()
        )

        # 获取最近消息
        recent_messages = session_state.history[-10:] if session_state.history else []
        messages_html = ""

        for msg in recent_messages:
            role_name = {
                'user': '用户',
                'assistant': 'AI',
                'agent': '坐席',
                'system': '系统'
            }.get(msg.role, msg.role)

            msg_time = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S')

            # 根据角色设置样式
            if msg.role == 'user':
                bg_color = '#e8f4fd'
                align = 'left'
            elif msg.role == 'assistant':
                bg_color = '#f0f9f0'
                align = 'left'
            else:
                bg_color = '#f5f5f5'
                align = 'left'

            messages_html += f'''
            <div style="padding: 8px 12px; margin: 4px 0; background: {bg_color}; border-radius: 6px;">
                <strong>{role_name}</strong> <span style="color: #999; font-size: 12px;">{msg_time}</span>
                <div style="margin-top: 4px;">{msg.content}</div>
            </div>
            '''

        # 触发原因
        reason_text = {
            'keyword': '关键词触发',
            'ai_fail': 'AI连续失败',
            'vip': 'VIP用户',
            'manual': '用户主动请求'
        }.get(
            session_state.escalation.reason if session_state.escalation else 'unknown',
            '未知原因'
        )

        # 生成完整 HTML
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
                .info-row {{ display: flex; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .info-label {{ font-weight: bold; width: 100px; color: #666; }}
                .info-value {{ flex: 1; }}
                .messages {{ margin-top: 16px; }}
                .footer {{ padding: 16px; text-align: center; font-size: 12px; color: #999; }}
                .urgent {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">Fiido 智能客服 - 人工接管请求</h2>
                </div>

                <div class="content">
                    <div class="urgent">
                        <strong>⚠️ 需要人工介入</strong><br>
                        用户请求已触发人工接管，请尽快处理。
                    </div>

                    <h3>会话信息</h3>
                    <div class="info-row">
                        <span class="info-label">会话ID</span>
                        <span class="info-value">{session_state.session_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">触发原因</span>
                        <span class="info-value">{reason_text}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">触发时间</span>
                        <span class="info-value">{trigger_time.strftime('%Y-%m-%d %H:%M:%S')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">当前状态</span>
                        <span class="info-value">{session_state.status.value if hasattr(session_state.status, 'value') else session_state.status}</span>
                    </div>

                    <div class="messages">
                        <h3>最近对话记录（最多10条）</h3>
                        {messages_html if messages_html else '<p style="color: #999;">暂无对话记录</p>'}
                    </div>
                </div>

                <div class="footer">
                    此邮件由 Fiido 客服系统自动发送<br>
                    发送时间: {now.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        '''

        return html


# 全局实例
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """获取全局 EmailService 实例"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_escalation_email(session_state) -> dict:
    """快捷函数：发送人工接管邮件"""
    return get_email_service().send_manual_escalation_email(session_state)
