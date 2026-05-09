# MarketMind

**Multi-Agent Financial Analysis Platform**

MarketMind is a full-stack AI-powered stock analysis system built with CrewAI. It uses multiple specialized AI agents to fetch live financial metrics, scrape sentiment data from the web, and generate structured BUY / SELL / HOLD investment recommendations with detailed reasoning.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend Tabs](#frontend-tabs)
- [Deploying to AWS EC2](#deploying-to-aws-ec2)
- [Azure Resources](#azure-resources)
- [Known Issues](#known-issues)

---

## Overview

MarketMind orchestrates two CrewAI agents that work sequentially to analyze any publicly traded stock:

1. **Senior Quantitative Analyst** — fetches fundamental financial data (P/E ratio, EPS, Beta, 52-week range, market cap) and compares 1-year performance against the S&P 500.
2. **Chief Investment Strategist** — reads the quant analysis, scrapes recent news and sentiment from the web using Firecrawl, and produces a final investment recommendation with justification.

Results are saved to Azure Blob Storage as Markdown reports and logged to Azure PostgreSQL for historical tracking.

---

## Architecture

```
Browser (index.html)
        |
        | HTTP + Server-Sent Events (SSE)
        v
FastAPI (main.py) — port 8000
        |
        |-- CrewAI Crew
        |       |-- Senior Quantitative Analyst
        |       |       |-- FundamentalAnalysisTool  (yfinance)
        |       |       |-- CompareStocksTool         (yfinance)
        |       |       |-- SearchMemory / SaveMemory
        |       |
        |       |-- Chief Investment Strategist
        |               |-- SentimentSearchTool       (Firecrawl)
        |               |-- SearchMemory / SaveMemory
        |
        |-- Azure Blob Storage  (saves .md report)
        |-- Azure PostgreSQL    (saves analysis rows)
```

The backend streams real-time events to the frontend via SSE. Every tool call, agent thought, and final answer is streamed line-by-line so you can watch the analysis happen live in the Raw Terminal tab.

---

## Features

- Live streaming of CrewAI agent output via Server-Sent Events
- Raw Terminal tab with color-coded agent, tool, and output lines
- Dashboard tab with metric cards, charts, and the full final verdict
- Agent Pipeline tab showing each task, tool call, arguments, and output
- Full Markdown report with download and copy buttons
- History tab showing all past analyses from PostgreSQL
- Dark and light mode toggle
- Azure Blob Storage integration for report persistence
- Azure PostgreSQL integration for analysis history

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, uvicorn |
| AI Agents | CrewAI, OpenAI GPT-4o-mini, Groq (fallback) |
| Web Scraping | Firecrawl |
| Financial Data | yfinance |
| Database | Azure PostgreSQL (psycopg2, SQLAlchemy) |
| File Storage | Azure Blob Storage |
| Frontend | Vanilla HTML, CSS, JavaScript, Chart.js |
| Package Manager | uv |

---

## Project Structure

```
crewai-agent-azure/
  main.py               — FastAPI app, SSE streaming, QueueWriter parser
  database.py           — PostgreSQL save and fetch functions
  tools/
    fundamental.py      — FundamentalAnalysisTool (yfinance)
    compare.py          — CompareStocksTool (yfinance)
    sentiment.py        — SentimentSearchTool (Firecrawl)
    memory.py           — SearchMemory, SaveMemory
  agents/
    quant.py            — Senior Quantitative Analyst agent definition
    strategist.py       — Chief Investment Strategist agent definition
  tasks/
    analysis.py         — Task definitions for both agents
  frontend/
    index.html          — Complete single-file frontend
  Dockerfile
  pyproject.toml
  .env                  — Not committed, contains secrets
  .gitignore
  README.md
```

---

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for deployment)
- An OpenAI API key
- A Firecrawl API key
- An Azure account with a PostgreSQL instance and Blob Storage container

---

## Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/marketmind.git
cd marketmind
```

**2. Install dependencies using uv**

```bash
uv sync
```

**3. Create your `.env` file**

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your real values. See [Environment Variables](#environment-variables).

---

## Environment Variables

Create a `.env` file in the project root. Never commit this file.

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o-mini

GROQ_API_KEY=gsk_...
GROQ_MODEL_NAME=llama-3.3-70b-versatile

FIRECRAWL_API_KEY=fc-...

AZURE_POSTGRES_CONNECTION_STRING=postgresql://user:password@host:5432/postgres?sslmode=require
AZURE_BLOB_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...

CREWAI_STORAGE_DIR=C:/Users/YourName/crewai_storage
```

| Variable | Description |
|---|---|
| OPENAI_API_KEY | Primary LLM for agent reasoning |
| OPENAI_MODEL_NAME | Model name, default gpt-4o-mini |
| GROQ_API_KEY | Fallback LLM (faster, free tier available) |
| FIRECRAWL_API_KEY | Web scraping for sentiment search |
| AZURE_POSTGRES_CONNECTION_STRING | Full PostgreSQL connection string |
| AZURE_BLOB_STORAGE_CONNECTION_STRING | Azure Blob Storage connection string |
| CREWAI_STORAGE_DIR | Local path for CrewAI memory storage |

---

## Running the Application

**Start the backend**

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

**Open the frontend**

Open `frontend/index.html` in your browser, or navigate to:

```
http://127.0.0.1:8000
```

**Run an analysis**

1. Type a ticker symbol (e.g. `AAPL`) in the sidebar
2. Click **Run Analysis**
3. Watch the live output in the **Raw Terminal** tab
4. Switch to **Dashboard** when complete to see charts and metrics
5. View the full report in the **Report** tab

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| POST | `/api/v1/analyze_stock` | Run analysis (blocking) |
| GET | `/api/v1/analyze_stock/stream/{ticker}` | Run analysis with SSE streaming |
| GET | `/api/v1/reports` | List all saved reports |
| GET | `/api/v1/reports/{ticker}` | Get latest report for a ticker |

**SSE Event Types** streamed to the frontend:

| Event Type | Description |
|---|---|
| crew_start | Crew execution has begun |
| task_start | A new task has started |
| agent_name | The agent handling the current task |
| tool_start | A tool call has been initiated |
| tool_name | Name of the tool being called |
| tool_args | Arguments passed to the tool |
| tool_output | Output returned from the tool |
| tool_done | Tool call completed |
| final_answer | Agent final answer for the task |
| task_done | Task completed |
| complete | Full analysis complete, includes result and blob URL |
| error | An error occurred |

---

## Frontend Tabs

**Raw Terminal**

Displays all CrewAI output in a VS Code-style dark terminal. Lines are color-coded by type: agent names in purple, tool calls in orange, tool outputs in green, final answers in yellow. Duplicate lines are filtered automatically.

**Dashboard**

Shows the verdict card (BUY / SELL / HOLD) with current price, eight metric cards (Price, Market Cap, P/E Ratio, EPS, Beta, 1Y Performance, Forward P/E, Analyst Rating), and four charts:

- Price vs S&P 500 (1 year line chart)
- Valuation metrics bar chart
- 52-Week price range
- Analyst consensus doughnut chart
- 12-Month indexed performance

Below the charts, the full Chief Investment Strategist verdict is displayed with all reasoning.

**Agent Pipeline**

Shows each meaningful task as a card with the agent name chip, tool executions with arguments and outputs, and the final answer. Internal CrewAI setup tasks are hidden automatically.

**Report**

Renders the full Markdown report with syntax formatting. Includes a download button to save as `.md` and a copy button.

**History**

Lists all past analyses from PostgreSQL with ticker, verdict, and IST timestamp. Clicking a row loads the full dashboard and report for that analysis. Requires the EC2 public IP to be whitelisted in the Azure PostgreSQL firewall.

---

## Deploying to AWS EC2

This is the recommended free deployment method. AWS EC2 t2.micro is free for 12 months.

**Step 1 — Create an EC2 instance**

- Go to the AWS Console and navigate to EC2
- Click Launch Instance
- Choose Ubuntu 24.04 LTS as the operating system
- Select t2.micro as the instance type (free tier eligible)
- Create a new key pair and download the `.pem` file
- Under Network Settings, add inbound rules for port 80 (HTTP) and port 22 (SSH)
- Launch the instance and note the public IPv4 address

**Step 2 — Connect to the instance**

```bash
chmod 400 marketmind-key.pem
ssh -i marketmind-key.pem ubuntu@YOUR_EC2_IP
```

**Step 3 — Install Docker on EC2**

```bash
sudo apt-get update -y
sudo apt-get install -y docker.io git curl
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker
```

**Step 4 — Clone your repository**

```bash
git clone https://github.com/YOUR_USERNAME/marketmind.git
cd marketmind
```

**Step 5 — Create the `.env` file on EC2**

```bash
nano .env
```

Paste in all your environment variables and save with Ctrl+X.

**Step 6 — Build and run**

```bash
docker build -t marketmind .
docker run -d \
  --name marketmind \
  --env-file .env \
  -p 80:8000 \
  --restart unless-stopped \
  marketmind
```

**Step 7 — Add EC2 IP to Azure PostgreSQL firewall**

Go to portal.azure.com, navigate to your PostgreSQL instance, open Networking, and add your EC2 public IP address as a firewall rule.

**Access the app**

```
http://YOUR_EC2_PUBLIC_IP
```

**Useful commands after deployment**

```bash
# View live logs
docker logs -f marketmind

# Restart after a code update
git pull
docker build -t marketmind .
docker stop marketmind && docker rm marketmind
docker run -d --name marketmind --env-file .env -p 80:8000 --restart unless-stopped marketmind

# Check container status
docker ps
```

---

## Azure Resources

| Resource | Purpose |
|---|---|
| PostgreSQL (crewaiagent0001.postgres.database.azure.com) | Stores analysis history rows |
| Blob Storage (crewquantagentai.blob.core.windows.net) | Stores analysis reports as .md files |

Both resources are on Azure and are accessed from wherever the backend runs (local machine or EC2). The PostgreSQL firewall must be updated whenever the backend's public IP changes.

---

## Known Issues

| Issue | Workaround |
|---|---|
| History tab shows blank | Add the current public IP to Azure PostgreSQL firewall |
| CrewAI storage error on exFAT drive | Set CREWAI_STORAGE_DIR to a path on an NTFS drive (C: drive) |
| `.venv` cannot be created on E: drive | Run `uv run` only from the C: drive copy of the project |
| EC2 IP changes on restart | Re-add the new IP to Azure PostgreSQL firewall after each restart |

---

## License

This project was built for academic purposes as part of the MSc Data Science and AI programme at Ramakrishna Mission Residential College (Autonomous), Narendrapur.