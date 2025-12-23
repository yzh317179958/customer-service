# SMTP 邮件配置指南

> **文档版本**：v1.0
> **创建日期**：2025-12-23
> **适用模块**：products/notification、services/email

---

## 一、概述

17track 物流追踪集成的通知功能依赖 SMTP 邮件服务发送以下类型的通知：

| 通知类型 | 模板文件 | 触发条件 |
|----------|----------|----------|
| 拆包裹通知 | split_package.html | 订单分多个包裹发货 |
| 预售发货通知 | presale_shipped.html | 预售商品发货 |
| 异常警报 | exception_alert.html | 物流异常（丢失/损坏/海关等） |
| 签收确认 | delivery_confirm.html | 包裹签收 |

---

## 二、环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# ===== SMTP 邮件配置 =====

# SMTP 服务器地址
SMTP_HOST=smtp.example.com

# SMTP 端口
# - 465: SSL（推荐）
# - 587: STARTTLS
# - 25:  明文（不推荐）
SMTP_PORT=465

# SMTP 认证信息
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-smtp-password

# 是否使用 TLS（仅在端口非 465 时有效）
SMTP_USE_TLS=true

# 发件人显示名称
EMAIL_FROM_NAME=Fiido Customer Service

# 默认收件人列表（用于内部通知，逗号分隔）
EMAIL_RECIPIENTS=support@fiido.com,ops@fiido.com

# 物流通知专用发件人（可选）
NOTIFICATION_EMAIL_FROM=noreply@fiido.com
```

---

## 三、常用 SMTP 服务商配置

### 3.1 QQ 邮箱

```bash
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-qq@qq.com
SMTP_PASSWORD=授权码  # 非QQ密码，需在QQ邮箱设置中获取
```

**获取授权码**：
1. 登录 QQ 邮箱 → 设置 → 账户
2. 开启 POP3/SMTP 服务
3. 生成授权码

### 3.2 Gmail

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=应用专用密码  # 需开启两步验证后生成
```

**获取应用专用密码**：
1. 登录 Google 账号 → 安全性
2. 开启两步验证
3. 创建应用专用密码

### 3.3 Outlook/Microsoft 365

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=你的密码
```

### 3.4 Amazon SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE  # AWS SES SMTP 凭证
SMTP_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 3.5 SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxx  # SendGrid API Key
```

### 3.6 阿里云邮件推送

```bash
SMTP_HOST=smtpdm.aliyun.com
SMTP_PORT=465
SMTP_USERNAME=发信地址
SMTP_PASSWORD=SMTP密码
```

---

## 四、验证配置

### 4.1 快速测试脚本

```python
import asyncio
import sys
sys.path.insert(0, '.')

from services.email import get_email_service

def test_smtp():
    service = get_email_service()

    # 检查配置
    if not service.config.is_configured():
        print("❌ SMTP 未配置")
        print(f"   SMTP_HOST: {service.config.smtp_host}")
        print(f"   SMTP_USERNAME: {'已设置' if service.config.smtp_username else '未设置'}")
        print(f"   SMTP_PASSWORD: {'已设置' if service.config.smtp_password else '未设置'}")
        return

    print("✅ SMTP 配置检测通过")
    print(f"   服务器: {service.config.smtp_host}:{service.config.smtp_port}")
    print(f"   发件人: {service.config.smtp_username}")

    # 发送测试邮件
    result = service.send_email(
        subject="SMTP 配置测试",
        html_content="<h1>测试成功</h1><p>您的 SMTP 配置正确。</p>",
        recipients=service.config.recipients[:1],  # 只发给第一个收件人
        email_type="test"
    )

    if result["success"]:
        print("✅ 测试邮件发送成功")
    else:
        print(f"❌ 测试邮件发送失败: {result.get('error')}")

if __name__ == "__main__":
    test_smtp()
```

### 4.2 运行测试

```bash
cd /home/yzh/AI客服/鉴权
python3 -c "
from services.email import get_email_service
svc = get_email_service()
print('配置状态:', '已配置' if svc.config.is_configured() else '未配置')
print('SMTP 服务器:', svc.config.smtp_host)
print('SMTP 端口:', svc.config.smtp_port)
"
```

---

## 五、故障排除

### 5.1 常见错误

| 错误信息 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `Connection refused` | 端口错误或被防火墙阻止 | 检查端口，尝试 587 或 465 |
| `Authentication failed` | 用户名或密码错误 | 检查凭证，使用授权码 |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL 证书问题 | 更新系统证书或使用 587+TLS |
| `Connection timed out` | 网络问题或 IP 被限制 | 检查网络，联系服务商 |

### 5.2 调试模式

启用详细日志：

```python
import logging
logging.getLogger('services.email').setLevel(logging.DEBUG)
```

---

## 六、生产环境注意事项

### 6.1 发送频率限制

不同服务商有不同的发送限制：

| 服务商 | 免费额度 | 频率限制 |
|--------|----------|----------|
| QQ 邮箱 | 无限制 | 200封/天 |
| Gmail | 无限制 | 500封/天 |
| Amazon SES | 200封/天 | 1封/秒 |
| SendGrid | 100封/天（免费版） | 无限制 |

### 6.2 发送最佳实践

1. **使用队列**：高并发时使用 Redis 队列异步发送
2. **退避重试**：失败后指数退避重试
3. **监控告警**：监控发送成功率，低于阈值报警
4. **SPF/DKIM**：配置 DNS 记录提高送达率

### 6.3 安全建议

1. **不要硬编码密码**：始终使用环境变量
2. **使用授权码**：避免使用账号真实密码
3. **最小权限**：创建专用发件邮箱账号
4. **定期轮换**：定期更换 SMTP 密码

---

## 七、与 17track 通知集成

### 7.1 邮件发送流程

```
17track Webhook 推送
        ↓
products/notification/handlers/tracking_handler.py
        ↓
判断事件类型（签收/异常）
        ↓
products/notification/handlers/notification_sender.py
        ↓
渲染邮件模板（Jinja2）
        ↓
services/email/service.py
        ↓
SMTP 发送
```

### 7.2 自定义邮件模板

邮件模板位于 `products/notification/templates/`：

```
templates/
├── split_package.html      # 拆包裹通知
├── presale_shipped.html    # 预售发货通知
├── exception_alert.html    # 异常警报
└── delivery_confirm.html   # 签收确认
```

模板使用 Jinja2 语法，可自定义样式和内容。

---

## 八、相关文档

- [17track 集成 PRD](prd.md)
- [实施计划](implementation-plan.md)
- [进度追踪](progress.md)
- [服务层邮件模块](../../../services/email/README.md)
