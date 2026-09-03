import requests

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def send_message(token: str, chat_id: int, text: str) -> None:
    url = API_BASE.format(token=token, method="sendMessage")
    response = requests.post(url, data={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=20)
    response.raise_for_status()


def get_updates(token: str, offset: int) -> list[dict]:
    """Short-poll (timeout=0) — potrivit pentru rulare periodica via cron."""
    url = API_BASE.format(token=token, method="getUpdates")
    response = requests.get(url, params={
        "offset": offset,
        "timeout": 0,
        "allowed_updates": '["message"]',
    }, timeout=20)
    response.raise_for_status()
    return response.json().get("result", [])
