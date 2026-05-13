"""
Fraud Case Intelligence Packager
Formats victim-submitted case data into agency-ready report bundles.
Supports IC3, FBI Cyber Division, Secret Service ECSAP formats.
"""

import os
import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "/tmp/cyberintel_reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


async def package_fraud_case(case_data: dict) -> dict:
    """
    Main packager. Generates formatted reports for each target agency.
    Returns file paths and submission metadata.
    """
    case_id = case_data.get("case_id", f"CASE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    target_agencies = case_data.get("target_agencies", ["IC3"])

    packages = {}

    for agency in target_agencies:
        if agency == "IC3":
            packages["IC3"] = _format_ic3(case_data, case_id)
        elif agency == "FBI":
            packages["FBI"] = _format_fbi(case_data, case_id)
        elif agency == "SECRET_SERVICE":
            packages["SECRET_SERVICE"] = _format_secret_service(case_data, case_id)

    # Save JSON bundles
    output_files = []
    for agency, content in packages.items():
        filename = REPORTS_DIR / f"{case_id}_{agency}.json"
        with open(filename, "w") as f:
            json.dump(content, f, indent=2)
        output_files.append(str(filename))

    # Generate summary report
    summary = _build_summary(case_data, case_id, packages)
    summary_file = REPORTS_DIR / f"{case_id}_SUMMARY.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    return {
        "case_id": case_id,
        "generated_at": datetime.utcnow().isoformat(),
        "packages": list(packages.keys()),
        "output_files": output_files,
        "summary": summary,
        "submission_links": _get_submission_links(target_agencies),
        "next_steps": _get_next_steps(case_data)
    }


def _format_ic3(case: dict, case_id: str) -> dict:
    """IC3 (Internet Crime Complaint Center) report format."""
    return {
        "report_type": "IC3_COMPLAINT",
        "case_reference": case_id,
        "submission_url": "https://www.ic3.gov/Home/FileComplaint",
        "generated": datetime.utcnow().isoformat(),
        "complainant": {
            "name": case.get("victim_name"),
            "email": case.get("victim_email"),
        },
        "incident": {
            "type": case.get("incident_type"),
            "date": case.get("incident_date"),
            "description": case.get("description"),
            "financial_loss_usd": case.get("financial_loss", 0),
            "currency": "USD"
        },
        "subject_info": case.get("suspect_info", {}),
        "evidence_list": case.get("evidence", []),
        "narrative": _build_narrative(case),
        "ic3_categories": _map_to_ic3_categories(case.get("incident_type", ""))
    }


def _format_fbi(case: dict, case_id: str) -> dict:
    """FBI Cyber Division tip format."""
    return {
        "report_type": "FBI_CYBER_TIP",
        "case_reference": case_id,
        "submission_url": "https://tips.fbi.gov",
        "generated": datetime.utcnow().isoformat(),
        "priority": _assess_priority(case),
        "victim": {
            "name": case.get("victim_name"),
            "contact": case.get("victim_email"),
        },
        "crime_classification": _classify_crime(case.get("incident_type", "")),
        "incident_summary": case.get("description"),
        "incident_date": case.get("incident_date"),
        "estimated_loss": case.get("financial_loss", 0),
        "suspect_profile": case.get("suspect_info", {}),
        "digital_evidence": case.get("evidence", []),
        "interstate_nexus": True,
        "narrative": _build_narrative(case)
    }


def _format_secret_service(case: dict, case_id: str) -> dict:
    """Secret Service ECSAP (Electronic Crimes Special Agent Program) format."""
    return {
        "report_type": "ECSAP_REFERRAL",
        "case_reference": case_id,
        "submission_url": "https://www.secretservice.gov/investigation/financialcrimes",
        "generated": datetime.utcnow().isoformat(),
        "victim_information": {
            "name": case.get("victim_name"),
            "email": case.get("victim_email"),
        },
        "financial_crime_type": _map_to_ecsap_category(case.get("incident_type", "")),
        "financial_loss": {
            "amount": case.get("financial_loss", 0),
            "currency": "USD",
            "method": case.get("suspect_info", {}).get("payment_method", "Unknown")
        },
        "date_of_incident": case.get("incident_date"),
        "incident_description": case.get("description"),
        "suspect_data": case.get("suspect_info", {}),
        "supporting_evidence": case.get("evidence", []),
        "threshold_met": case.get("financial_loss", 0) >= 1000,  # ECSAP threshold
        "narrative": _build_narrative(case)
    }


