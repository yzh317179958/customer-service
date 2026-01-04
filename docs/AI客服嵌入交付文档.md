# Fiido AI 智能客服 - Shopify 嵌入指南

> **版本**: v7.9.5
> **交付日期**: 2026-01-04
> **文档状态**: 正式交付

---

## 一、功能简介

Fiido AI 智能客服是一款 7×24 小时在线的 AI 客服系统，支持：

- 产品咨询（型号、价格、规格）
- 订单查询（输入订单号或邮箱即可查询）
- 物流追踪（自动识别快递单号并查询状态）
- 常见问题解答

嵌入后，网站右下角会出现一个**悬浮聊天按钮**，用户点击即可与 AI 客服对话。

---

## 二、嵌入代码

将以下代码**完整复制**，粘贴到 Shopify 主题文件 `theme.liquid` 的 `</body>` 标签之前：

```html
<!-- Fiido AI 智能客服 - v7.9.5 -->
<style>
  #fiido-chat-iframe {
    position: fixed;
    bottom: 0;
    right: 0;
    width: 420px;
    height: 700px;
    max-height: 100vh;
    border: none;
    z-index: 9999;
    background: transparent;
    pointer-events: none;
  }
  #fiido-chat-iframe.active {
    pointer-events: auto;
  }
  @media (max-width: 480px) {
    #fiido-chat-iframe {
      width: 100%;
      height: 100%;
      max-height: 100vh;
    }
  }
</style>
<iframe id="fiido-chat-iframe" class="active" src="https://ai.fiido.com/chat-test/?embed" allow="microphone"></iframe>
<!-- End Fiido AI 智能客服 -->
```

---

## 三、Shopify 后台操作步骤

### 步骤 1：进入代码编辑器

1. 登录 **Shopify Admin** 后台
2. 左侧菜单点击 **Online Store**（在线商店）→ **Themes**（模版）
3. 找到当前使用的模版，点击 **Actions**（操作）→ **Edit code**（编辑代码）

### 步骤 2：找到 theme.liquid 文件

1. 在左侧文件列表中，展开 **Layout** 文件夹
2. 点击 **theme.liquid** 文件

### 步骤 3：粘贴嵌入代码

1. 按 `Ctrl+F`（Mac 用 `Cmd+F`）打开搜索框
2. 搜索 `</body>`
3. 在 `</body>` 标签的**上一行**粘贴嵌入代码
4. 点击右上角 **Save**（保存）

---

## 四、验证安装

安装完成后，请按以下步骤验证：

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 访问 www.fiido.com 任意页面 | 右下角出现圆形聊天按钮 |
| 2 | 点击聊天按钮 | 从右侧滑出聊天窗口 |
| 3 | 输入 "hello" 并发送 | AI 回复英文问候语 |
| 4 | 点击关闭按钮（×） | 聊天窗口关闭，按钮仍在 |
| 5 | 用手机访问网站 | 聊天窗口自适应全屏 |

---

## 五、位置调整（可选）

### 5.1 避免与其他插件重叠

如果聊天按钮与网站上其他插件（如 QuickCEP）位置冲突，可以调整位置：

```html
<style>
  #fiido-chat-iframe {
    bottom: 80px;  /* 向上移动 80px */
  }
</style>
```

### 5.2 在特定页面隐藏

如果需要在结账页面隐藏聊天按钮：

```html
<style>
  .template-checkout #fiido-chat-iframe {
    display: none !important;
  }
</style>
```

---

## 六、常见问题

### Q1: 安装后看不到聊天按钮？

- 请清除浏览器缓存后刷新页面
- 检查代码是否粘贴在 `</body>` 标签之前
- 确认代码没有被其他内容截断

### Q2: 聊天窗口加载较慢？

首次加载需要初始化 AI 连接，通常需要 2-3 秒。后续对话会更快。

### Q3: AI 客服更新后需要修改代码吗？

**不需要**。嵌入代码指向我们的服务器，功能更新会自动同步，无需修改网站代码。

### Q4: 支持哪些语言？

目前主要支持**英文**对话，适合海外用户咨询。

---

## 七、技术支持

如遇问题，请联系：

| 项目 | 信息 |
|------|------|
| 技术对接人 | 研发部 - 杨子豪 |
| 服务状态检查 | https://ai.fiido.com/api/health |

---

## 八、版本记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v7.9.5 | 2026-01-04 | 修复嵌入模式背景显示问题，优化加载体验 |
| v7.9.4 | 2026-01-04 | 新增嵌入模式，简化嵌入代码 |
| v7.9.3 | 2026-01-04 | 修复内存泄漏问题，正式上线 |
