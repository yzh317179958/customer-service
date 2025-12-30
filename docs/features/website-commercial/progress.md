# 官网商业化 - 进度追踪

> **核心目标**：官网能访问、能付款
> **当前**：Step 2 已完成，可开始 Step 3

---

| Step | 任务 | 状态 |
|------|------|------|
| 1 | 前端品牌适配 | ✅ 已完成 |
| 2 | 收款码弹窗 | ✅ 已完成 |
| 3 | 部署上线 | ⏳ 待开始 |
| 4 | 后端框架（可选） | - |
| 5 | 数据库（可选） | - |

---

## Step 1: 前端品牌适配

**完成时间:** 2025-12-30 17:00
**版本号:** v7.9.0

**完成内容:**
- Navbar.tsx - 品牌名 CrossBorderAI → Fiido，标语改为"AI 智能客服"
- Footer.tsx - 品牌名、版权信息、标语全部改为 Fiido
- Pricing.tsx - 价格符号 $ → ¥，单位 /mo → /月，套餐改为免费版/基础版/专业版（¥0/¥199/¥499）
- PricingPage.tsx - 价格符号 $ → ¥，单位改中文，ROI 计算器货币改为人民币
- FAQ.tsx - NovaStream 内容替换为 Fiido 相关问答（4条）
- index.html - 标题改为"Fiido | AI 智能客服 - 跨境电商客服解决方案"

**修改文件清单:**
```
components/Navbar.tsx
components/Footer.tsx
components/Pricing.tsx
components/FAQ.tsx
pages/PricingPage.tsx
index.html
```

**测试结果:**
- ✅ 首页品牌名显示 Fiido
- ✅ 首页价格显示人民币（¥）
- ✅ 价格方案页价格显示人民币（¥）
- ✅ FAQ 内容为 Fiido 相关
- ✅ 页面标题为 Fiido

---

## Step 2: 收款码弹窗

**完成时间:** 2025-12-30 17:20
**版本号:** v7.9.1

**完成内容:**
- 新增 PaymentModal.tsx 收款码弹窗组件
- 集成收款码图片 (1.jpg → payment-qr.jpg)
- 显示套餐名称、价格、开通流程
- 客服微信：yzh317179958（可复制）
- 修复全站摆设按钮，统一指向定价/支付流程

**修改文件清单:**
```
components/PaymentModal.tsx (新增)
components/Pricing.tsx
components/Hero.tsx
components/CTA.tsx
components/EcosystemIntegration.tsx
pages/PricingPage.tsx
pages/ProductDetail.tsx
pages/SolutionDetail.tsx
pages/CasesPage.tsx
pages/Home.tsx
public/payment-qr.jpg (新增)
```

**测试结果:**
- ✅ 点击"立即订阅"弹出收款码弹窗
- ✅ 弹窗显示收款码图片
- ✅ 全站按钮均可跳转到定价区域
- ✅ 客服微信可复制
