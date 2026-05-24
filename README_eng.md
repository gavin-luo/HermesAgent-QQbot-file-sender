# qqbot-file-sender Plugin  
*(Version v1.0)*

- Enables large language models (LLMs) to transmit physical files to QQ chats via the Hermes Agent framework.  
- This plugin is exclusively designed and developed for Hermes Agent, targeting QQ Bot / QQ Channel integrations only.  
- Verified and tested with Hermes Agent v0.14.0 (released on May 16, 2026).

---

## ✨ Key Features

- ✅ Automatically targets the chat session defined by the `QQBOT_HOME_CHANNEL` environment variable.  
- ✅ Prioritizes transmission via the gateway's built-in adapter, supporting chunked uploads for large files.  
- ✅ Includes an HTTP fallback mechanism, ensuring compatibility in environments without gateway access (e.g., cron jobs).  
- ✅ Implements file validation, MIME type detection, and Base64 encoding for secure transmission.  
- ✅ Supports multiple file types: images, videos, audio, and generic documents.  
- ✅ Minimizes LLM inference overhead—files can be sent with minimal reasoning, conserving token usage, reducing execution latency, and alleviating context management burden.

---

## 📦 Installation

> ⚠️ **Important Notice**: This is a **plugin**, not a skill. Please ensure correct categorization during deployment.

1. After downloading, rename the extracted directory to `qqbot-file-sender`, resulting in the following structure:
   ```bash
   /yourpath/qqbot-file-sender/
   ```

2. Copy the `qqbot-file-sender` directory to the Hermes plugins path:
   ```bash
   cp -r qqbot-file-sender ~/.hermes/plugins/
   ```

3. Enable the plugin via the Hermes CLI:
   ```bash
   hermes plugins enable qqbot-file-sender
   ```

4. **Prompt Configuration** (for models with <9B parameters):  
   Append the following instruction to your `USER.md` file to guide model behavior:
   ```text
   When sending a file to a user, if the current conversation channel is QQ Channel / QQ Bot, use the plugin "qqbot-file-sender" to deliver the file.
   ```

5. Restart the Hermes Agent to apply changes:
   ```bash
   hermes gateway restart
   ```

---

## 🔧 Configuration

### Prerequisite: Verify `.hermes/.env` Settings

- If QQ Bot / QQ Channel communication functions correctly, the environment variables `QQBOT_HOME_CHANNEL` and `QQ_APP_ID` are already configured.  
- If `QQBOT_HOME_CHANNEL` is missing, instruct users to send the command `/sethome` via the QQ client to the current QQ Bot / LLM instance. This action will automatically generate the `QQ_CLIENT_SECRET` variable and its corresponding value.

### Required Environment Variables

Ensure the following variables are defined in your `.hermes/.env` file:

| Variable | Description |
|----------|-------------|
| `QQBOT_HOME_CHANNEL` | Default target chat identifier (user/group openid) |
| `QQ_APP_ID` | QQ Bot App ID (used for HTTP fallback) |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret (used for HTTP fallback) |

---

## 🚀 Usage

When invoked by an LLM, the plugin requires only the `file_path` parameter:

```json
{
  "file_path": "/tmp/report.pdf",
  "caption": "Please find attached your quarterly report."
}
```

```json
{
  "file_path": "/home/username/ancd.zip",
  "caption": "Kindly review the attached file."
}
```

> 📌 Note: Explicit specification of `chat_id` is unnecessary—the plugin automatically resolves the target using `QQBOT_HOME_CHANNEL`.

---

## 📝 Registered Tool Name

The plugin registers the following tool for LLM invocation:  
**`qqbot_send_file`** *(note: underscores, not hyphens)*

---

## 🔄 Operational Workflow

1. **Validation**: Confirm file existence and non-zero size.  
2. **Target Resolution**: Determine `chat_id` (priority: explicit parameter > `QQBOT_HOME_CHANNEL`).  
3. **Primary Transmission**: Attempt delivery via the gateway's built-in adapter (in-process execution).  
4. **Fallback Mechanism**: If primary method fails, revert to HTTP API using `QQ_APP_ID` and `QQ_CLIENT_SECRET`.

---

## ✅ Compatibility

This plugin is purpose-built for the Hermes Agent ecosystem and has been rigorously tested with **Hermes Agent v0.14.0** (released May 16, 2026).

---

## 📚 Source & Attribution

- **Plugin Repository**: [HermesAgent-QQbot-file-sender](https://github.com/gavin-luo/HermesAgent-QQbot-file-sender)  
- **License & Contribution**: Please refer to the upstream repository for licensing terms and contribution guidelines.
