<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=Bonk%20Vault%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=Auto%20Sponsored%20Tasks%20%7C%20Watch%20and%20Earn%20%7C%20Miner%20Cards%20%7C%20Mini%20Games%20%7C%20Multi-Account&descAlign=50&descAlignY=58"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Auto%20Sponsored%20Tasks%20%7C%20Settle%20Every%20Open%20Task;Watch%20and%20Earn%20%7C%20Monetag%20%26%20Adsgram%20Until%20Daily%20Cap;Visit%20and%20Earn%20%7C%20Spin%20and%20Earn%20%7C%20Daily%20Slots;Miner%20Cards%20%7C%20Basic%20%2F%20Ultra%20%2F%20Supreme%20%2B%20Passive%20Sync;Auto%20Six%20Mini%20Games%20%7C%20Proxy%20Support%20%7C%20Multi-Account"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white"/>
  <img alt="platform" src="https://img.shields.io/badge/Platform-Bonk%20Vault%20Miniapp-111111"/>
  <img alt="multi-account" src="https://img.shields.io/badge/Multi--Account-Supported-111111"/>
  <img alt="proxy" src="https://img.shields.io/badge/Proxy-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>Bonk Vault Bot</b> is a full automation bot for the Bonk Vault Telegram Miniapp.<br/>
  It handles the complete daily cycle: settling every open sponsored task, watching rewarded ads on both available networks until each daily cap is reached, collecting every visit and spin slot, validating ads towards the basic, ultra and supreme miner cards and syncing the passive vault, then playing all six mini games by solving each round from the data the server returns, all running across multiple accounts with proxy support and a live countdown between cycles.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Features](#features)
- [File Structure](#file-structure)
- [Disclaimer](#disclaimer)

---

## Requirements

- Python `3.12+`
- Git

---

## Installation

**Clone the repository:**

```bash
git clone https://github.com/Yuurisan-N1/Bonkvault-Miniapp.git
cd Bonkvault-Miniapp
```

**Install dependencies:**

```bash
pip install aiohttp yuurisan
```

---

## Configuration

### 1. Accounts (data.txt)

Fill `data.txt` with Telegram WebApp `initData` for each account, one per line:

```
user=%7B%22id%22...&hash=abc123
user=%7B%22id%22...&hash=def456
```

> `initData` can be obtained from the browser DevTools when opening Bonk Vault on Telegram Web.

### 2. Proxy (proxy.txt)

Fill `proxy.txt` with proxies, one per line (optional, leave empty to run without proxy):

```
host:port
host:port:user:pass
http://user:pass@host:port
```

Proxies are assigned to accounts by index in round-robin order.

### 3. Bot Settings (config.json)

`sleep_seconds` controls how many seconds the bot waits between cycles. If `config.json` is missing, it is created automatically with a default of `3600` seconds.

```json
{
  "settings": {
    "sleep_seconds": 3600
  }
}
```

---

## Running the Bot

```bash
python bot.py
```

Press `Ctrl+C` at any time to stop the bot cleanly.

---

## Features

### Auto Sponsored Tasks
The bot reads the sponsored task board the server publishes and keeps every entry that is still marked active. Tasks are ordered by the reward the server reports, and each one the account has not collected yet is settled in turn. After every settlement the bot re-reads the vault and prints the reward and the new confirmed balance, so a task line only appears once the server has actually moved the balance. Tasks already collected by the account are skipped without a request.

### Auto Watch and Earn
The bot reads the daily watch allowance from the server settings and the current watch counter from the vault. While slots remain it alternates between the two rewarded-ad networks the miniapp offers, **Monetag** and **Adsgram**, crediting one ad view per slot. Each ad view updates the vault balance, the ad bonus balance, the lifetime total and the daily activity counter. A shared cooldown is respected between ad views so the cadence matches the miniapp, and the watch counter resets when the previous watch is more than a day old.

### Auto Visit and Earn
The visit and earn phase claims every remaining daily visit slot. Each visit credits the vault balance, the lifetime total and the daily visit counter, and is followed by a fresh vault read so the printed reward is the balance movement the server stored. The phase stops as soon as the daily visit allowance reported by the server is reached and reports how many slots were already used.

### Auto Spin and Earn
The spin and earn phase claims every remaining daily spin slot. Each spin credits the vault balance, the lifetime total and the daily spin counter, respects the same cooldown as the rewarded ads, and is verified with a fresh vault read before it is printed.

### Auto Miner Cards
Three miner cards are supported: **Basic**, **Ultra** and **Supreme**. For each card the bot records the number of validated ad views the card requires, then activates the card once its requirement is met. The Basic card opens the passive vault, the Ultra card needs its own validated ads, and the Supreme card is only activated while both the Basic and the Ultra card are still running, matching the card rules the miniapp enforces. Card activations and ad counts are stored on the account so progress continues across cycles.

### Auto Passive Vault Sync
Once any miner card is running, the bot accumulates the passive mining rate of every card that is still within its lifetime window, collects the accumulated vault, and prints the credited amount together with the confirmed balance. Cards whose lifetime window has expired stop contributing until they are activated again.

### Auto Mini Games
Six mini games are played in order: **2048 Mini**, **Candy Match**, **Coin Catcher**, **Fruit Ninja**, **Quick Quiz** and **Word Scramble**. For each game the bot mints a play chance, opens a round, then settles it using the round data the server returns — the word scramble is solved from the target words handed out with the round, the quick quiz is answered from the question set the round exposes together with an arithmetic solver, and the score based games submit a valid play profile. The points awarded for each round are read from the server response and logged per game.

### Proxy Support
Proxies are loaded from `proxy.txt` and assigned to accounts by position in round-robin order. Proxy credentials are masked in log output. Running without proxies is fully supported.

### Multi Account
All accounts in `data.txt` are processed sequentially within every cycle. The Telegram name is parsed directly from the `initData` string, and the vault balance is printed for every account before the phases start. A blank line separates each account's output. The cycle number is tracked and logged at the start of each round.

### Auto Countdown
After all accounts complete a cycle, the bot displays a live `HH:MM:SS` countdown in the terminal until the next cycle starts, then re-shows the banner before beginning again.

---

## File Structure

```text
BonkVault-Miniapp/
├── bot.py          # Main bot, full daily cycle automation
├── config.json     # Sleep duration between cycles
├── data.txt        # Account initData, one per line
├── proxy.txt       # Proxy list, one per line (optional)
├── LICENSE         # License file
└── utils/
    └── banner.py   # Banner using yuurisan module
```

---

## Disclaimer

This tool is built for educational and technical exploration purposes. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>
