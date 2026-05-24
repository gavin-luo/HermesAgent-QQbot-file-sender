"""QQ Bot 文件发送插件 — 完整改进版.

核心改进:
1. 使用 _gateway_runner_ref() 复用内置 adapter（分片上传、token 管理）
2. QQBOT_HOME_CHANNEL 作为默认目标，LLM 无需思考 chat_id
3. 保留 HTTP fallback 用于 cron / 非 gateway 进程场景
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from gateway.run import _gateway_runner_ref  # 正确的弱引用

logger = logging.getLogger(__name__)

# ── Tool schema ──────────────────────────────────────────────────────────

QQBOT_SEND_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "要发送的文件的绝对路径或相对路径（相对于 Hermes 工作目录）",
        },
        "caption": {
            "type": "string",
            "description": "附带的文字说明（可选，跟随文件一起显示）",
        },
        "file_name": {
            "type": "string",
            "description": "在 QQ 中显示的文件名（可选，默认使用原文件名）",
        },
    },
    "required": ["file_path"],
}

# ── Handler ──────────────────────────────────────────────────────────────

def _handle_qqbot_send_file(params: Dict[str, Any], **kwargs: Any) -> str:
    """发送物理文件到 QQ 聊天.

    chat_id 自动从环境变量 QQBOT_HOME_CHANNEL 获取，无需手动指定。
    返回值：JSON 字符串，让 QQ 通道识别处理。
    """
    file_path: str = params.get("file_path", "")
    caption: Optional[str] = params.get("caption")
    file_name: Optional[str] = params.get("file_name")

    # 1) 验证文件路径
    if not file_path:
        return _fail("file_path is required")

    local_path = Path(file_path).expanduser()
    if not local_path.is_absolute():
        local_path = (Path.cwd() / local_path).resolve()

    if not local_path.exists() or not local_path.is_file():
        return _fail(f"文件不存在: {local_path}")

    if local_path.stat().st_size == 0:
        return _fail("文件为空，无法发送")

    resolved_name = file_name or local_path.name

    # 2) 获取目标 chat_id（显式 > 环境变量）
    chat_id: Optional[str] = params.get("chat_id")
    if not chat_id:
        chat_id = os.getenv("QQBOT_HOME_CHANNEL", "").strip()

    if not chat_id:
        return _fail(
            "缺少目标聊天 ID。请设置环境变量 QQBOT_HOME_CHANNEL，"
            "或调用时提供 chat_id 参数"
        )

    # 3) 尝试通过内置 adapter 发送（gateway 在进程内时）
    try:
        runner = _gateway_runner_ref()
    except Exception:
        runner = None

    if runner is not None:
        adapter = getattr(runner, "adapters", {}).get("qqbot")  # type: ignore
        if adapter is not None:
            return _send_via_adapter(
                adapter,
                chat_id=chat_id,
                file_path=str(local_path),
                caption=caption,
                file_name=resolved_name,
            )

    # 4) Fallback：直接通过 QQ API 发送（gateway 不在本进程时，如 cron）
    return _send_via_direct_api(
        file_path=str(local_path),
        chat_id=chat_id,
        caption=caption,
        file_name=resolved_name,
    )


# ── Adapter path (gateway 进程中，推荐) ──────────────────────────────────

def _send_via_adapter(
    adapter,
    chat_id: str,
    file_path: str,
    caption: Optional[str],
    file_name: str,
) -> str:
    """通过内置 QQ adapter 发送文件."""
    logger.info("通过内置 QQ adapter 发送: %s → %s", file_path, chat_id)

    async def _send():
        # 尝试使用 adapter 的 send_document 方法
        if hasattr(adapter, "send_document"):
            return await adapter.send_document(
                chat_id=chat_id,
                file_path=file_path,
                caption=caption,
                file_name=file_name,
            )
        # 降级：使用 send_file（如果有）
        elif hasattr(adapter, "send_file"):
            return await adapter.send_file(
                chat_id=chat_id,
                file_path=file_path,
                caption=caption,
                file_name=file_name,
            )
        else:
            raise RuntimeError("adapter 既没有 send_document 也没有 send_file 方法")

    result = _run_async(_send())
    if result.success:
        # adapter 返回的是 SendResult，成功时返回包含成功信息的字符串
        return _ok(file_path, chat_id, message_id=result.message_id)
    return _fail(result.error or "发送失败")


# ── Direct API fallback (cron / 非 gateway 进程) ─────────────────────────

def _send_via_direct_api(
    file_path: str,
    chat_id: str,
    caption: Optional[str],
    file_name: str,
) -> str:
    """直接通过 QQ HTTP API 发送文件（不依赖 gateway 进程）."""
    try:
        import httpx
    except ImportError:
        return _fail("httpx 未安装，无法使用 fallback 发送")

    app_id = os.getenv("QQ_APP_ID", "").strip()
    secret = os.getenv("QQ_CLIENT_SECRET", "").strip()
    if not app_id or not secret:
        return _fail("QQ_APP_ID / QQ_CLIENT_SECRET 环境变量未配置")

    media_type = _get_media_type(Path(file_path))

    try:
        with httpx.Client(timeout=120) as client:
            # 获取 access token
            token_resp = client.post(
                "https://bots.qq.com/app/getAppAccessToken",
                json={"appId": app_id, "clientSecret": secret},
            )
            token_data = _safe_json(token_resp)
            if not token_data:
                return _fail(f"获取 access token 失败: HTTP {token_resp.status_code}")
            access_token = token_data.get("access_token")
            if not access_token:
                return _fail(f"token 响应中无 access_token: {token_data}")

            headers = {
                "Authorization": f"QQBot {access_token}",
                "Content-Type": "application/json",
            }

            # 上传文件（使用用户端点和群组端点）
            upload_data = _upload_file_via_api(client, headers, file_path, media_type, chat_id, file_name)
            if not upload_data or "file_info" not in upload_data:
                return _fail(f"文件上传失败: {upload_data}")

            # 发送消息
            payload: Dict[str, Any] = {
                "msg_type": 7,
                "media": {"file_info": upload_data["file_info"]},
            }
            if caption:
                payload["content"] = caption[:4000]

            # 尝试用户端点，失败则尝试群组端点
            send_data = _send_message_via_api(client, headers, chat_id, payload)
            if send_data:
                return _ok(file_path, chat_id, message_id=send_data.get("id"))
            else:
                # 尝试群组端点
                if chat_id.startswith("group_"):
                    send_data = _send_message_via_api(client, headers, chat_id, payload, is_group=True)
                    if send_data:
                        return _ok(file_path, chat_id, message_id=send_data.get("id"))
                return _fail("所有发送端点都失败了")
    except Exception as e:
        logger.exception("direct API 发送异常")
        return _fail(f"发送异常: {str(e)}")


def _upload_file_via_api(client, headers, file_path: str, media_type: int, chat_id: str, file_name: str) -> Optional[Dict]:
    """上传文件到 QQ API，支持用户/群组端点."""
    # 读取并 base64 编码
    file_data = _read_base64(file_path)

    # 根据 chat_id 类型选择端点
    api_suffixes = [f"/v2/users/{chat_id}/files"]
    if chat_id.startswith("group_"):
        api_suffixes.append(f"/v2/groups/{chat_id}/files")

    for suffix in api_suffixes:
        url = f"https://api.sgroup.qq.com{suffix}"
        payload = {
            "file_type": media_type,
            "srv_send_msg": False,
            "file_data": file_data,
            "file_name": file_name,
        }
        try:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                return resp.json()
        except Exception:
            continue
    return None


def _send_message_via_api(client, headers, chat_id: str, payload: Dict, is_group: bool = False) -> Optional[Dict]:
    """发送媒体消息."""
    endpoints = []
    if is_group:
        endpoints.append(f"https://api.sgroup.qq.com/v2/groups/{chat_id}/messages")
    else:
        endpoints.append(f"https://api.sgroup.qq.com/v2/users/{chat_id}/messages")

    for url in endpoints:
        try:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                return resp.json()
        except Exception:
            continue
    return None


# ── Utilities ────────────────────────────────────────────────────────────

def _read_base64(file_path: str) -> str:
    """读取文件并返回 base64 编码."""
    import base64

    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _get_media_type(file_path: Path) -> int:
    """根据扩展名判断 QQ 媒体类型."""
    ext = file_path.suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
        return 1  # 图片
    if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        return 2  # 视频
    if ext in {".mp3", ".wav", ".ogg", ".aac", ".flac", ".amr", ".silk"}:
        return 3  # 语音
    return 4  # 文件


def _run_async(coro):
    """安全地运行异步协程并返回结果，避免 event loop 冲突."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 无运行中的 loop -> 直接运行
        return asyncio.run(coro)
    # 有运行中的 loop，开新线程执行（避免 deadlock）
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


def _safe_json(resp) -> Optional[Dict[str, Any]]:
    """安全解析 HTTP 响应 JSON."""
    try:
        return resp.json()
    except Exception:
        return None


def _ok(file_path: str, chat_id: str, message_id: Optional[str] = None) -> str:
    return json.dumps(
        {"success": True, "file_path": file_path, "chat_id": chat_id, "message_id": message_id},
        ensure_ascii=False,
    )


def _fail(error: str) -> str:
    return json.dumps({"success": False, "error": error}, ensure_ascii=False)


# ── Availability check ───────────────────────────────────────────────────

def _check_qqbot_available() -> bool:
    """检查插件是否可用：gateway 中有 QQ adapter 或环境变量已配置."""
    try:
        runner = _gateway_runner_ref()
        if runner and hasattr(runner, "adapters"):
            return "qqbot" in runner.adapters
    except Exception:
        pass
    return bool(os.getenv("QQ_APP_ID") and os.getenv("QQ_CLIENT_SECRET"))