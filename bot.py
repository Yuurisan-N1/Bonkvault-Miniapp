import os
import re
import sys
import json
import time
import random
import signal
import asyncio
import aiohttp

from urllib.parse import parse_qs, unquote

from utils.banner import show_banner

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

MY_PROJECT = "Bonk Vault Miniapp"

BASE_URL = "https://bonkvault.ai.studio"
FIREBASE_DB = "https://bonkvault-e1924-default-rtdb.firebaseio.com"
IDENTITY_API = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
SIGNUP_API = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"

FIREBASE_KEY = "AIzaSyD_nS4KFdBPT_esKu4_tSKMI2ClVGxv0Cg"

REF_CODE = "QW9FBONK"

FIREBASE_HOST = "bonkvault.local"
PASSWORD_SUFFIX = "!bonkAuth"

WATCH_FEATURES = (
    ("monetag", "watch_earn_monetag", "Monetag"),
    ("adsgram", "watch_earn_adsgram", "Adsgram"),
)

SPIN_FEATURE = "spin_wheel"
MINER_FEATURE = "miner_card"
CLAIM_FEATURE = "passive_claim"

MINER_CARDS = (
    ("basic", "Basic Miner"),
    ("ultra", "Ultra Miner"),
    ("supreme", "Supreme Miner"),
)

TASK_COLLECTION = "mainTasks"
TASK_DAILY_CAP = 12

GAME_PHASES = (
    ("2048-mini", "2048 Mini"),
    ("candy-match", "Candy Match"),
    ("coin-catcher", "Coin Catcher"),
    ("fruit-ninja", "Fruit Ninja"),
    ("quick-quiz", "Quick Quiz"),
    ("word-game", "Word Scramble"),
)

GAME_PLAYS = {
    "2048-mini": {"maxTileReached": 256, "scoreAchieved": 4200, "movesMade": 180},
    "candy-match": {"score": 1800, "matchesCleared": 40, "combosCount": 9},
    "coin-catcher": {"score": 1200, "coinsCaught": 48, "bombsHit": 1, "maxStreak": 22},
    "fruit-ninja": {"score": 1400, "fruitsSliced": 90, "maxCombo": 18},
}

QUIZ_ANSWERS = (
    ("how many days are in one week", "7 Days"),
    ("how many hours are in 1 full day", "24 Hours"),
    ("what action do players perform in telegram tap to earn games", "Tap the screen or coin"),
    ("what animal is known as the king of the jungle", "Lion"),
    ("what color is a healthy ripe banana", "Yellow"),
    ("what color is the clear daytime sky", "Blue"),
    ("what do we use to see sunlight during the day", "The Sun"),
    ("what do you use to store digital crypto coins safely", "Crypto Wallet"),
    ("what is bitcoin", "Digital money / Crypto"),
    ("what is a secret seed phrase used for", "Backup recovery key for crypto wallet"),
    ("what is a stablecoin like usdt or usdc", "Coin pegged to $1 USD value"),
    ("what is the capital city of india", "New Delhi"),
    ("what is the native coin used for gas fees on solana", "SOL"),
    ("what is the native token of the telegram ton network", "TON"),
    ("what mascot animal is featured on the bonk token logo", "Shiba Inu Dog"),
    ("what planet do we live on", "Earth"),
    ("what sound does a cat make", "Meow"),
    ("what symbol represents bitcoin around the world", "\u20bf"),
    ("which popular messaging app hosts telegram mini apps and bots", "Telegram"),
    ("which tool allows you to search and browse the web", "Web Browser"),
)

MATH_ASK = re.compile(r"what is (\d+)\s*(plus|minus|\+|x|\*)\s*(\d+)", re.IGNORECASE)

WATCH_TABLE = ((13.2, 16.5, 16.5, 19.8, 19.8, 23.1, 24.2, 26.4), (.3, .2, .15, .15, .08, .07, .03, .02))
VISIT_TABLE = ((6.6, 11, 11, 13.2, 14.3, 15.4), (.35, .25, .2, .1, .07, .03))
SPIN_TABLE = ((7.7, 11, 13.2, 15.4, 18.7, 19.8, 24.2), (.35, .25, .2, .1, .05, .03, .02))

WATCH_PROVIDER_TABLE = ((35.0, 50.0),)

MINER_ADS = {"basic": 10, "ultra": 25, "supreme": 20}
MINER_RATE = {"basic": 22.0, "ultra": 40.7, "supreme": 121.0}
MINER_LIFE_MINUTES = {"basic": 1440, "ultra": 720, "supreme": 180}

LIMIT_KEYS = (("watchLimitPerDay", "watch"), ("visitLimitPerDay", "visit"), ("spinLimitPerDay", "spin"))
COUNTER_KEYS = (("watch", "watchCount", "lastWatchAt"), ("visit", "visitCount", "lastVisitAt"),
                ("spin", "spinCount", "lastSpinAt"))

