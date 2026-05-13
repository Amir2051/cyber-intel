"""
Crypto Wallet Tracer Module
Traces wallet transactions, flags known scam addresses, builds transaction graphs.
Supports ETH, BTC, BNB, and TRON.
"""

import os
from datetime import datetime

import httpx

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
TRONSCAN_API_KEY = os.getenv("TRONSCAN_API_KEY")
BLOCKCHAIN_API_KEY = os.getenv("BLOCKCHAIN_API_KEY")  # blockchain.info, optional

# Known scam/blacklist addresses (expandable database — populate from threat feeds)
KNOWN_SCAM_ADDRESSES: set[str] = set()

DEFAULT_TIMEOUT = 15.0


async def trace_wallet(address: str, chain: str = "eth") -> dict:
    """
    Main tracer entry point. Returns transaction history,
    risk flags, and graph-ready node/edge data.
    """
    chain = (chain or "eth").lower()
    # EVM chains use lowercase 0x..., BTC and TRON are case-sensitive
    addr_key = address.strip().lower() if chain in ("eth", "bnb") else address.strip()

    result = {
        "address": addr_key,
        "chain": chain,
        "timestamp": datetime.utcnow().isoformat(),
        "risk_flags": [],
        "risk_score": 0,
        "transactions": [],
        "connected_wallets": [],
        "graph": {"nodes": [], "edges": []},
        "summary": {},
    }

    if chain == "eth":
        await _trace_eth(addr_key, result)
    elif chain == "btc":
        await _trace_btc(addr_key, result)
    elif chain == "bnb":
        await _trace_bnb(addr_key, result)
    elif chain == "tron":
        await _trace_tron(addr_key, result)
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    if addr_key in KNOWN_SCAM_ADDRESSES:
        result["risk_flags"].append("ADDRESS_IN_SCAM_DATABASE")
        result["risk_score"] += 80

    result["risk_score"] = min(result["risk_score"], 100)
    return result


async def _trace_eth(address: str, result: dict):
    """Trace Ethereum wallet via Etherscan V2 (chainid=1)."""
    if not ETHERSCAN_API_KEY:
        result["risk_flags"].append("NO_ETHERSCAN_API_KEY")
        return

    base = "https://api.etherscan.io/v2/api"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            txn_resp = await client.get(base, params={
                "chainid": 1,
                "module": "account", "action": "txlist", "address": address,
                "startblock": 0, "endblock": 99999999, "page": 1, "offset": 50,
                "sort": "desc", "apikey": ETHERSCAN_API_KEY,
            })
            bal_resp = await client.get(base, params={
                "chainid": 1,
                "module": "account", "action": "balance", "address": address,
                "tag": "latest", "apikey": ETHERSCAN_API_KEY,
            })
        except Exception as e:
            result["risk_flags"].append(f"ETH_LOOKUP_ERROR: {e}")
            return

    txn_data = txn_resp.json() if txn_resp.status_code == 200 else {}
    bal_data = bal_resp.json() if bal_resp.status_code == 200 else {}

    txns = txn_data.get("result", [])
    if not isinstance(txns, list):
        txns = []

    result["transactions"] = [
        {
            "hash": t.get("hash"),
            "from": t.get("from"),
            "to": t.get("to"),
            "value_eth": int(t.get("value", 0) or 0) / 1e18,
            "timestamp": datetime.fromtimestamp(int(t.get("timeStamp", 0) or 0)).isoformat(),
            "status": "success" if t.get("isError") == "0" else "failed",
            "gas_used": t.get("gasUsed"),
        }
        for t in txns[:50]
    ]

    nodes = {address: {"id": address, "type": "subject", "tx_count": len(txns)}}
    edges = []
    connected = set()
    for t in txns[:20]:
        frm = (t.get("from") or "").lower()
        to = (t.get("to") or "").lower()
        val = int(t.get("value", 0) or 0) / 1e18
        for addr in (frm, to):
            if addr and addr != address and addr not in nodes:
                nodes[addr] = {"id": addr, "type": "connected", "tx_count": 1}
                connected.add(addr)
        edges.append({"source": frm, "target": to, "value_eth": val, "hash": t.get("hash")})

        if to and to != address and val > 1.0:
            result["risk_flags"].append(f"LARGE_OUTFLOW_{val:.2f}_ETH_TO_{to[:10]}")
            result["risk_score"] += 15

    result["graph"]["nodes"] = list(nodes.values())
    result["graph"]["edges"] = edges
    result["connected_wallets"] = list(connected)[:20]

    try:
        balance_wei = int(bal_data.get("result", 0) or 0)
    except (TypeError, ValueError):
        balance_wei = 0
    result["summary"] = {
        "balance_eth": balance_wei / 1e18,
        "transaction_count": len(result["transactions"]),
        "connected_wallet_count": len(result["connected_wallets"]),
    }

    if len(result["transactions"]) > 20 and result["summary"]["balance_eth"] < 0.001:
        result["risk_flags"].append("HIGH_VOLUME_NEAR_ZERO_BALANCE")
        result["risk_score"] += 25


