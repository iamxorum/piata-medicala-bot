# Piața Medicală Bot

Watches [piatamedicala.ro](https://www.piatamedicala.ro/) and sends a Telegram message the moment a new **dentist job** in your specified area gets posted.

## How it works

- Checks the site every 5 minutes (default).
- Sends each new listing once — no repeats.
- Anyone who sends `/start` to your Telegram bot subscribes automatically. `/stop` unsubscribes.
- Runs non-stop in a Docker container on your server.

## Start it

1. Copy `.env.example` to `.env` and fill in your bot token (get it from `@BotFather` on Telegram).
2. Start:
   ```
   docker compose up -d --build
   ```
3. Watch it live:
   ```
   docker compose logs -f
   ```

## Stop it

```
docker compose down
```

## What you can change in `.env`

- `POLL_INTERVAL_SECONDS` — how often it checks the site.
- `INCLUDE_KEYWORDS` / `EXCLUDE_KEYWORDS` — words a listing's title must/must not contain.
- `LOCATION_KEYWORDS` — which cities/counties count (default: Bucuresti, Ilfov).

Each line in `.env` has a comment above it explaining what it does.