AD_WATCH_SECONDS = 15
COOLDOWN_SECONDS = 0
CALL_ATTEMPTS = 3
CALL_RETRY_SECONDS = 4
ACTION_PAUSE_SECONDS = 2
RATE_LIMIT_PAUSE_SECONDS = 8
NAME_LIMIT = 18
TASK_NAME_LIMIT = 24
DAY_MS = 86400000

BANNED_CODES = (
    91, 93, 124, 35, 33, 64, 36, 37, 94, 38, 42, 40, 41,
    45, 44, 58, 59, 39, 34, 96, 126, 43, 61, 60, 62, 63, 47, 92,
)
BANNED_CHARS = tuple(chr(code) for code in BANNED_CODES)

PAGE_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
)


def log_green(msg):
    print(f"{GREEN}{BOLD}{msg}{RESET}", flush=True)


def log_yellow(msg):
    print(f"{YELLOW}{BOLD}{msg}{RESET}", flush=True)


def log_red(msg):
    print(f"{RED}{BOLD}{msg}{RESET}", flush=True)


def signal_handler(sig, frame):
    print(flush=True)
    log_red("Script stopped by user")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def clean_text(value, fallback):
    if value is None:
        return str(fallback)
    text = str(value)
    for symbol in BANNED_CHARS:
        text = text.replace(symbol, " ")
    text = "".join(char for char in text if ord(char) < 128)
    text = " ".join(text.split())
    return text if text else str(fallback)


def shorten(value, fallback, limit):
    text = clean_text(value, fallback)
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    space = cut.rfind(" ")
    return cut[:space].rstrip() if space > 0 else text[:limit].rstrip()


def number_of(mapping, key, fallback=0):
    if not isinstance(mapping, dict):
        return fallback
    try:
        return int(float(mapping.get(key)))
    except (TypeError, ValueError):
        return fallback


def decimal_of(mapping, key, fallback=0.0):
    if not isinstance(mapping, dict):
        return fallback
    try:
        return float(mapping.get(key))
    except (TypeError, ValueError):
        return fallback


def stamp_of(mapping, key, fallback=0):
    if not isinstance(mapping, dict):
        return fallback
    try:
        return int(float(mapping.get(key)))
    except (TypeError, ValueError):
        return fallback


def parse_payload(body):
    try:
        payload = json.loads(body)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_config():
    defaults = {
        "settings": {
            "sleep_seconds": 3600,
        }
    }
    if not os.path.exists("config.json"):
        return defaults
    try:
        with open("config.json") as handle:
            loaded = json.load(handle)
    except Exception:
        return defaults
    settings = loaded.get("settings")
    if not isinstance(settings, dict):
        return defaults
    merged = dict(defaults["settings"])
    merged.update(settings)
    return {"settings": merged}


def load_lines(filename, required):
    if not os.path.exists(filename):
        if required:
            log_red(f"File {clean_text(filename, 'data.txt')} was not found")
            sys.exit(1)
        return []
    lines = [line.strip() for line in open(filename).readlines() if line.strip()]
    if required and not lines:
        log_red("File data.txt is empty and holds no initData string")
        sys.exit(1)
    return lines


def parse_init_data(line):
    value = line.strip()
    if "|" in value:
        value = value.rsplit("|", 1)[0].strip()
    if "tgWebAppData=" in value:
        value = value.split("tgWebAppData=", 1)[1]
        value = value.split("&tgWebAppVersion")[0].split("&tgWebAppPlatform")[0]
        value = unquote(value)
    fields = parse_qs(value, keep_blank_values=True)
    raw_user = (fields.get("user") or [""])[0]
    if not raw_user:
        return None
    try:
        profile = json.loads(raw_user)
    except Exception:
        try:
            profile = json.loads(unquote(raw_user))
        except Exception:
            return None
    if not isinstance(profile, dict) or not profile.get("id"):
        return None
    return {
        "initData": value,
        "id": str(profile.get("id")),
        "username": str(profile.get("username") or ""),
        "firstName": str(profile.get("first_name") or ""),
        "lastName": str(profile.get("last_name") or ""),
        "startParam": str((fields.get("start_param") or [""])[0]),
    }


def display_name(account):
    for candidate in (account.get("firstName"), account.get("username")):
        if candidate:
            return candidate
    return "account"


def normalize_proxy(proxy_line):
    if not proxy_line:
        return None
    value = proxy_line.strip()
    if "://" in value:
        return value
    parts = value.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"
    if len(parts) == 3:
        host, port, user = parts
        return f"http://{user}@{host}:{port}"
    return f"http://{value}"


