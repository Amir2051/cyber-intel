# CyberIntel Platform

**Private Cyber Threat Intelligence & Victim Advocacy Platform**

Full-stack platform combining OSINT profiling, crypto tracing, fraud case packaging, dark web monitoring, deed fraud detection, and reputation scoring — built for investigators, victim advocates, and law firms.

---

## Platform Modules

| Module | Description | APIs Required |
|---|---|---|
| **OSINT Profiler** | Actor dossier from email/username/phone/domain/IP | Hunter.io, Shodan, NumVerify, WhoisXML |
| **Crypto Tracer** | Wallet graph + risk flagging (ETH/BTC/BNB/TRON) | Etherscan, BscScan, TronScan |
| **Case Packager** | IC3 / FBI / Secret Service report bundles | None |
| **Dark Web Monitor** | Keyword alerts across breach + paste sites | DeHashed |
| **Deed Fraud Scanner** | Property transfer anomaly detection | ATTOM Data |
| **Reputation Scorer** | Phone & email risk scoring (0–100) | Hunter.io, Shodan, NumVerify, AbstractAPI |
| **Case Manager** | Case tracking dashboard | None |

---

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Fill in your API keys in .env

pip install -r requirements.txt
python main.py
# API running at http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# UI running at http://localhost:5173
```

---

## API Keys to Acquire

| Key | Service | Get It |
|---|---|---|
| `HUNTER_API_KEY` | Email intelligence | https://hunter.io |
| `SHODAN_API_KEY` | Host / domain infra intel | https://shodan.io |
| `NUMVERIFY_API_KEY` | Phone validation | https://numverify.com |
| `WHOISXML_API_KEY` | WHOIS lookup | https://whoisxmlapi.com |
| `ETHERSCAN_API_KEY` | ETH blockchain | https://etherscan.io/apis |
| `BSCSCAN_API_KEY` | BNB blockchain | https://bscscan.com/apis |
| `TRONSCAN_API_KEY` | TRON blockchain | https://tronscan.org |
| `DEHASHED_API_KEY` | Breach/dark data | https://dehashed.com |
| `DEHASHED_EMAIL` | DeHashed account email | https://dehashed.com |
| `ATTOM_API_KEY` | Property records | https://api.attomdata.com |
| `ABSTRACT_API_KEY` | Phone + email verify | https://www.abstractapi.com |

---

## Tech Stack

- **Backend:** Python + FastAPI + httpx
- **Frontend:** React 18 + Vite + Tailwind CSS
- **Styling:** Space Mono + Inter, dark intelligence aesthetic
- **Reports:** JSON bundles (PDF export via reportlab — extend as needed)

---

## Project Structure

```
cyberintel-platform/
├── backend/
│   ├── main.py                    # FastAPI app + all routes
│   ├── requirements.txt
│   ├── .env.example               # API key template
│   └── modules/
│       ├── osint_profiler.py      # OSINT aggregation
│       ├── crypto_tracer.py       # Blockchain tracing
│       ├── fraud_packager.py      # Agency report generation
│       ├── darkweb_monitor.py     # Keyword monitoring
│       ├── deed_fraud_scanner.py  # Property fraud detection
│       └── reputation_scorer.py  # Risk scoring engine
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── Sidebar.jsx
    │   │   └── UI.jsx             # Shared component library
    │   ├── pages/                 # One page per module
    │   └── services/api.js        # API client
    └── vite.config.js
```

---

## Monetization Tiers (Suggested)

| Tier | Price | Includes |
|---|---|---|
| **Starter** | $49/mo | OSINT + Reputation Scorer, 100 lookups/mo |
| **Investigator** | $149/mo | All tools, 500 lookups/mo, 5 monitors |
| **Firm** | $499/mo | Unlimited, white-label, API access, case manager |
| **Per Report** | $15–25 | One-time fraud case package |

---

## Legal Notice

This platform is designed for **passive intelligence collection, victim advocacy, and lawful investigation**. Active countermeasures (jamming, spoofing, unauthorized access) are outside the scope of this system and may be illegal. Use in compliance with applicable federal and state law.

---

## Deployment

```bash
# Backend (production)
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (production build)
npm run build
# Serve /dist with nginx or Vercel
```
