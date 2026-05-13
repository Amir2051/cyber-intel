"""
OSINT Actor Profiling Module
Aggregates intelligence from multiple sources given an email, username,
phone, domain, or IP.
"""

import os
import re
import asyncio
from datetime import datetime

import httpx

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY")
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
WHOISXML_API_KEY = os.getenv("WHOISXML_API_KEY")

USER_AGENT = "CyberIntel-Platform/1.0"
DEFAULT_TIMEOUT = 12.0


async def run_osint_profile(query: str, query_type: str) -> dict:
    """Main entry point. Routes to sub-collectors based on query_type."""
    profile = {
        "query": query,
        "query_type": query_type,
        "timestamp": datetime.utcnow().isoformat(),
        "sources": [],
        "risk_score": 0,
        "findings": {},
    }

    if query_type == "email":
        tasks = [
            _check_hunter_email(query),
            _check_email_format(query),
            _check_shodan_domain(query.split("@", 1)[-1]) if "@" in query else _noop(),
        ]
    elif query_type == "username":
        tasks = [_check_username_social(query)]
    elif query_type == "phone":
        tasks = [_check_numverify(query)]
    elif query_type == "domain":
        tasks = [
            _check_whois(query),
            _check_hunter_domain(query),
            _check_shodan_domain(query),
        ]
    elif query_type == "ip":
        tasks = [_check_shodan_host(query)]
    else:
        raise ValueError(f"Unsupported query_type: {query_type}")

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            profile["sources"].append({"source": "internal", "status": "error", "data": {"error": str(r)}})
        elif r:
            profile["sources"].append(r)
            data = r.get("data") if isinstance(r, dict) else None
            if isinstance(data, dict):
                profile["findings"].update(data)

    profile["risk_score"] = _calculate_risk_score(profile["findings"])
    return profile


async def _noop() -> dict:
    return {"source": "skipped", "status": "n/a", "data": {}}