def mask_proxy(proxy_url):
    try:
        value = proxy_url.split("://")[-1]
        after_at = value.split("@")[-1]
        host_part = after_at.split(":")[0]
        port_part = after_at.split(":")[1] if ":" in after_at else ""
        octets = host_part.split(".")
        if len(octets) == 4:
            masked_host = f"{octets[0]}*****{octets[3]}"
        elif len(host_part) > 4:
            masked_host = f"{host_part[:2]}*****{host_part[-2:]}"
        else:
            masked_host = "***"
        suffix = f":{port_part}" if port_part else ""
        return f"http://user:pass@{masked_host}{suffix}"
    except Exception:
        return "http://user:pass@***:***"


def countdown(seconds, label):
    total = int(seconds)
    if total < 1:
        return
    line = ""
    for remaining in range(total, 0, -1):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        rest = remaining % 60
        line = f"{clean_text(label, 'item')} {hours:02d}:{minutes:02d}:{rest:02d}"
        print(f"\r{YELLOW}{BOLD}{line}{RESET}", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * (len(line) + 6) + "\r", end="", flush=True)


def utc_day(offset_hours=0):
    return time.strftime("%Y-%m-%d", time.gmtime(time.time() + offset_hours * 3600))


def roll(values, weights):
    chance = random.random()
    total = 0.0
    for value, weight in zip(values, weights):
        total += weight
        if chance < total:
            return float(value)
    return float(values[-1])


def roll_range(values):
    low, high = values
    return float(random.randint(int(low), int(high)))


def math_answer(text):
    found = MATH_ASK.search(text)
    if not found:
        return ""
    first = int(found.group(1))
    second = int(found.group(3))
    operator = found.group(2).lower()
    if operator in ("plus", "+"):
        total = first + second
    elif operator in ("x", "*"):
        total = first * second
    else:
        total = first - second
    return str(total)


def quiz_choice(question, options):
    text = str(question or "")
    expected = math_answer(text)
    if not expected:
        lowered = text.lower()
        for fragment, answer in QUIZ_ANSWERS:
            if fragment in lowered:
                expected = answer
                break
    if expected:
        for index, option in enumerate(options):
            if str(option).strip().lower() == expected.strip().lower():
                return index
    return 0


def round_answers(slug, payload):
    if slug == "word-game":
        words = [str(item.get("targetWord") or "") for item in payload.get("challenges") or []]
        words = [word for word in words if word]
        if not words:
            return None
        return {"solvedAnswers": words}
    if slug == "quick-quiz":
        questions = payload.get("questions") or []
        if not questions:
            return None
        choices = [quiz_choice(item.get("question"), item.get("options") or [])
                   for item in questions]
        return {"userAnswers": choices}
    plays = GAME_PLAYS.get(slug)
    return dict(plays) if plays else None


def event_id(prefix, uid):
    stamp = int(time.time() * 1000)
    tail = "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(8))
    return f"ad_{prefix}_{str(uid)[:16]}_{stamp}_{tail}"


async def call_json(session, method, url, proxy, payload, token):
    last_status = 0
    last_body = ""
    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": BASE_URL,
        "referer": BASE_URL + "/",
        "user-agent": PAGE_AGENT,
    }
    if token:
        headers["authorization"] = "Bearer " + token
    if payload is not None:
        headers["content-type"] = "application/json"
    for attempt in range(1, CALL_ATTEMPTS + 1):
        pause = CALL_RETRY_SECONDS * attempt
        body_text = json.dumps(payload) if payload is not None else None
        try:
            request = session.request(
                method,
                url,
                data=body_text,
                headers=headers,
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=40),
            )
            async with request as response:
                last_status = response.status
                last_body = await response.text()
                if response.status < 500 and response.status != 429:
                    return last_status, last_body
                if response.status == 429:
                    pause = RATE_LIMIT_PAUSE_SECONDS * attempt
        except Exception:
            last_status = 0
            last_body = ""
        if attempt < CALL_ATTEMPTS:
            countdown(pause, "Retry in")
    return last_status, last_body


class Vault:
    def __init__(self, session, uid, token, proxy):
        self.session = session
        self.uid = uid
        self.token = token
        self.proxy = proxy

    async def _request(self, method, path, payload=None):
        url = f"{FIREBASE_DB}/{path}.json?auth={self.token}"
        status, body = await call_json(self.session, method, url, self.proxy, payload, "")
        parsed = parse_payload(body)
        if isinstance(parsed, dict) and "error" in parsed and len(parsed) == 1:
            return status, {}
        return status, parsed

    async def read(self, path=""):
        suffix = f"/{path}" if path else ""
        status, data = await self._request("GET", f"users/{self.uid}{suffix}")
        return data

    async def write(self, path, payload):
        suffix = f"/{path}" if path else ""
        return await self._request("PATCH", f"users/{self.uid}{suffix}", payload)

    async def public(self, path):
        status, data = await self._request("GET", path)
        return data


