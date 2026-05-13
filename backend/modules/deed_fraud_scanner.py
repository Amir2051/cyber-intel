"""
Deed Fraud Early Warning Scanner
Detects suspicious property transfers using public records and pattern matching.
"""

import os
import httpx
from datetime import datetime

ATTOM_API_KEY = os.getenv("ATTOM_API_KEY")  # ATTOM Data Solutions - property data


async def scan_deed_fraud(property_address: str, owner_name: str, county: str, state: str) -> dict:
    """
    Scan for deed fraud indicators on a given property.
    """
    result = {
        "property_address": property_address,
        "owner_name": owner_name,
        "county": county,
        "state": state,
        "timestamp": datetime.utcnow().isoformat(),
        "risk_score": 0,
        "risk_flags": [],
        "property_data": {},
        "transfer_history": [],
        "recommendations": []
    }

    await _lookup_property(property_address, state, result)
    _analyze_fraud_patterns(result)
    _generate_recommendations(result)

    return result


async def _lookup_property(address: str, state: str, result: dict):
    """Lookup property data via ATTOM API."""
    if not ATTOM_API_KEY:
        result["risk_flags"].append("NO_PROPERTY_API_KEY")
        result["property_data"] = {
            "note": "Connect ATTOM_API_KEY for live property lookup",
            "manual_check": f"https://www.countyoffice.org/property-records/"
        }
        return

    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    headers = {
        "apikey": ATTOM_API_KEY,
        "Accept": "application/json"
    }
    params = {"address": address}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                prop = data.get("property", [{}])[0]
                summary = prop.get("summary", {})
                sale = prop.get("sale", {})

                result["property_data"] = {
                    "address": prop.get("address", {}).get("oneLine"),
                    "assessed_value": summary.get("propAssessedValue"),
                    "year_built": summary.get("yearBuilt"),
                    "owner": sale.get("sellerName"),
                    "last_sale_date": sale.get("saleTransDate"),
                    "last_sale_amount": sale.get("amount", {}).get("saleAmt"),
                    "property_type": summary.get("propClass"),
                }

                result["transfer_history"] = [{
                    "date": sale.get("saleTransDate"),
                    "amount": sale.get("amount", {}).get("saleAmt"),
                    "seller": sale.get("sellerName"),
                    "buyer": sale.get("buyerName"),
                }]
        except Exception as e:
            result["risk_flags"].append(f"PROPERTY_LOOKUP_ERROR: {str(e)}")


def _analyze_fraud_patterns(result: dict):
    """Detect fraud indicators in property data."""
    prop = result.get("property_data", {})
    transfers = result.get("transfer_history", [])

    # Pattern: Recent transfer with no corresponding sale amount (gift deed fraud)
    for transfer in transfers:
        if transfer.get("date") and not transfer.get("amount"):
            result["risk_flags"].append("TRANSFER_WITH_NO_CONSIDERATION")
            result["risk_score"] += 40

    # Pattern: Sale price significantly below assessed value
    assessed = prop.get("assessed_value")
    sale_amt = prop.get("last_sale_amount")
    if assessed and sale_amt:
        try:
            ratio = float(sale_amt) / float(assessed)
            if ratio < 0.5:
                result["risk_flags"].append("SALE_PRICE_BELOW_50PCT_ASSESSED")
                result["risk_score"] += 35
        except (ValueError, ZeroDivisionError):
            pass

    # Pattern: Owner name mismatch with provided name
    recorded_owner = prop.get("owner", "").lower()
    provided_owner = result.get("owner_name", "").lower()
    if recorded_owner and provided_owner:
        if provided_owner not in recorded_owner and recorded_owner not in provided_owner:
            result["risk_flags"].append("OWNER_NAME_MISMATCH_WITH_RECORDS")
            result["risk_score"] += 50

    result["risk_score"] = min(result["risk_score"], 100)


def _generate_recommendations(result: dict):
    """Generate action steps based on risk assessment."""
    score = result["risk_score"]
    flags = result["risk_flags"]

    if score >= 60:
        result["recommendations"].extend([
            "URGENT: File an emergency deed restriction with your county recorder",
            "Contact a real estate attorney immediately",
            "Submit a report to your state's real estate fraud unit",
            "Place a security freeze on your credit with all three bureaus"
        ])
    elif score >= 30:
        result["recommendations"].extend([
            "Monitor property records monthly for unauthorized changes",
            "Consider a deed restriction or owner's title insurance",
            "Verify ownership records directly with county recorder"
        ])
    else:
        result["recommendations"].append(
            "No immediate action required — continue routine monitoring"
        )

    if "OWNER_NAME_MISMATCH_WITH_RECORDS" in flags:
        result["recommendations"].append(
            "Obtain a certified copy of the current deed from county recorder"
        )
