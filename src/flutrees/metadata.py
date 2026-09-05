from __future__ import annotations
from typing import Dict

def parse_header_robust(header: str) -> Dict[str, str]:
    """
    Best-effort parser.
    Legacy format expected: Type|Strain|GISAID|Gene|Status|...
    Never throws; always returns a dict with stable keys.
    """
    out = {
        "type_subtype": "Unknown",
        "strain": "Unknown",
        "gisaid_id": "Unknown",
        "gene_segment": "Unknown",
        "sequence_status": "Unknown",
        "location": "Unknown",
        "date": "Unknown",
        "raw_header": header.strip() if header else "",
    }

    if not header:
        return out

    parts = header.split("|")
    if len(parts) >= 5:
        out["type_subtype"] = parts[0].strip() or "Unknown"
        out["strain"] = parts[1].strip() or "Unknown"
        out["gisaid_id"] = parts[2].strip() or "Unknown"
        out["gene_segment"] = parts[3].strip() or "Unknown"
        out["sequence_status"] = parts[4].strip() or "Unknown"
    else:
        out["strain"] = header.strip()

    sp = out["strain"].split("/")
    if len(sp) >= 4:
        out["location"] = (sp[1].strip() or out["location"])
        out["date"] = (sp[-1].strip() or out["date"])

    return out
