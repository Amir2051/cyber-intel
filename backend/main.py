import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from modules.osint_profiler import run_osint_profile
from modules.crypto_tracer import trace_wallet
from modules.fraud_packager import package_fraud_case
from modules.darkweb_monitor import add_monitor_target, get_alerts
from modules.deed_fraud_scanner import scan_deed_fraud
from modules.reputation_scorer import score_reputation

app = FastAPI(
    title="CyberIntel Platform API",
    description="Cyber Threat Intelligence & Victim Advocacy Platform",
    version="1.0.0",
)

# CORS: comma-separated origins via env, defaults to local Vite dev server.
# "*" + allow_credentials=True is rejected by browsers per the CORS spec, so
# we drop credentials when the wildcard is in use.
_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── OSINT Profiler ──────────────────────────────────────────────
class OSINTRequest(BaseModel):
    query: str
    query_type: str  # email | username | phone | domain | ip


@app.post("/api/osint/profile")
async def osint_profile(req: OSINTRequest):
    try:
        result = await run_osint_profile(req.query, req.query_type)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Crypto Tracer ───────────────────────────────────────────────
class WalletRequest(BaseModel):
    address: str
    chain: str = "eth"  # eth | btc | bnb | tron


@app.post("/api/crypto/trace")
async def crypto_trace(req: WalletRequest):
    try:
        result = await trace_wallet(req.address, req.chain)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Fraud Case Packager ─────────────────────────────────────────
class FraudCaseRequest(BaseModel):
    case_id: str
    victim_name: str
    victim_email: str
    incident_type: str
    incident_date: str
    description: str
    evidence: list = []
    suspect_info: dict = {}
    financial_loss: float = 0.0
    target_agencies: list = ["IC3", "FBI"]


@app.post("/api/fraud/package")
async def fraud_package(req: FraudCaseRequest):
    try:
        result = await package_fraud_case(req.model_dump())
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Dark Web Monitor ────────────────────────────────────────────
class MonitorRequest(BaseModel):
    keyword: str
    keyword_type: str  # name | email | domain | ssn_prefix | phone
    client_id: str


@app.post("/api/darkweb/monitor")
async def darkweb_monitor(req: MonitorRequest):
    try:
        result = await add_monitor_target(req.keyword, req.keyword_type, req.client_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/darkweb/alerts/{client_id}")
async def darkweb_alerts(client_id: str):
    try:
        result = await get_alerts(client_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Deed Fraud Scanner ──────────────────────────────────────────
class DeedRequest(BaseModel):
    property_address: str
    owner_name: str
    county: str
    state: str


@app.post("/api/deed/scan")
async def deed_scan(req: DeedRequest):
    try:
        result = await scan_deed_fraud(
            req.property_address, req.owner_name, req.county, req.state
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reputation Scorer ───────────────────────────────────────────
class ReputationRequest(BaseModel):
    value: str
    value_type: str  # email | phone


@app.post("/api/reputation/score")
async def reputation_score(req: ReputationRequest):
    try:
        result = await score_reputation(req.value, req.value_type)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health Check ────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "operational",
        "platform": "CyberIntel v1.0",
        "keys_configured": {
            "hunter": bool(os.getenv("HUNTER_API_KEY")),
            "shodan": bool(os.getenv("SHODAN_API_KEY")),
            "numverify": bool(os.getenv("NUMVERIFY_API_KEY")),
            "whoisxml": bool(os.getenv("WHOISXML_API_KEY")),
            "etherscan": bool(os.getenv("ETHERSCAN_API_KEY")),
            "bscscan": bool(os.getenv("BSCSCAN_API_KEY")),
            "tronscan": bool(os.getenv("TRONSCAN_API_KEY")),
            "dehashed": bool(os.getenv("DEHASHED_API_KEY")),
            "attom": bool(os.getenv("ATTOM_API_KEY")),
            "abstract": bool(os.getenv("ABSTRACT_API_KEY")),
        },
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
