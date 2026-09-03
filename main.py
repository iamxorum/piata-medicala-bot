import os
import sys
import time

import requests
from dotenv import load_dotenv

from scraper import fetch_matching_ads
from storage import load_state, save_state, load_subscribers, save_subscribers
from telegram_client import send_message, get_updates


def _split_list(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def load_config() -> dict:
    return {
        "pages_to_check": int(os.environ.get("PAGES_TO_CHECK", "3")),
        "include_keywords": _split_list(os.environ.get("INCLUDE_KEYWORDS", "medic")),
        "exclude_keywords": _split_list(os.environ.get("EXCLUDE_KEYWORDS", "asistent,receptioner,receptie")),
        "location_keywords": _split_list(os.environ.get("LOCATION_KEYWORDS", "bucuresti,ilfov")),
        "max_seen_ids": int(os.environ.get("MAX_SEEN_IDS", "3000")),
    }


def process_telegram_commands(token: str, subscribers: dict) -> None:
    """Citeste mesaje noi (/start, /stop) si actualizeaza lista de abonati."""
    updates = get_updates(token, subscribers["update_offset"])
    changed = False

    for update in updates:
        subscribers["update_offset"] = update["update_id"] + 1
        message = update.get("message")
        if not message or "text" not in message:
            continue

        chat_id = message["chat"]["id"]
        text = message["text"].strip().lower()

        if text.startswith("/start"):
            if chat_id not in subscribers["chat_ids"]:
                subscribers["chat_ids"].append(chat_id)
                changed = True
                send_message(token, chat_id,
                              "Te-ai abonat! Vei primi aici anunturi noi de "
                              "medic stomatolog in Bucuresti/Ilfov de pe piatamedicala.ro. "
                              "Trimite /stop oricand ca sa te dezabonezi.")
            else:
                send_message(token, chat_id, "Esti deja abonat.")
        elif text.startswith("/stop"):
            if chat_id in subscribers["chat_ids"]:
                subscribers["chat_ids"].remove(chat_id)
                changed = True
                send_message(token, chat_id, "Te-ai dezabonat. Trimite /start ca sa te reabonezi.")

    if updates or changed:
        save_subscribers(subscribers)


def broadcast(token: str, subscribers: dict, ad: dict) -> None:
    text = (
        f"🦷 <b>{ad['title']}</b>\n"
        f"📍 {ad['location']}\n"
        f"📅 {ad['date']}\n"
        f"{ad['url']}"
    )
    removed = []
    for chat_id in subscribers["chat_ids"]:
        try:
            send_message(token, chat_id, text)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 403:
                removed.append(chat_id)
            else:
                print(f"  eroare la trimiterea catre {chat_id}: {exc}")
        except requests.RequestException as exc:
            print(f"  eroare la trimiterea catre {chat_id}: {exc}")

    if removed:
        subscribers["chat_ids"] = [c for c in subscribers["chat_ids"] if c not in removed]
        save_subscribers(subscribers)


def tick(token: str) -> None:
    config = load_config()
    state = load_state()
    subscribers = load_subscribers()

    process_telegram_commands(token, subscribers)

    if not subscribers["chat_ids"]:
        print("Niciun abonat inca — trimiteti /start catre bot din Telegram.")
        return

    matching_ads = fetch_matching_ads(config)
    seen_ids = set(state["seen_ids"])

    if not state["first_run_done"]:
        print(f"Prima rulare: {len(matching_ads)} anunturi curente salvate, fara notificari.")
        state["seen_ids"] = list(seen_ids | {ad["id"] for ad in matching_ads})
        state["first_run_done"] = True
        save_state(state, config["max_seen_ids"])
        return

    new_ads = [ad for ad in matching_ads if ad["id"] not in seen_ids]
    if not new_ads:
        print("Niciun anunt nou.")
        return

    print(f"Anunturi noi: {len(new_ads)} -> {len(subscribers['chat_ids'])} abonati")
    for ad in new_ads:
        broadcast(token, subscribers, ad)
        seen_ids.add(ad["id"])
        print(f"  trimis: {ad['title']} ({ad['url']})")

    state["seen_ids"] = list(seen_ids)
    save_state(state, config["max_seen_ids"])


def main() -> None:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Lipseste TELEGRAM_BOT_TOKEN din .env. Copiaza .env.example in .env si completeaza-l.")
        sys.exit(1)

    interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))
    run_once = os.environ.get("RUN_ONCE", "false").lower() == "true"

    while True:
        try:
            tick(token)
        except Exception as exc:  # nu lasa o eroare trecatoare (retea etc) sa opreasca bucla
            print(f"Eroare neasteptata: {exc}")

        if run_once:
            break

        sys.stdout.flush()
        time.sleep(interval)


if __name__ == "__main__":
    main()