async def firebase_session(session, proxy, telegram_id):
    email = f"tg_{telegram_id}@{FIREBASE_HOST}"
    password = f"Tg{telegram_id}{PASSWORD_SUFFIX}"
    body = {"email": email, "password": password, "returnSecureToken": True}
    for endpoint in (IDENTITY_API, SIGNUP_API):
        status, text = await call_json(session, "POST", f"{endpoint}?key={FIREBASE_KEY}",
                                       proxy, body, "")
        payload = parse_payload(text)
        if payload.get("idToken") and payload.get("localId"):
            return {"uid": str(payload["localId"]), "token": str(payload["idToken"]),
                    "email": email}
    return None


async def register_user(session, proxy, account):
    await call_json(
        session, "POST", BASE_URL + "/api/telegram/register-user", proxy,
        {
            "id": int(account["id"]),
            "username": account["username"],
            "firstName": account["firstName"],
            "lastName": account["lastName"],
            "refCode": account["refCode"],
        }, "")


def default_profile(uid, account):
    return {
        "uid": uid,
        "fullName": f"{account['firstName']} {account['lastName']}".strip() or "Vault Member",
        "email": f"tg_{account['id']}@{FIREBASE_HOST}",
        "availableBalance": 0,
        "tBonkBalance": 1000,
        "dailyEarned": 0,
        "dailyEarnedDate": utc_day(),
        "lifetimeEarned": 0,
        "lifetimeWithdrawal": 0,
        "totalVisits": 0,
        "totalWatchAds": 0,
        "accountStatus": "active",
        "currentStreak": 0,
        "lastClaimedStreakAt": None,
        "referralCount": 0,
        "pendingReferralCount": 0,
        "referralRewardClaimed": False,
        "createdAt": int(time.time() * 1000),
        "lastLogin": int(time.time() * 1000),
    }


def touch_daily_earned(state, amount):
    today = utc_day()
    if state.get("dailyEarnedDate") != today:
        state["dailyEarned"] = amount
        state["dailyEarnedDate"] = today
    else:
        state["dailyEarned"] = number_of(state, "dailyEarned") + amount


def touch_activity(state, bucket, step=1):
    today = utc_day(5.5)
    activity = state.get("dailyActivity")
    if not isinstance(activity, dict) or activity.get("dateKey") != today:
        activity = {"dateKey": today, "watchCount": 0, "visitCount": 0, "spinCount": 0,
                    "activeSeconds": 0}
    field = {"watch": "watchCount", "visit": "visitCount", "spin": "spinCount"}.get(bucket)
    if field:
        activity[field] = number_of(activity, field) + step
    state["dailyActivity"] = activity


def touch_ad_ledger(state, feature, card_id=None):
    ledger = state.get("processedAdEvents")
    if not isinstance(ledger, dict):
        ledger = {}
    ledger[event_id(feature, state.get("uid", ""))] = {
        "feature": feature,
        "cardId": card_id,
        "timestamp": int(time.time() * 1000),
        "accepted": True,
    }
    keys = list(ledger.keys())
    if len(keys) > 150:
        for old in keys[: len(keys) - 150]:
            ledger.pop(old, None)
    state["processedAdEvents"] = ledger


def reset_counters(state):
    now = int(time.time() * 1000)
    for bucket, counter, stamp in COUNTER_KEYS:
        last = stamp_of(state, stamp)
        if last and now - last > DAY_MS:
            state[counter] = 0


def grant(state, amount):
    state["availableBalance"] = decimal_of(state, "availableBalance") + amount
    state["lifetimeEarned"] = decimal_of(state, "lifetimeEarned") + amount
    touch_daily_earned(state, amount)


def credit_watch(state, provider):
    feature = dict((key, item) for key, item, _ in WATCH_FEATURES)[provider]
    amount = roll_range(WATCH_PROVIDER_TABLE[0]) if provider == "adsgram" else roll(*WATCH_TABLE)
    grant(state, amount)
    state["tBonkBalance"] = number_of(state, "tBonkBalance", 1000) + 100
    state["totalWatchAds"] = number_of(state, "totalWatchAds") + 1
    state["watchCount"] = number_of(state, "watchCount") + 1
    now = int(time.time() * 1000)
    state["lastWatchAt"] = now
    state["lastRewardedAdAt"] = now
    touch_activity(state, "watch")
    touch_ad_ledger(state, feature)
    return amount


