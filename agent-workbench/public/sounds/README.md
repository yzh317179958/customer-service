# 提示音文件说明

此目录用于存放消息提醒的音频文件。

## 所需文件

1. **notification.mp3** - 默认通知提示音
   - 用途：新会话、客户回复、转接请求等
   - 时长：建议 1-2 秒
   - 格式：MP3（推荐）或 OGG

2. **vip-notification.mp3** - VIP客户专属提示音
   - 用途：VIP客户请求服务时
   - 时长：建议 2-3 秒
   - 格式：MP3（推荐）或 OGG
   - 特点：应该比默认提示音更明显

## 音频要求

- 格式：MP3 / OGG / WAV
- 采样率：建议 44.1kHz
- 比特率：建议 128kbps
- 声道：单声道或立体声均可
- 音量：应该适中，不要过响

## 获取提示音

可以从以下来源获取免费提示音：

1. **Freesound** - https://freesound.org/
2. **Zapsplat** - https://www.zapsplat.com/
3. **Notification Sounds** - https://notificationsounds.com/

## 临时方案

如果暂时没有音频文件，系统会优雅降级，仅显示浏览器通知而不播放声音。

## 使用方法

将音频文件放置在此目录下：

```
public/sounds/
├── notification.mp3        # 必需
├── vip-notification.mp3    # 可选（如无则使用默认音）
└── README.md               # 本文件
```

重新加载前端即可生效，无需重启开发服务器。
