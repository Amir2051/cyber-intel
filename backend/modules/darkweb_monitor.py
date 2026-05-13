"""
Dark Web Monitor Module
Monitors paste sites and indexed dark web sources for keyword appearances.
Sends alerts when targets are found.
"""

import os
import httpx
import asyncio
import json
from datetime import datetime
from pathlib import Path

MONITOR_DB = Path(os.getenv("MONITOR_DB", "/tmp/cyberintel_monitors.json"))
ALERTS_DB = Path(os.getenv("ALERTS_DB", "/tmp/cyberintel_alerts.json"))
DEHASHED_API_KEY = os.getenv("DEHASHED_API_KEY")
DEHASHED_EMAIL = os.getenv("DEHASHED_EMAIL")

# Paste sites to monitor (public/indexed)
PASTE_SOURCES = [
    "https://psbdmp.ws/api/search/{keyword}",  # Pastebin dump search
]


def _load_db(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_db(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


async def add_monitor_target(keyword: str, keyword_type: str, client_id: str) -> dict:
    """Register a new monitoring target for a client."""
    db = _load_db(MONITOR_DB)
    
    if client_id not in db:
        db[client_id] = []
    
    # Check for duplicates
    existing = [t for t in db[client_id] if t["keyword"] == keyword]
    if existing:
        return {"status": "already_monitoring", "keyword": keyword, "client_id": client_id}
    
    target = {
        "id": f"MON-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "keyword": keyword,
        "keyword_type": keyword_type,
        "client_id": client_id,
        "added": datetime.utcnow().isoformat(),
        "last_checked": None,
        "alert_count": 0,
        "active": True
    }
    
    db[client_id].append(target)
    _save_db(MONITOR_DB, db)
    
    # Run initial scan
    initial_results = await _scan_keyword(keyword, keyword_type)
    
    if initial_results:
        await _store_alerts(client_id, keyword, initial_results)
    
    return {
        "status": "monitoring_started",
        "target": target,
        "initial_scan": {
            "hits": len(initial_results),
            "results": initial_results[:3]  # Return first 3
        }
    }


async def get_alerts(client_id: str) -> dict:
    """Retrieve all alerts for a client."""
    alerts_db = _load_db(ALERTS_DB)
    monitor_db = _load_db(MONITOR_DB)
    
    client_alerts = alerts_db.get(client_id, [])
    client_monitors = monitor_db.get(client_id, [])
    
    return {
        "client_id": client_id,
        "monitors": client_monitors,
        "alerts": client_alerts,
        "unread_count": len([a for a in client_alerts if not a.get("read")]),
        "total_alerts": len(client_alerts)
    }


async def _scan_keyword(keyword: str, keyword_type: str) -> list:
    """
    Scan multiple sources for keyword appearances.
    Returns list of hits with source, context, and timestamp.
    """
    results = []
    tasks = [
        _scan_dehashed(keyword, keyword_type),
        _scan_paste_sites(keyword),
    ]
    
    scan_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for r in scan_results:
        if isinstance(r, list):
            results.extend(r)
    
    return results


async def _scan_dehashed(keyword: str, keyword_type: str) -> list:
    """Search DeHashed breach database."""
    if not DEHASHED_API_KEY or not DEHASHED_EMAIL:
        return []
    
    field_map = {
        "email": "email",
        "phone": "phone",
        "name": "name",
        "domain": "domain",
        "ssn_prefix": "social"
    }
    
    field = field_map.get(keyword_type, "email")
    url = f"https://api.dehashed.com/search?query={field}:{keyword}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                url,
                auth=(DEHASHED_EMAIL, DEHASHED_API_KEY),
                headers={"Accept": "application/json"},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", []) or []
                return [
                    {
                        "source": "DeHashed",
                        "type": "breach",
                        "keyword": keyword,
                        "database_name": e.get("database_name", "Unknown"),
                        "email": e.get("email"),
                        "username": e.get("username"),
                        "found_at": datetime.utcnow().isoformat(),
                        "severity": "HIGH"
                    }
                    for e in entries[:10]
                ]
        except Exception:
            pass
    
    return []


async def _scan_paste_sites(keyword: str) -> list:
    """Search indexed paste sites for keyword."""
    results = []
    
    # Ahmia paste search (public)
    url = f"https://ahmia.fi/search/?q={keyword}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10, follow_redirects=True)
            if resp.status_code == 200 and keyword.lower() in resp.text.lower():
                results.append({
                    "source": "Ahmia",
                    "type": "indexed_reference",
                    "keyword": keyword,
                    "url": url,
                    "found_at": datetime.utcnow().isoformat(),
                    "severity": "MEDIUM"
                })
        except Exception:
            pass
    
    return results


async def _store_alerts(client_id: str, keyword: str, findings: list):
    """Persist alert findings to the alerts database."""
    db = _load_db(ALERTS_DB)
    
    if client_id not in db:
        db[client_id] = []
    
    for finding in findings:
        alert = {
            "alert_id": f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "client_id": client_id,
            "keyword": keyword,
            "finding": finding,
            "created_at": datetime.utcnow().isoformat(),
            "read": False,
            "severity": finding.get("severity", "MEDIUM")
        }
        db[client_id].append(alert)
    
    _save_db(ALERTS_DB, db)


async def run_scheduled_scan():
    """
    Run scans for all active monitors.
    Call this from a scheduler (cron / APScheduler).
    """
    monitor_db = _load_db(MONITOR_DB)
    
    for client_id, targets in monitor_db.items():
        for target in targets:
            if not target.get("active"):
                continue
            
            findings = await _scan_keyword(target["keyword"], target["keyword_type"])
            
            if findings:
                await _store_alerts(client_id, target["keyword"], findings)
                target["alert_count"] += len(findings)
            
            target["last_checked"] = datetime.utcnow().isoformat()
    
    _save_db(MONITOR_DB, monitor_db)
