"""
Phone / Email Reputation Scorer
Aggregates risk signals from multiple APIs into a unified 0-100 risk score.
"""

import os
import re
import asyncio
from datetime import datetime

import httpx

NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
ABSTRACT_API_KEY = os.getenv("ABSTRACT_API_KEY")

DEFAULT_TIMEOUT = 12.0


async def score_reputation(value: str, value_type: str) -> dict:
    """Main entry. Returns unified risk score and signal breakdown."""
    result = {
        "value": value,
        "type": value_type,
        "timestamp": datetime.utcnow().isoformat(),
        "risk_score": 0,
        "risk_level": "UNKNOWN",
        "signals": [],
        "summary": {},
    }

    if value_type == "email":
        await _score_email(value, result)
    elif value_type == "phone":
        await _score_phone(value, result)
    else:
        raise ValueError(f"Unsupported value_type: {value_type}")

    result["risk_level"] = _classify_risk(result["risk_score"])
    return result


async def _score_email(email: str, result: dict):
    domain = email.split("@", 1)[-1].lower() if "@" in email else ""
    tasks = [
        _check_email_hunter(email),
        _check_email_abstract(email),
        _check_email_patterns(email),
        _check_email_domain_shodan(domain),
    ]
    signals = await asyncio.gather(*tasks, return_exceptions=True)

    score = 0
    for s in signals:
        if isinstance(s, dict):
            result["signals"].append(s)
            score += s.get("score_contribution", 0) or 0

    result["risk_score"] = min(score, 100)
    result["summary"] = {
        "domain": domain,
        "disposable": any(s.get("disposable") for s in result["signals"] if isinstance(s, dict)),
        "deliverable": next(
            (s.get("deliverable") for s in result["signals"]
             if isinstance(s, dict) and "deliverable" in s),
            None,
        ),
        "exposed_infra": next(
            (s.get("exposed_infra") for s in result["signals"]
             if isinstance(s, dict) and "exposed_infra" in s),
            None,
        ),
    }


async def _score_phone(phone: str, result: dict):
    tasks = [
        _check_phone_numverify(phone),
        _check_phone_abstract(phone),
    ]
    signals = await asyncio.gather(*tasks, return_exceptions=True)

    score = 0
    for s in signals:
        if isinstance(s, dict):
            result["signals"].append(s)
            score += s.get("score_contribution", 0) or 0

    result["risk_score"] = min(score, 100)
    result["summary"] = {
        "valid": next((s.get("valid") for s in result["signals"]
                       if isinstance(s, dict) and "valid" in s), None),
        "line_type": next((s.get("line_type") for s in result["signals"]
                           if isinstance(s, dict) and "line_type" in s), None),
        "carrier": next((s.get("carrier") for s in result["signals"]
                         if isinstance(s, dict) and "carrier" in s), None),
    }


async def _check_email_hunter(email: str) -> dict:
    if not HUNTER_API_KEY:
        return {"source": "Hunter.io", "status": "no_key", "score_contribution": 0}

    url = "https://api.hunter.io/v2/email-verifier"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"email": email, "api_key": HUNTER_API_KEY})
            if resp.status_code != 200:
                return {"source": "Hunter.io", "status": f"http_{resp.status_code}", "score_contribution": 0}
            d = resp.json().get("data", {}) or {}
            disposable = d.get("disposable", False)
            deliverable = d.get("result")

            contribution = 0
            if disposable:
                contribution += 35
            if deliverable == "undeliverable":
                contribution += 20
            if not d.get("mx_records"):
                contribution += 10

            return {
                "source": "Hunter.io",
                "deliverable": deliverable,
                "disposable": disposable,
                "score": d.get("score"),
                "mx_records": d.get("mx_records"),
                "score_contribution": contribution,
            }
        except Exception as e:
            return {"source": "Hunter.io", "error": str(e), "score_contribution": 0}


async def _check_email_abstract(email: str) -> dict:
    if not ABSTRACT_API_KEY:
        return {"source": "AbstractAPI", "status": "no_key", "score_contribution": 0}

    url = "https://emailvalidation.abstractapi.com/v1/"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"api_key": ABSTRACT_API_KEY, "email": email})
            if resp.status_code != 200:
                return {"source": "AbstractAPI", "status": f"http_{resp.status_code}", "score_contribution": 0}
            d = resp.json() or {}
            is_free = (d.get("is_free_email") or {}).get("value", False)
            is_disposable = (d.get("is_disposable_email") or {}).get("value", False)
            is_valid = (d.get("is_valid_format") or {}).get("value", True)

            contribution = 0
            if is_disposable:
                contribution += 35
            if not is_valid:
                contribution += 20

            return {
                "source": "AbstractAPI",
                "is_free_email": is_free,
                "is_disposable": is_disposable,
                "is_valid_format": is_valid,
                "deliverability": d.get("deliverability"),
                "score_contribution": contribution,
            }
        except Exception as e:
            return {"source": "AbstractAPI", "error": str(e), "score_contribution": 0}


