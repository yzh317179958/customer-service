# 邮件服务规范

> **服务定位**：SMTP 邮件发送服务
> **服务状态**：已完成
> **最后更新**：2025-12-18

---

## 一、服务职责

- SMTP 邮件发送
- 多语言邮件模板
- 发送记录与重试

---

## 二、公开接口

```python
class EmailService:
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        template: str = None
    ) -> bool

def get_email_service() -> EmailService
```

---

## 三、目录结构

```
services/email/
├── __init__.py
├── README.md           # 本文档
├── service.py          # 邮件服务
├── templates/          # 邮件模板
│   ├── presale.html
│   ├── split_package.html
│   └── anomaly_report.html
└── tests/
    └── test_email.py
```

---

## 四、配置项

| 环境变量 | 说明 |
|----------|------|
| SMTP_HOST | SMTP 服务器 |
| SMTP_PORT | SMTP 端口 |
| SMTP_USER | SMTP 用户名 |
| SMTP_PASSWORD | SMTP 密码 |

---

## 五、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-18 | 初始版本 |