def credit_visit(state):
    amount = roll(*VISIT_TABLE)
    grant(state, amount)
    state["totalVisits"] = number_of(state, "totalVisits") + 1
    state["visitCount"] = number_of(state, "visitCount") + 1
    now = int(time.time() * 1000)
    state["lastVisitAt"] = now
    state["lastRewardedAdAt"] = now
    touch_activity(state, "visit")
    return amount


def credit_spin(state):
    amount = roll(*SPIN_TABLE)
    grant(state, amount)
    now = int(time.time() * 1000)
    state["lastSpinAt"] = now
    state["lastRewardedAdAt"] = now
    state["spinCount"] = number_of(state, "spinCount") + 1
    touch_activity(state, "spin")
    touch_ad_ledger(state, SPIN_FEATURE)
    return amount


def credit_task(state, task):
    done = state.get("completedMainTasks")
    if not isinstance(done, dict):
        done = {}
    task_id = str(task.get("id"))
    if not task_id or done.get(task_id):
        return 0.0
    amount = decimal_of(task, "reward")
    if amount <= 0:
        return 0.0
    grant(state, amount)
    done[task_id] = int(time.time() * 1000)
    state["completedMainTasks"] = done
    return amount


def miner_ads_done(state, card):
    cards = state.get("passiveCards")
    counts = cards.get("adCounts") if isinstance(cards, dict) else None
    return number_of(counts, card) if isinstance(counts, dict) else 0


def credit_miner_ad(state, card):
    required = number_of(MINER_ADS, card)
    cards = state.get("passiveCards")
    if not isinstance(cards, dict):
        cards = {}
    counts = cards.get("adCounts")
    if not isinstance(counts, dict):
        counts = {key: 0 for key, _ in MINER_CARDS}
    if number_of(counts, card) >= required:
        return False
    counts[card] = number_of(counts, card) + 1
    cards["adCounts"] = counts
    state["passiveCards"] = cards
    touch_ad_ledger(state, MINER_FEATURE, card)
    return True


def can_activate(state, card):
    required = number_of(MINER_ADS, card)
    if miner_ads_done(state, card) < required:
        return f"{required} validated ads are required before this card activates"
    cards = state.get("passiveCards") or {}
    if not isinstance(cards, dict):
        return "The miner card record is not readable"
    times = cards.get("activationTimes") or {}
    now = int(time.time() * 1000)
    owned = list(cards.get("owned") or [])
    if card == "supreme":
        for key in ("basic", "ultra"):
            life = number_of(MINER_LIFE_MINUTES, key) * 60000
            if now - stamp_of(times, key) >= life:
                return "Both the basic and the ultra miner have to run before this card opens"
    pending = 0.0
    last_claim = stamp_of(cards, "lastClaim")
    if owned and last_claim:
        rate = 0.0
        for item in owned:
            life = number_of(MINER_LIFE_MINUTES, item) * 60000
            if now - stamp_of(times, item) < life:
                rate += decimal_of(MINER_RATE, item)
        pending = (now - last_claim) / 3600000.0 * rate
    counts = dict(cards.get("adCounts") or {})
    counts[card] = 0
    if card not in owned:
        owned.append(card)
    times[card] = now
    cards["adCounts"] = counts
    cards["owned"] = owned
    cards["activationTimes"] = times
    cards["lastClaim"] = now
    cards["accumulated"] = decimal_of(cards, "accumulated") + pending
    state["passiveCards"] = cards
    return ""


def claim_passive(state):
    cards = state.get("passiveCards")
    if not isinstance(cards, dict):
        return 0.0
    owned = list(cards.get("owned") or [])
    if not owned:
        return 0.0
    times = cards.get("activationTimes") or {}
    now = int(time.time() * 1000)
    last_claim = stamp_of(cards, "lastClaim")
    rate = 0.0
    for item in owned:
        life = number_of(MINER_LIFE_MINUTES, item) * 60000
        if now - stamp_of(times, item) < life:
            rate += decimal_of(MINER_RATE, item)
    hours = (now - last_claim) / 3600000.0 if last_claim else 0.0
    pending = int(decimal_of(cards, "accumulated") + hours * rate)
    if pending <= 0:
        return 0.0
    grant(state, pending)
    cards["lastClaim"] = now
    cards["accumulated"] = 0
    state["passiveCards"] = cards
    return float(pending)


async def push_state(vault, state, keys):
    payload = {key: state[key] for key in keys if key in state}
    if not payload:
        return None
    status, _ = await vault.write("", payload)
    if status != 200:
        return None
    fresh = await vault.read()
    return fresh if isinstance(fresh, dict) else None


def confirmed_balance(fresh):
    return decimal_of(fresh, "availableBalance")


def movement(balance, previous):
    return balance - previous, int(round(balance)) - int(round(previous))


def tally(track, amount):
    if amount > 0:
        track[0] += amount


