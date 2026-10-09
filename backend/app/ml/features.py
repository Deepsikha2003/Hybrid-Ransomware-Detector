"""File parsing and feature alignment.

Uploaded files are treated strictly as DATA (CSV/TXT/LOG). Nothing uploaded is ever executed.
- CSV (or delimited TXT/LOG with a header): one row = one sample; columns are matched by name to the
  feature list stored inside each trained model bundle.
- Sysmon-style text logs: one event per line; engineered behavioural features are derived (see below).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import settings

ALLOWED_EXT = {"csv", "txt", "log"}

# Engineered schema produced by parse_event_log(); used by the demo behavioural model and any
# behavioural model you train on features with these names.
BEHAVIOR_FEATURES = [
    "process_create_count", "file_create_count", "registry_mod_count", "network_conn_count",
    "unique_file_extensions", "ransom_extension_count", "ransom_note_count",
    "shadow_copy_cmd_count", "backup_tamper_cmd_count", "suspicious_cmd_count",
    "unique_processes", "unique_dest_ips", "file_creates_per_process",
]

# Indicative PE-header schema for the demo static model (real datasets define their own columns).
STATIC_FEATURES = [
    "NumberOfSections", "SizeOfCode", "SizeOfInitializedData", "AddressOfEntryPoint", "ImageBase",
    "SectionsMeanEntropy", "SectionsMaxEntropy", "ResourcesMeanEntropy", "ImportsNb", "ImportsNbDLL",
    "DllCharacteristics", "Characteristics", "Subsystem", "SizeOfImage", "SizeOfHeaders", "CheckSum",
]

RANSOM_EXT = {".locked", ".encrypted", ".crypt", ".crypted", ".enc", ".lockbit", ".ryk", ".wncry", ".wnry", ".cerber", ".zepto", ".locky", ".petya", ".conti", ".blackcat", ".akira"}
NOTE_PAT = re.compile(r"(readme|decrypt|recover|restore|how_to|ransom|_help_)[^\\/]*\.(txt|html|hta)$", re.I)
SHADOW_PAT = re.compile(r"vssadmin.*delete\s+shadows|wmic.*shadowcopy.*delete|Get-WmiObject.*Win32_Shadowcopy", re.I)
BACKUP_PAT = re.compile(r"bcdedit.*(recoveryenabled\s+no|ignoreallfailures)|wbadmin.*delete|wevtutil\s+cl", re.I)
SUSP_PAT = re.compile(r"powershell.*(-enc|-encodedcommand|downloadstring|bypass)|certutil.*-urlcache|mshta|rundll32.*javascript|cipher\s+/w", re.I)
EVENT_PAT = re.compile(r"Event\s*ID\D{0,4}(\d+)", re.I)
KV = lambda key: re.compile(rf"\b{key}\W{{1,3}}(.+?)(?=\s+[A-Za-z]\w*\s*[:=]\s|\s*$)", re.I)  # value runs until the next "Key:" token (paths may contain spaces)
IMAGE_PAT, TARGET_PAT, DEST_PAT, CMD_PAT = KV("Image"), KV("TargetFilename"), KV("DestinationIp"), re.compile(r"CommandLine\W{1,3}(.+)$", re.I)


class ParseError(ValueError):
    pass


def parse_event_log(text: str) -> pd.DataFrame:
    procs, ips, exts = set(), set(), set()
    c = dict.fromkeys(["p", "f", "r", "n", "ren", "note", "shadow", "backup", "susp"], 0)
    events = 0
    for line in text.splitlines():
        m = EVENT_PAT.search(line)
        if not m:
            continue
        events += 1
        eid = int(m.group(1))
        img = IMAGE_PAT.search(line)
        if img:
            procs.add(img.group(1).lower())
        cmd = CMD_PAT.search(line)
        cmdline = cmd.group(1) if cmd else line
        if eid == 1:
            c["p"] += 1
            c["shadow"] += bool(SHADOW_PAT.search(cmdline))
            c["backup"] += bool(BACKUP_PAT.search(cmdline))
            c["susp"] += bool(SUSP_PAT.search(cmdline))
        elif eid == 11:
            c["f"] += 1
            t = TARGET_PAT.search(line)
            if t:
                path = t.group(1)
                ext = Path(path.replace("\\", "/")).suffix.lower()
                exts.add(ext)
                c["ren"] += ext in RANSOM_EXT
                c["note"] += bool(NOTE_PAT.search(path))
        elif eid in (12, 13, 14):
            c["r"] += 1
        elif eid == 3:
            c["n"] += 1
            d = DEST_PAT.search(line)
            if d:
                ips.add(d.group(1))
    if events == 0:
        raise ParseError("No event records found (expected lines containing 'EventID: <n>').")
    row = {
        "process_create_count": c["p"], "file_create_count": c["f"], "registry_mod_count": c["r"],
        "network_conn_count": c["n"], "unique_file_extensions": len(exts), "ransom_extension_count": c["ren"],
        "ransom_note_count": c["note"], "shadow_copy_cmd_count": c["shadow"], "backup_tamper_cmd_count": c["backup"],
        "suspicious_cmd_count": c["susp"], "unique_processes": len(procs), "unique_dest_ips": len(ips),
        "file_creates_per_process": c["f"] / max(len(procs), 1),
    }
    return pd.DataFrame([row])


def parse_upload(path: Path, ext: str) -> pd.DataFrame:
    ext = ext.lower().lstrip(".")
    if ext not in ALLOWED_EXT:
        raise ParseError(f"Unsupported file type '.{ext}'. Allowed: CSV, TXT, LOG.")
    raw = path.read_bytes()
    if b"\x00" in raw[:8192]:
        raise ParseError("File looks binary. Upload extracted feature data (CSV/TXT/LOG), not executables.")
    text = raw.decode("utf-8", errors="replace")
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    if not first:
        raise ParseError("File is empty.")
    looks_tabular = ext == "csv" or (first.count(",") >= 2 or first.count("\t") >= 2) and not EVENT_PAT.search(first)
    if looks_tabular:
        try:
            df = pd.read_csv(path, sep=None, engine="python", nrows=settings.max_rows, on_bad_lines="skip")
        except Exception as exc:  # noqa: BLE001
            raise ParseError(f"Could not parse tabular data: {exc}") from exc
        df.columns = [str(c).strip() for c in df.columns]
        df = df.replace([np.inf, -np.inf], np.nan).dropna(how="all")
        if df.empty:
            raise ParseError("No data rows found.")
        return df
    return parse_event_log(text)


def align(df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, float]:
    """Return a frame with exactly `features` (numeric, NaN where absent) and the fraction of features present."""
    lookup = {c.lower(): c for c in df.columns}
    cols, hit = {}, 0
    for f in features:
        src = lookup.get(f.lower())
        if src is not None:
            hit += 1
            cols[f] = pd.to_numeric(df[src], errors="coerce")
        else:
            cols[f] = pd.Series(np.nan, index=df.index)
    out = pd.DataFrame(cols).replace([np.inf, -np.inf], np.nan)
    return out, hit / max(len(features), 1)
