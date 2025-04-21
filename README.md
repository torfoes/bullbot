# Bullbot

**Bullbot** is an experimental trading‑automation platform written in Django.  It watches Donald Trump’s posts on **Truth Social**, rates each post’s potential to move financial markets with **OpenAI**, identifies a likely‑affected sector, and—when the impact is deemed *large*—simulates an **options trade** (paper‑trading only).  All posts, classifications, and trades are stored in a relational database so you can review and analyse the strategy’s performance over time.

> **Heads‑up**  This is a research prototype.  It does **not** place real trades and is **not** financial advice.  Use at your own risk.

---
## 1. How it Works

```
flowchart TD
    A [Truth Social] -- RSS via Truthbrush --> B[Ingestion]
    B -- raw post --> C[OpenAI NLP]
    C -- impact = Small --> D[Log & ignore]
    C -- impact = Large + sector + sentiment --> E[Trade Decision]
    E -- trade details --> F[Simulator]
    F -- create Trade rows --> G[SQLite]
    D -- Post rows --> G
```

1. **Ingestion** – \`Truthbrush\` logs into Truth Social and pulls new posts from \`@realDonaldTrump\`.
2. **Classification** – OpenAI rates each post as *Large* or *Small* impact.  For *Large*, it also returns the most‑likely sector and whether the effect is *bullish* or *bearish*.
3. **Decision** – If bullish: buy a CALL; if bearish: buy a PUT on a representative ticker/ETF for the detected sector.
4. **Execution** – Trades are **simulated** (paper) and written to the DB.  A future scheduler can close positions & compute P/L.

---
## 2. Project Tree

\```text
bullbot/
├── manage.py               # Django entry‑point
├── .env                    # secrets (never commit)
├── requirements.txt
├── bullbot/                # project settings package
│   ├── settings.py
│   └── ...
└── trading/                # core app
    ├── models.py           # Post & Trade ORM
    ├── injestion.py        # Truth Social + OpenAI helpers
    ├── execution.py        # trade logic + simulator
    ├── management/commands/
    │   ├── run_bot.py              # continuous ingestion and simulation
    │   ├── classify_post.py        # classify single post and suggest trade
    │   ├── list_positions.py       # show open paper-trades
    │   └── close_positions.py      # close positions by profit or Greeks
    └── tests/              # pytest-django tests
\```

---
## 3. QuickStart

```bash
# 1. clone & create virtual environment
python -m venv venv && source venv/bin/activate

# 2. install deps
pip install -r requirements.txt

# 3. create .env (see below)
cp .env.example .env  # or edit manually

# 4. migrate DB
python manage.py migrate

# 5. run bot (Ctrl+C to stop)
python manage.py run_bot

# 6. run tests
pytest
```

---
## 4 Configuration (\`.env\`)

```dotenv
DEBUG=False
SECRET_KEY=replace‑me

TRUTH_USERNAME=your_truth_username
TRUTH_PASSWORD=your_truth_password
OPENAI_API_KEY=sk‑...

BROKER=simulation  # keep simulation – real broker integration TBD
```

*Never commit real secrets to version control.*  Bullbot loads them via **python‑dotenv** in \`settings.py\`.

---
## 5 Key Components

| Module            | Purpose                                                                                      |
|-------------------|----------------------------------------------------------------------------------------------|
| \`trading.models\`  | \`Post\` – every Truth post processed.<br>\`Trade\` – every simulated option order.               |
| \`trading.ingestion.TruthClient\` | Polls Truth Social using Truthbrush; yields new posts.                           |
| \`trading.ingestion.NLPService\`  | Wrapper over OpenAI Chat Completion for impact, sector & sentiment.             |
| \`trading.execution.decide_trade\`| Maps sector × sentiment → ticker, option type, strike, expiry.                  |
| \`trading.execution.Simulator\`   | Creates \`Trade\` rows (paper).  Swap for real broker in future.                  |
| \`run_bot\` mgmt cmd | Infinite loop: ingestion ➜ NLP ➜ decision ➜ execution.                                       |

---
## 6 |Customising Strategy

* **Sector→Ticker map** – edit \`SECTOR_TICKER\` in \`trading/execution.py\`.
* **Prompt tuning** – update prompts in \`NLPService\` to refine what counts as *Large* impact.
* **Real pricing** – replace dummy entry price & strike with live quotes (e.g. \`yfinance\`).
* **Exit rules** – add a scheduled task (Celery Beat) to close positions after N days or at profit target.

---
## 7 |Testing

Bullbot ships with **pytest‑django** tests that stub the OpenAI calls so you can verify logic without hitting the network:

\```bash
pytest
\```

Add more tests in \`trading/tests/\` as you extend the strategy.

---
## 8 Roadmap

## Roadmap

- [x] Live option pricing via yfinance.option_chain (bid/ask) and Greeks calculation.
- [x] Spread-aware simulation: buy at ask, sell at bid with profit targets (close_positions command).
- [x] Scheduled position evaluation & daily P/L summary via management commands.
- [x] Web dashboard to visualise paper-trades at `/positions/`.
- [ ] Broker API integration (Alpaca, Interactive Brokers, TDA) for real order routing.
- [ ] Advanced performance metrics: Sharpe ratio, drawdown, Sortino ratio over time.
- [ ] Support additional influencers and social feeds beyond Truth Social.

---
## 9|License & Disclaimer

Bullbot is released under the MIT License.  **No warranties.**  Paper‑trading only.  Always do your own research before deploying real capital.