async def _trace_btc(address: str, result: dict):
    """Trace Bitcoin wallet via blockchain.info."""
    url = f"https://blockchain.info/rawaddr/{address}?limit=50"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url)
        except Exception as e:
            result["risk_flags"].append(f"BTC_ERROR: {e}")
            return

    if resp.status_code != 200:
        result["risk_flags"].append("BTC_LOOKUP_FAILED")
        return

    try:
        data = resp.json()
    except Exception as e:
        result["risk_flags"].append(f"BTC_PARSE_ERROR: {e}")
        return

    txns = data.get("txs", []) or []
    result["transactions"] = [
        {
            "hash": t.get("hash"),
            "time": datetime.fromtimestamp(t.get("time", 0) or 0).isoformat(),
            "inputs": [i.get("prev_out", {}).get("addr") for i in (t.get("inputs", []) or [])],
            "outputs": [o.get("addr") for o in (t.get("out", []) or [])],
            "value_btc": sum(o.get("value", 0) or 0 for o in (t.get("out", []) or [])) / 1e8,
        }
        for t in txns[:50]
    ]
    result["summary"] = {
        "balance_btc": (data.get("final_balance", 0) or 0) / 1e8,
        "total_received_btc": (data.get("total_received", 0) or 0) / 1e8,
        "transaction_count": data.get("n_tx", 0) or 0,
    }


async def _trace_bnb(address: str, result: dict):
    """Trace BNB Smart Chain wallet via Etherscan V2 (chainid=56).

    The Etherscan V2 unified API accepts BSC via chainid and reuses the
    Etherscan API key — no separate BscScan key required.
    """
    api_key = BSCSCAN_API_KEY or ETHERSCAN_API_KEY
    if not api_key:
        result["risk_flags"].append("NO_BSCSCAN_API_KEY")
        return

    base = "https://api.etherscan.io/v2/api"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            txn_resp = await client.get(base, params={
                "chainid": 56,
                "module": "account", "action": "txlist", "address": address,
                "startblock": 0, "endblock": 99999999, "page": 1, "offset": 50,
                "sort": "desc", "apikey": api_key,
            })
        except Exception as e:
            result["risk_flags"].append(f"BNB_ERROR: {e}")
            return

    txns = txn_resp.json().get("result", []) if txn_resp.status_code == 200 else []
    if not isinstance(txns, list):
        txns = []

    result["transactions"] = [
        {
            "hash": t.get("hash"),
            "from": t.get("from"),
            "to": t.get("to"),
            "value_bnb": int(t.get("value", 0) or 0) / 1e18,
            "timestamp": datetime.fromtimestamp(int(t.get("timeStamp", 0) or 0)).isoformat(),
            "status": "success" if t.get("isError") == "0" else "failed",
        }
        for t in txns[:50]
    ]
    result["summary"] = {
        "transaction_count": len(result["transactions"]),
        "chain": "BSC",
    }


async def _trace_tron(address: str, result: dict):
    """Trace TRON wallet via TronScan public API."""
    url = "https://apilist.tronscanapi.com/api/transaction"
    headers = {"TRON-PRO-API-KEY": TRONSCAN_API_KEY} if TRONSCAN_API_KEY else {}
    params = {"address": address, "limit": 50, "start": 0, "sort": "-timestamp"}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=headers) as client:
        try:
            resp = await client.get(url, params=params)
        except Exception as e:
            result["risk_flags"].append(f"TRON_ERROR: {e}")
            return

    if resp.status_code != 200:
        result["risk_flags"].append("TRON_LOOKUP_FAILED")
        return

    try:
        data = resp.json()
    except Exception as e:
        result["risk_flags"].append(f"TRON_PARSE_ERROR: {e}")
        return

    txns = data.get("data", []) or []
    result["transactions"] = [
        {
            "hash": t.get("hash"),
            "from": t.get("ownerAddress"),
            "to": t.get("toAddress"),
            "value_trx": (t.get("amount", 0) or 0) / 1e6,
            "timestamp": datetime.fromtimestamp((t.get("timestamp", 0) or 0) / 1000).isoformat()
            if t.get("timestamp") else None,
            "contract_type": t.get("contractType"),
        }
        for t in txns[:50]
    ]
    result["summary"] = {
        "transaction_count": data.get("total", len(result["transactions"])),
        "chain": "TRON",
    }
