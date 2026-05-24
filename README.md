# qqbot-file-sender 插件

- 让大模型通过 Hermes Agent 发送物理文件到 QQ 聊天。
- 本插件只针对 Hermes Agent 设计和开发，仅用于 QQ bot/QQ channel；
- 在 Hermes Agent v0.14.0 (2026.5.16) 版本中测试通过

## ✨ 特性

- ✅ 自动使用 `QQBOT_HOME_CHANNEL` 作为目标聊天
- ✅ 优先通过 gateway 内置 adapter 发送（支持大文件分片）
- ✅ 自带 HTTP fallback，支持 cron 等无 gateway 场景
- ✅ 文件验证、MIME 类型检测、base64 编码
- ✅ 支持图片、视频、音频、普通文件

## 📦 安装

<span style="color: red;"> 请注意：这是插件 plugin ，不是技能 skill。</apan>
** 请注意：这是插件 plugin ，不是技能 skill。 ** 

下载后，先把目录名改为 "qqbot-file-sender" , 改好后就像下面这样
```bash
/youpath/qqbot-file-sender/
```

将 `qqbot-file-sender` 目录复制到 `~/.hermes/plugins/`：

```bash
cp -r qqbot-file-sender ~/.hermes/plugins/
```

重启 Hermes Agent：

```bash
hermes gateway restart
```

## 🔧 配置

### 先检查 .hermes/.env 文件内容
- 如果QQ bot/QQbot channel 正常交流对话，说明变量`QQBOT_HOME_CHANNEL` 、 `QQ_APP_ID` 已经存在。
- 如果 `QQBOT_HOME_CHANNEL`变量值不存在，需要用户在 QQ客户端向当前 QQbot /LLM 发送命令 `/sethome`，就会自动产生出  `QQ_CLIENT_SECRET`的变量名和值。

环境变量：

在 `.hermes/.env`文件中必须存在下面三个变量值，

| 变量名 | 说明 |
|--------|------|
| `QQBOT_HOME_CHANNEL` | 默认聊天 ID（user/group openid） |
| `QQ_APP_ID` | QQ Bot App ID（fallback 用） |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret（fallback 用） |



## 🚀 使用

大模型调用时只需提供 `file_path`：

```json
{
  "file_path": "/tmp/report.pdf",
  "caption": "这是您的季度报告"
}
```

无需指定 `chat_id`（自动使用 `QQBOT_HOME_CHANNEL`）。

## 📝 工具名称

注册的工具：`qqbot_send_file`（注意下划线）

## 🔄 工作原理

1. 验证文件存在、非空
2. 解析目标 `chat_id`（优先：参数 > `QQBOT_HOME_CHANNEL`）
3. 尝试 gateway 内置 adapter（同进程时）
4. 失败则使用 HTTP API（需要 `QQ_APP_ID` / `QQ_CLIENT_SECRET`）

# 适用条件
本插件针对 Hermes Agent 设计和开发，在Hermes Agent v0.14.0 (2026.5.16) 版本中测试通过