def _build_narrative(case: dict) -> str:
    """Build a formal narrative summary from case data."""
    return (
        f"On {case.get('incident_date', 'an unspecified date')}, victim {case.get('victim_name', 'Unknown')} "
        f"reported an incident of type '{case.get('incident_type', 'Unknown')}'. "
        f"The victim sustained a financial loss of ${case.get('financial_loss', 0):,.2f} USD. "
        f"Incident description: {case.get('description', 'No description provided.')} "
        f"{'Suspect information has been provided.' if case.get('suspect_info') else 'No suspect information available.'} "
        f"{'Supporting evidence has been attached.' if case.get('evidence') else 'No evidence attached.'}"
    )


def _map_to_ic3_categories(incident_type: str) -> list:
    mapping = {
        "crypto_scam": ["Cryptocurrency", "InvestmentFraud"],
        "romance_scam": ["ConfidenceFraud", "RomanceScam"],
        "phishing": ["Phishing", "Spoofing"],
        "deed_fraud": ["RealEstateFraud", "TitleFraud"],
        "business_email": ["BEC", "EmailAccountCompromise"],
        "identity_theft": ["IdentityTheft"],
        "ransomware": ["Ransomware", "CyberExtortion"],
    }
    return mapping.get(incident_type.lower(), ["Other"])


def _classify_crime(incident_type: str) -> str:
    mapping = {
        "crypto_scam": "Wire Fraud / Cryptocurrency Fraud",
        "romance_scam": "Wire Fraud / Romance Fraud",
        "phishing": "Computer Fraud / Phishing",
        "deed_fraud": "Real Estate / Title Fraud",
        "business_email": "Business Email Compromise",
        "identity_theft": "Identity Theft",
        "ransomware": "Ransomware / Extortion",
    }
    return mapping.get(incident_type.lower(), "Computer Fraud")


def _map_to_ecsap_category(incident_type: str) -> str:
    mapping = {
        "crypto_scam": "Electronic Financial Fraud",
        "deed_fraud": "Real Property Fraud",
        "business_email": "Business Email Compromise",
        "identity_theft": "Access Device Fraud",
    }
    return mapping.get(incident_type.lower(), "Electronic Crimes")


def _assess_priority(case: dict) -> str:
    loss = case.get("financial_loss", 0)
    if loss >= 100000:
        return "HIGH"
    elif loss >= 10000:
        return "MEDIUM"
    return "STANDARD"


def _build_summary(case: dict, case_id: str, packages: dict) -> dict:
    return {
        "case_id": case_id,
        "victim": case.get("victim_name"),
        "incident_type": case.get("incident_type"),
        "financial_loss": case.get("financial_loss", 0),
        "priority": _assess_priority(case),
        "agencies_reported": list(packages.keys()),
        "generated_at": datetime.utcnow().isoformat()
    }


def _get_submission_links(agencies: list) -> dict:
    links = {
        "IC3": "https://www.ic3.gov/Home/FileComplaint",
        "FBI": "https://tips.fbi.gov",
        "SECRET_SERVICE": "https://www.secretservice.gov/investigation/financialcrimes"
    }
    return {a: links[a] for a in agencies if a in links}


def _get_next_steps(case: dict) -> list:
    steps = [
        "Submit IC3 complaint using the generated report",
        "Keep all digital evidence in original format",
        "Document all communications with suspects",
        "Contact your bank/financial institution immediately if funds were transferred",
    ]
    if case.get("financial_loss", 0) >= 10000:
        steps.append("Contact your local FBI field office directly given financial loss amount")
    if case.get("incident_type") == "deed_fraud":
        steps.append("File an emergency injunction with your county recorder's office")
    return steps