async def phase_tasks(vault, state, monitor, track):
    tasks = await vault.public(TASK_COLLECTION)
    if not isinstance(tasks, dict):
        log_yellow("The task board could not be read on this run")
        return 0
    board = []
    for key, item in tasks.items():
        if isinstance(item, dict) and item.get("active") is not False:
            board.append(dict(item, id=key))
    board.sort(key=lambda item: decimal_of(item, "reward"), reverse=True)
    done = state.get("completedMainTasks") or {}
    claimed = 0.0
    for task in board[:TASK_DAILY_CAP]:
        if done.get(str(task.get("id"))):
            continue
        label = shorten(task.get("title") or task.get("description"), "sponsored task",
                        TASK_NAME_LIMIT)
        amount = credit_task(state, task)
        if amount <= 0:
            continue
        fresh = await push_state(vault, state, ("availableBalance", "lifetimeEarned", "dailyEarned",
                                               "dailyEarnedDate", "completedMainTasks"))
        if not fresh:
            log_yellow(f"Task {clean_text(label, 'sponsored task')} did not confirm on the server")
            resync = await vault.read()
            if isinstance(resync, dict):
                state.update(resync)
                monitor = confirmed_balance(resync)
            continue
        balance = confirmed_balance(fresh)
        delta, shown = movement(balance, monitor)
        state.update(fresh)
        done = state.get("completedMainTasks") or {}
        if delta <= 0:
            log_yellow(f"Task {clean_text(label, 'sponsored task')} credits no balance movement")
            continue
        claimed += delta
        monitor = balance
        tally(track, delta)
        log_green(f"Task {clean_text(label, 'sponsored task')} credited "
                  f"{clean_text(shown, 0)} BONK, vault now "
                  f"{clean_text(int(round(balance)), 0)}")
        countdown(ACTION_PAUSE_SECONDS, "Next task in")
    if claimed <= 0:
        log_yellow("Every sponsored task on the board was already collected")
    return monitor


async def phase_miner(vault, state, monitor, track):
    for card, label in MINER_CARDS:
        required = number_of(MINER_ADS, card)
        recorded = 0
        while miner_ads_done(state, card) < required:
            if not credit_miner_ad(state, card):
                break
            recorded += 1
        if not recorded:
            continue
        fresh = await push_state(vault, state, ("lastRewardedAdAt", "passiveCards"))
        if not fresh:
            log_yellow(f"{clean_text(label, 'Miner card')} ad records did not confirm")
            continue
        state.update(fresh)
        log_green(f"{clean_text(label, 'Miner card')} now holds "
                  f"{clean_text(miner_ads_done(state, card), 0)} of "
                  f"{clean_text(required, 0)} validated ads")
        countdown(COOLDOWN_SECONDS, "Next card in")
    for card, label in MINER_CARDS:
        if ledger_has(state, card):
            continue
        reason = can_activate(state, card)
        if reason:
            log_yellow(f"{clean_text(label, 'Miner card')} is not ready: "
                       f"{clean_text(reason, 'not ready')}")
            continue
        fresh = await push_state(vault, state, ("passiveCards",))
        if not fresh:
            log_yellow(f"{clean_text(label, 'Miner card')} activation did not confirm")
            continue
        state.update(fresh)
        log_green(f"{clean_text(label, 'Miner card')} is now running")
        countdown(ACTION_PAUSE_SECONDS, "Next card in")
    return monitor


async def phase_watch(vault, state, monitor, limits, track):
    limit = number_of(limits, "watchLimitPerDay")
    count = number_of(state, "watchCount")
    if count >= limit:
        log_yellow(f"Watch and earn is already at {clean_text(count, 0)} of "
                   f"{clean_text(limit, 0)} for today")
        return monitor
    gained = 0.0
    turn = 0
    while number_of(state, "watchCount") < limit:
        provider, feature, label = WATCH_FEATURES[turn % len(WATCH_FEATURES)]
        turn += 1
        credit_watch(state, provider)
        fresh = await push_state(vault, state, (
            "availableBalance", "lifetimeEarned", "dailyEarned", "dailyEarnedDate",
            "tBonkBalance", "totalWatchAds", "watchCount", "lastWatchAt",
            "lastRewardedAdAt", "dailyActivity", "processedAdEvents"))
        if not fresh:
            log_yellow(f"{clean_text(label, 'provider')} credit did not confirm on the server")
            return monitor
        balance = confirmed_balance(fresh)
        delta, shown = movement(balance, monitor)
        state.update(fresh)
        if delta <= 0:
            log_yellow(f"{clean_text(label, 'provider')} credit left the vault unchanged")
            return monitor
        gained += delta
        monitor = balance
        tally(track, delta)
        log_green(f"{clean_text(label, 'provider')} ad credited "
                  f"{clean_text(shown, 0)} BONK, vault now "
                  f"{clean_text(int(round(balance)), 0)}")
        countdown(COOLDOWN_SECONDS, "Next ad in")
    if gained <= 0:
        log_yellow("No watch and earn slot could be credited on this run")
    return monitor


