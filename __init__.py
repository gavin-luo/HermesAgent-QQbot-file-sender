"""QQ Bot 文件发送插件 — 让大模型轻松发送物理文件."""
from .qqbot_tools import (
    _check_qqbot_available,
    _handle_qqbot_send_file,
    QQBOT_SEND_FILE_SCHEMA,
)

def register(ctx):
    """注册 QQBot 文件发送工具."""
    ctx.register_tool(
        name="qqbot_send_file",
        toolset="qqbot",
        schema=QQBOT_SEND_FILE_SCHEMA,
        handler=_handle_qqbot_send_file,
        check_fn=_check_qqbot_available,
        emoji="📁",
    )