async def _check_hunter_email(email: str) -> dict:
    """Verify email deliverability via Hunter.io."""
    if not HUNTER_API_KEY:
        return {"source": "Hunter.io", "status": "no_api_key", "data": {}}

    url = "https://api.hunter.io/v2/email-verifier"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"email": email, "api_key": HUNTER_API_KEY})
            if resp.status_code != 200:
                return {"source": "Hunter.io", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json().get("data", {}) or {}
            return {
                "source": "Hunter.io",
                "status": "success",
                "data": {
                    "deliverable": d.get("result"),
                    "score": d.get("score"),
                    "disposable": d.get("disposable"),
                    "webmail": d.get("webmail"),
                    "mx_records": d.get("mx_records"),
                },
            }
        except Exception as e:
            return {"source": "Hunter.io", "status": "error", "data": {"error": str(e)}}


async def _check_hunter_domain(domain: str) -> dict:
    """Get domain intelligence via Hunter.io."""
    if not HUNTER_API_KEY:
        return {"source": "Hunter.io Domain", "status": "no_api_key", "data": {}}

    url = "https://api.hunter.io/v2/domain-search"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"domain": domain, "api_key": HUNTER_API_KEY})
            if resp.status_code != 200:
                return {"source": "Hunter.io Domain", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json().get("data", {}) or {}
            return {
                "source": "Hunter.io Domain",
                "status": "success",
                "data": {
                    "organization": d.get("organization"),
                    "country": d.get("country"),
                    "email_count": len(d.get("emails", []) or []),
                    "pattern": d.get("pattern"),
                },
            }
        except Exception as e:
            return {"source": "Hunter.io Domain", "status": "error", "data": {"error": str(e)}}


async def _check_whois(domain: str) -> dict:
    """WHOIS lookup via WhoisXML API."""
    if not WHOISXML_API_KEY:
        return {"source": "WHOIS", "status": "no_api_key", "data": {}}

    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(
                url,
                params={
                    "apiKey": WHOISXML_API_KEY,
                    "domainName": domain,
                    "outputFormat": "JSON",
                },
            )
            if resp.status_code != 200:
                return {"source": "WHOIS", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json().get("WhoisRecord", {}) or {}
            registrant = d.get("registrant", {}) or {}
            registrant_name = (registrant.get("name") or "").lower()
            return {
                "source": "WHOIS",
                "status": "success",
                "data": {
                    "registrar": d.get("registrarName"),
                    "created": d.get("createdDate"),
                    "expires": d.get("expiresDate"),
                    "updated": d.get("updatedDate"),
                    "registrant_name": registrant.get("name"),
                    "registrant_org": registrant.get("organization"),
                    "registrant_country": registrant.get("country"),
                    "privacy_protected": "privacy" in registrant_name or "redacted" in registrant_name,
                },
            }
        except Exception as e:
            return {"source": "WHOIS", "status": "error", "data": {"error": str(e)}}


async def _check_numverify(phone: str) -> dict:
    """Validate and enrich phone number via NumVerify."""
    if not NUMVERIFY_API_KEY:
        return {"source": "NumVerify", "status": "no_api_key", "data": {}}

    url = "http://apilayer.net/api/validate"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(
                url,
                params={"access_key": NUMVERIFY_API_KEY, "number": phone, "format": 1},
            )
            if resp.status_code != 200:
                return {"source": "NumVerify", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json() or {}
            return {
                "source": "NumVerify",
                "status": "success",
                "data": {
                    "valid": d.get("valid"),
                    "country": d.get("country_name"),
                    "carrier": d.get("carrier"),
                    "line_type": d.get("line_type"),
                    "location": d.get("location"),
                    "international_format": d.get("international_format"),
                },
            }
        except Exception as e:
            return {"source": "NumVerify", "status": "error", "data": {"error": str(e)}}


async def _check_email_format(email: str) -> dict:
    """Basic email format and disposable-domain analysis (no API required)."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    is_valid = bool(re.match(pattern, email))
    domain = email.split("@", 1)[-1].lower() if "@" in email else ""
    disposable_domains = {
        "mailinator.com", "guerrillamail.com", "tempmail.com",
        "throwaway.email", "yopmail.com", "sharklasers.com",
        "10minutemail.com", "trashmail.com",
    }
    return {
        "source": "Format Analysis",
        "status": "success",
        "data": {
            "format_valid": is_valid,
            "domain": domain,
            "is_disposable": domain in disposable_domains,
        },
    }


async def _check_username_social(username: str) -> dict:
    """Check username presence on major platforms via concurrent probes."""
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Twitter": f"https://twitter.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
    }

    async def _probe(client, name, url):
        try:
            resp = await client.get(url, timeout=8)
            return name, url, resp.status_code
        except Exception:
            return name, url, None

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        results = await asyncio.gather(*[_probe(client, n, u) for n, u in platforms.items()])

    found, not_found = [], []
    for name, url, status in results:
        if status == 200:
            found.append({"platform": name, "url": url})
        else:
            not_found.append(name)

    return {
        "source": "Social Platforms",
        "status": "success",
        "data": {
            "username": username,
            "found_on": found,
            "not_found_on": not_found,
            "platform_count": len(found),
        },
    }


async def _check_shodan_domain(domain: str) -> dict:
    """Shodan DNS lookup → exposed hosts/services for a domain."""
    if not SHODAN_API_KEY:
        return {"source": "Shodan", "status": "no_api_key", "data": {}}
    if not domain:
        return {"source": "Shodan", "status": "no_domain", "data": {}}

    url = f"https://api.shodan.io/dns/domain/{domain}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"key": SHODAN_API_KEY})
            if resp.status_code != 200:
                return {"source": "Shodan", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json() or {}
            records = d.get("data", []) or []
            ips = sorted({r.get("value") for r in records if r.get("type") == "A" and r.get("value")})
            subdomains = sorted(set(d.get("subdomains", []) or []))
            return {
                "source": "Shodan",
                "status": "success",
                "data": {
                    "domain": d.get("domain"),
                    "subdomain_count": len(subdomains),
                    "subdomains_sample": subdomains[:10],
                    "ip_addresses": ips[:10],
                    "ip_count": len(ips),
                },
            }
        except Exception as e:
            return {"source": "Shodan", "status": "error", "data": {"error": str(e)}}


async def _check_shodan_host(ip: str) -> dict:
    """Shodan host lookup → open ports, banners, vulns for an IP."""
    if not SHODAN_API_KEY:
        return {"source": "Shodan Host", "status": "no_api_key", "data": {}}

    url = f"https://api.shodan.io/shodan/host/{ip}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"key": SHODAN_API_KEY})
            if resp.status_code != 200:
                return {"source": "Shodan Host", "status": f"http_{resp.status_code}", "data": {}}
            d = resp.json() or {}
            vulns_field = d.get("vulns")
            vulns = list(vulns_field.keys())[:20] if isinstance(vulns_field, dict) \
                else (vulns_field or [])[:20]
            return {
                "source": "Shodan Host",
                "status": "success",
                "data": {
                    "ip": d.get("ip_str"),
                    "country": d.get("country_name"),
                    "org": d.get("org"),
                    "isp": d.get("isp"),
                    "os": d.get("os"),
                    "open_ports": d.get("ports", []),
                    "hostnames": d.get("hostnames", []),
                    "vulns": vulns,
                    "tags": d.get("tags", []),
                },
            }
        except Exception as e:
            return {"source": "Shodan Host", "status": "error", "data": {"error": str(e)}}


def _calculate_risk_score(findings: dict) -> int:
    """Calculate a 0-100 risk score from aggregated findings."""
    score = 0
    if findings.get("is_disposable"):
        score += 30
    if findings.get("privacy_protected"):
        score += 10
    if findings.get("deliverable") == "undeliverable":
        score += 20
    if findings.get("line_type") == "voip":
        score += 15
    vulns = findings.get("vulns")
    if isinstance(vulns, list) and vulns:
        score += min(len(vulns) * 5, 30)
    open_ports = findings.get("open_ports")
    if isinstance(open_ports, list) and len(open_ports) > 10:
        score += 10
    return min(score, 100)