async def phase_visit(vault, state, monitor, limits, track):
    limit = number_of(limits, "visitLimitPerDay")
    count = number_of(state, "visitCount")
    if count >= limit:
        log_yellow(f"Visit and earn is already at {clean_text(count, 0)} of "
                   f"{clean_text(limit, 0)} for today")
        return monitor
    gained = 0.0
    while number_of(state, "visitCount") < limit:
        credit_visit(state)
        fresh = await push_state(vault, state, (
            "availableBalance", "lifetimeEarned", "dailyEarned", "dailyEarnedDate",
            "totalVisits", "visitCount", "lastVisitAt", "lastRewardedAdAt", "dailyActivity"))
        if not fresh:
            log_yellow("The visit credit did not confirm on the server")
            return monitor
        balance = confirmed_balance(fresh)
        delta, shown = movement(balance, monitor)
        state.update(fresh)
        if delta <= 0:
            log_yellow("The visit credit left the vault unchanged")
            return monitor
        gained += delta
        monitor = balance
        tally(track, delta)
        log_green(f"Visit credited {clean_text(shown, 0)} BONK, "
                  f"vault now {clean_text(int(round(balance)), 0)}")
        countdown(COOLDOWN_SECONDS, "Next visit in")
    if gained <= 0:
        log_yellow("No visit slot could be credited on this run")
    return monitor


async def phase_spin(vault, state, monitor, limits, track):
    limit = number_of(limits, "spinLimitPerDay")
    count = number_of(state, "spinCount")
    if count >= limit:
        log_yellow(f"Spin and earn is already at {clean_text(count, 0)} of "
                   f"{clean_text(limit, 0)} for today")
        return monitor
    gained = 0.0
    while number_of(state, "spinCount") < limit:
        credit_spin(state)
        fresh = await push_state(vault, state, (
            "availableBalance", "lifetimeEarned", "dailyEarned", "dailyEarnedDate",
            "lastSpinAt", "lastRewardedAdAt", "spinCount", "dailyActivity",
            "processedAdEvents"))
        if not fresh:
            log_yellow("The spin credit did not confirm on the server")
            return monitor
        balance = confirmed_balance(fresh)
        delta, shown = movement(balance, monitor)
        state.update(fresh)
        if delta <= 0:
            log_yellow("The spin credit left the vault unchanged")
            return monitor
        gained += delta
        monitor = balance
        tally(track, delta)
        log_green(f"Spin credited {clean_text(shown, 0)} BONK, "
                  f"vault now {clean_text(int(round(balance)), 0)}")
        countdown(COOLDOWN_SECONDS, "Next spin in")
    if gained <= 0:
        log_yellow("No spin slot could be credited on this run")
    return monitor


async def phase_games(vault, session, proxy, account, monitor, track):
    credited = 0.0
    missed = 0
    for slug, label in GAME_PHASES:
        status, body = await call_json(
            session, "POST", f"{BASE_URL}/api/{slug}/credit-chance", proxy,
            {"uid": vault.uid, "eventId": event_id(slug, vault.uid),
             "durationSeconds": AD_WATCH_SECONDS}, "")
        if status != 200:
            missed += 1
            continue
        status, body = await call_json(
            session, "POST", f"{BASE_URL}/api/{slug}/start-round", proxy,
            {"uid": vault.uid}, "")
        round_payload = parse_payload(body)
        if status != 200 or not round_payload.get("roundId"):
            missed += 1
            continue
        answers = round_answers(slug, round_payload)
        if not answers:
            missed += 1
            continue
        answers["uid"] = vault.uid
        answers["roundId"] = round_payload["roundId"]
        status, body = await call_json(
            session, "POST", f"{BASE_URL}/api/{slug}/submit-round", proxy, answers, "")
        result = parse_payload(body)
        if status != 200 or not result.get("success"):
            missed += 1
            continue
        points = number_of(result, "pointsAwarded")
        if points > 0:
            credited += points
            tally(track, points)
            log_green(f"{clean_text(label, 'game')} round was credited "
                      f"{clean_text(points, 0)} BONK")
        else:
            missed += 1
        countdown(ACTION_PAUSE_SECONDS, "Next game in")
    if missed:
        log_yellow(f"{clean_text(missed, 0)} game rounds could not be credited on this run")
    elif credited == 0:
        log_yellow("No game round returned a confirmed credit on this run")
    return monitor


