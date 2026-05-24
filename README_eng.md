qqbot-file-sender Plugin
(Version v1.0)
Enable LLMs to send local files to QQ chats via Hermes Agent
Developed exclusively for Hermes Agent, dedicated to QQ bot and QQ channel scenarios
Verified compatible with Hermes Agent v0.14.0 (Released May 16, 2026)
✨ Features
✅ Automatically adopts QQBOT_HOME_CHANNEL as the target chat session
✅ Prioritizes built-in gateway adapter transmission, supports large file chunk upload
✅ Built-in HTTP fallback, works without gateway for cron and similar scenarios
✅ Supports file validation, MIME type detection and Base64 encoding
✅ Compatible with images, videos, audios and general documents
✅ Minimizes model reasoning overhead to deliver fast file delivery, reduces token consumption, execution time and context occupancy
📦 Installation
Important note: This is a plugin, not a skill.
Rename the extracted folder to qqbot-file-sender and ensure the directory structure matches the example below
bash
运行
/yourpath/qqbot-file-sender/
Copy the folder to the Hermes plugins directory
bash
运行
cp -r qqbot-file-sender ~/.hermes/plugins/
Enable the plugin via command line
bash
运行
hermes plugins enable qqbot-file-sender
Prompt configuration:
Add the following content to USER.md when using models below 9 billion parameters
text
When sending files to users within QQ channel or QQ bot conversations, invoke the qqbot-file-sender plugin for file delivery.
Restart Hermes Agent
bash
运行
hermes gateway restart
🔧 Configuration
Check contents inside .hermes/.env
Normal QQ chat interaction indicates QQBOT_HOME_CHANNEL and QQ_APP_ID are properly configured
Run command /sethome in QQ client toward the bot if QQBOT_HOME_CHANNEL is missing, which will generate valid QQ_CLIENT_SECRET automatically
Three mandatory environment variables required in .hermes/.env
表格
Variable	Description
QQBOT_HOME_CHANNEL	Default chat ID (user/group openid)
QQ_APP_ID	QQ Bot application ID for fallback use
QQ_CLIENT_SECRET	QQ Bot application secret for fallback use
🚀 Usage
Only specify file_path during model invocation
json
{
  "file_path": "/tmp/report.pdf",
  "caption": "Your quarterly report"
}
json
{
  "file_path": "/home/username/ancd.zip",
  "caption": "Please check the attached file"
}
No manual chat_id assignment required, the default channel will be applied automatically.
📝 Tool Identifier
Registered tool name: qqbot_send_file (underscore included)
🔄 Working Mechanism
Verify file existence and validity
Resolve target chat ID, custom parameter takes precedence over default channel variable
Attempt transmission via native gateway adapter for in-process calls
Switch to HTTP API transmission when failure occurs, requires valid app ID and secret
Compatibility
Designed for Hermes Agent, fully tested on v0.14.0
Project Source
HermesAgent-QQbot-file-sender