async def _check_email_patterns(email: str) -> dict:
    """Rule-based checks requiring no API."""
    contribution = 0
    flags = []

    disposable_domains = {
        "mailinator.com", "guerrillamail.com", "tempmail.com",
        "throwaway.email", "yopmail.com", "sharklasers.com",
        "10minutemail.com", "trashmail.com", "maildrop.cc",
        "fakeinbox.com", "spamgourmet.com", "tempr.email",
    }

    local = email.split("@", 1)[0] if "@" in email else email
    domain = email.split("@", 1)[-1].lower() if "@" in email else ""

    if domain in disposable_domains:
        contribution += 35
        flags.append("KNOWN_DISPOSABLE_DOMAIN")

    if re.search(r"\d{4,}", local):
        contribution += 10
        flags.append("EXCESSIVE_NUMBERS_IN_LOCAL_PART")

    if len(local) > 30:
        contribution += 5
        flags.append("UNUSUALLY_LONG_LOCAL_PART")

    return {
        "source": "Pattern Analysis",
        "flags": flags,
        "domain": domain,
        "disposable": domain in disposable_domains,
        "score_contribution": contribution,
    }


async def _check_email_domain_shodan(domain: str) -> dict:
    """Check the email's domain on Shodan — exposed hosts / known CVEs are a signal."""
    if not SHODAN_API_KEY:
        return {"source": "Shodan Domain", "status": "no_key", "score_contribution": 0}
    if not domain:
        return {"source": "Shodan Domain", "status": "no_domain", "score_contribution": 0}

    url = f"https://api.shodan.io/dns/domain/{domain}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"key": SHODAN_API_KEY})
            if resp.status_code != 200:
                return {
                    "source": "Shodan Domain",
                    "status": f"http_{resp.status_code}",
                    "score_contribution": 0,
                }
            d = resp.json() or {}
            records = d.get("data", []) or []
            ips = {r.get("value") for r in records if r.get("type") == "A" and r.get("value")}
            subdomains = d.get("subdomains", []) or []
            exposed = bool(ips)
            # Heuristic only: a large attack surface on the sender's domain is a mild signal,
            # not proof of malice. Capped low to avoid false positives on big providers.
            contribution = 5 if len(subdomains) > 50 else 0
            return {
                "source": "Shodan Domain",
                "domain": d.get("domain"),
                "subdomain_count": len(subdomains),
                "ip_count": len(ips),
                "exposed_infra": exposed,
                "score_contribution": contribution,
            }
        except Exception as e:
            return {"source": "Shodan Domain", "error": str(e), "score_contribution": 0}


async def _check_phone_numverify(phone: str) -> dict:
    if not NUMVERIFY_API_KEY:
        return {"source": "NumVerify", "status": "no_key", "score_contribution": 0}

    url = "http://apilayer.net/api/validate"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(
                url,
                params={"access_key": NUMVERIFY_API_KEY, "number": phone, "format": 1},
            )
            if resp.status_code != 200:
                return {"source": "NumVerify", "status": f"http_{resp.status_code}", "score_contribution": 0}
            d = resp.json() or {}
            contribution = 0
            line_type = d.get("line_type", "") or ""

            if not d.get("valid"):
                contribution += 40
            if line_type == "voip":
                contribution += 30
            if line_type == "prepaid":
                contribution += 15

            return {
                "source": "NumVerify",
                "valid": d.get("valid"),
                "line_type": line_type,
                "carrier": d.get("carrier"),
                "country": d.get("country_name"),
                "location": d.get("location"),
                "score_contribution": contribution,
            }
        except Exception as e:
            return {"source": "NumVerify", "error": str(e), "score_contribution": 0}


async def _check_phone_abstract(phone: str) -> dict:
    if not ABSTRACT_API_KEY:
        return {"source": "AbstractAPI Phone", "status": "no_key", "score_contribution": 0}

    url = "https://phonevalidation.abstractapi.com/v1/"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"api_key": ABSTRACT_API_KEY, "phone": phone})
            if resp.status_code != 200:
                return {"source": "AbstractAPI Phone", "status": f"http_{resp.status_code}", "score_contribution": 0}
            d = resp.json() or {}
            contribution = 0
            if not d.get("valid"):
                contribution += 40
            if d.get("type") == "voip":
                contribution += 30

            return {
                "source": "AbstractAPI Phone",
                "valid": d.get("valid"),
                "type": d.get("type"),
                "carrier": (d.get("carrier") or {}).get("name") if isinstance(d.get("carrier"), dict) else d.get("carrier"),
                "country": (d.get("country") or {}).get("name") if isinstance(d.get("country"), dict) else d.get("country"),
                "score_contribution": contribution,
            }
        except Exception as e:
            return {"source": "AbstractAPI Phone", "error": str(e), "score_contribution": 0}


def _classify_risk(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 15:
        return "LOW"
    return "CLEAN"