async def phase_passive(vault, state, monitor, track):
    if not any(ledger_has(state, card) for card, _ in MINER_CARDS):
        return monitor
    amount = claim_passive(state)
    if amount <= 0:
        log_yellow("The passive vault has not accumulated BONK yet")
        return monitor
    fresh = await push_state(vault, state, ("availableBalance", "lifetimeEarned", "dailyEarned",
                                           "dailyEarnedDate", "passiveCards"))
    if not fresh:
        log_yellow("The passive claim did not confirm on the server")
        return monitor
    balance = confirmed_balance(fresh)
    delta, shown = movement(balance, monitor)
    state.update(fresh)
    if delta <= 0:
        log_yellow("The passive claim left the vault unchanged")
        return monitor
    log_green(f"Passive mining credited {clean_text(shown, 0)} BONK, "
              f"vault now {clean_text(int(round(balance)), 0)}")
    tally(track, delta)
    return balance


def ledger_has(state, card):
    cards = state.get("passiveCards")
    if not isinstance(cards, dict):
        return False
    owned = cards.get("owned") or []
    return card in owned


async def read_limits(vault):
    settings = await vault.public("settings")
    return settings if isinstance(settings, dict) else {}


async def process_account(line, proxy, index):
    account = parse_init_data(line)
    if not account:
        log_red(f"Credential line {clean_text(index, 1)} is not valid initData")
        return
    account["refCode"] = account["startParam"].upper() or REF_CODE

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        auth = await firebase_session(session, proxy, account["id"])
        if not auth:
            log_red(f"Sign in failed for account number {clean_text(index, 1)}")
            return

        await register_user(session, proxy, account)
        vault = Vault(session, auth["uid"], auth["token"], proxy)

        state = await vault.read()
        if not isinstance(state, dict):
            status, _ = await vault.write("", default_profile(auth["uid"], account))
            if status != 200:
                log_red(f"The vault profile could not be created for line "
                        f"{clean_text(index, 1)}")
                return
            state = await vault.read()
        if not isinstance(state, dict):
            log_red(f"The vault profile is unreadable for account number {clean_text(index, 1)}")
            return

        reset_counters(state)
        limits = await read_limits(vault)
        name = shorten(display_name(account), "account", NAME_LIMIT)
        start = decimal_of(state, "availableBalance")
        log_green(f"Signed in {clean_text(name, 'account')} with "
                  f"{clean_text(int(start), 0)} BONK in the vault")
        await vault.write("", {"lastLogin": int(time.time() * 1000),
                               "accountStatus": "active"})

        monitor = start
        track = [0.0]
        monitor = await phase_tasks(vault, state, monitor, track)
        monitor = await phase_miner(vault, state, monitor, track)
        monitor = await phase_watch(vault, state, monitor, limits, track)
        monitor = await phase_visit(vault, state, monitor, limits, track)
        monitor = await phase_spin(vault, state, monitor, limits, track)
        monitor = await phase_games(vault, session, proxy, account, monitor, track)
        settled = await vault.read()
        if isinstance(settled, dict):
            state.update(settled)
            monitor = confirmed_balance(settled)
        monitor = await phase_passive(vault, state, monitor, track)

        fresh = await vault.read()
        if isinstance(fresh, dict):
            end = decimal_of(fresh, "availableBalance")
            if end > start:
                log_green(f"Vault balance rose from {clean_text(int(round(start)), 0)} to "
                          f"{clean_text(int(round(end)), 0)} BONK")
            else:
                log_yellow("Vault balance stayed unchanged after this run")
            if abs((end - start) - track[0]) > 1:
                log_yellow(f"Claims reported {clean_text(int(round(track[0])), 0)} BONK but the "
                           f"vault moved {clean_text(int(round(end - start)), 0)}")


async def main_async(accounts, proxies, sleep_secs):
    cycle = 1
    while True:
        log_yellow(f"Starting automation cycle number {clean_text(cycle, 0)}")

        for index, line in enumerate(accounts):
            if index > 0:
                print()

            proxy_line = proxies[index % len(proxies)] if proxies else None
            proxy_url = normalize_proxy(proxy_line) if proxy_line else None
            if proxy_url:
                log_yellow(f"Using proxy {mask_proxy(proxy_url)}")

            await process_account(line, proxy_url, index + 1)
            countdown(ACTION_PAUSE_SECONDS, "Next account in")

        log_yellow(f"Automation cycle number {clean_text(cycle, 0)} is complete")
        cycle += 1
        countdown(sleep_secs, "Next cycle starts in")
        show_banner(MY_PROJECT)


def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

    show_banner(MY_PROJECT)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    settings = load_config().get("settings", {})
    accounts = load_lines("data.txt", True)
    proxies = load_lines("proxy.txt", False)
    asyncio.run(main_async(accounts, proxies, settings["sleep_seconds"]))


if __name__ == "__main__":
    main()
