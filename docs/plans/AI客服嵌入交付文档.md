# Fiido AI 智能客服 - 嵌入代码交付文档

> **版本**: v7.9.25
> **更新日期**: 2025-01-06
> **测试地址**: https://ai.fiido.com/chat-test/embed-test.html

---

## 一、嵌入代码

将以下代码添加到网站 `</body>` 标签前即可：

```html
<!-- Fiido AI 智能客服 - v7.9.25 -->
<iframe id="fiido-chat-iframe" src="https://ai.fiido.com/chat-test/?embed"
    style="position:fixed;bottom:0;right:0;width:100px;height:100px;border:none;z-index:9999;background:transparent;"></iframe>
<script>
(function(){
    var f=document.getElementById('fiido-chat-iframe');
    var isMobile=window.innerWidth<=768;
    var closeTimer=null;
    if(isMobile){f.style.bottom='60px';}
    window.addEventListener('message',function(e){
        if(e.data&&e.data.type==='fiido-chat-state'){
            if(closeTimer){clearTimeout(closeTimer);closeTimer=null;}
            if(e.data.isOpen){
                if(isMobile){
                    f.style.width='100vw';
                    f.style.height='100vh';
                    f.style.bottom='0';
                }else{
                    f.style.width='440px';
                    f.style.height='100vh';
                }
            }else{
                closeTimer=setTimeout(function(){
                    f.style.width='100px';
                    f.style.height='100px';
                    f.style.bottom=isMobile?'60px':'0';
                },500);
            }
        }
    });
    window.addEventListener('resize',function(){
        var wasMobile=isMobile;
        isMobile=window.innerWidth<=768;
        if(isMobile!==wasMobile){
            f.style.width='100px';
            f.style.height='100px';
            f.style.bottom=isMobile?'60px':'0';
        }
    });
})();
</script>
```

---

## 二、效果说明

| 状态 | 电脑端 | 移动端 |
|------|--------|--------|
| 关闭 | 100px×100px（只显示悬浮按钮） | 100px×100px，bottom:60px |
| 打开 | 440px×100vh，ChatPanel 从右侧滑入 | 全屏 100vw×100vh |

---

## 三、注意事项

1. **z-index**: 默认 9999，如与页面元素冲突可调整
2. **HTTPS**: 必须在 HTTPS 页面中使用
3. **跨域**: 嵌入代码已处理跨域通信，无需额外配置

---

## 四、常见问题

### Q: 聊天按钮不显示？
A: 检查是否有 CSS 覆盖了 iframe 的 `position:fixed` 或 `z-index`

### Q: 点击无反应？
A: 确认页面是 HTTPS，检查浏览器控制台是否有跨域错误

### Q: 手机端悬浮按钮位置需要调整？
A: 修改嵌入代码中 `f.style.bottom='60px'` 的数值

---

## 五、技术支持

如有问题请联系技术团队。
