#!/usr/bin/env python3
"""
NNAnet OMS "Sales by Model Line" batch downloader (per-store cookies, .env loaded)

Env vars required in a .env file next to this script:
  HICKORY_COOKIE=...
  CONCORD_COOKIE=...
  WINSTON_COOKIE=...
  LAKE_COOKIE=...
Each value is the full "k=v; k=v; ..." cookie string (quotes optional).
"""

import os
import sys
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime
import requests
from dotenv import load_dotenv

# ----------------------------- CONFIG ---------------------------------

JOBS = [
    {"dlr": "5544", "name": "Hickory"},
    {"dlr": "3768", "name": "Concord"},
    {"dlr": "2755", "name": "Winston"},
    {"dlr": "3919", "name": "Lake"},
]

ROLL_DAYS = 90
SELL_DAYS = 26
ADD_DATE_STAMP = False
OUTPUT_DIR = "files"     # raw .xls files saved here beside the script
CONVERT_TO = None        # set to None to skip any conversion

# Optional Netscape cookies.txt fallback (used only if that store's env var is missing)
COOKIE_FILE = None  # e.g., r"C:\path\cookies.txt" or leave None

# ----------------------------------------------------------------------

BASE_URL = "https://oms-b.nnanet.com"

def load_env():
    # Load .env from the script directory
    env_path = Path(__file__).with_name(".env")
    load_dotenv(env_path)

def make_session_from_cookie_string(cookie_header: str | None, cookie_file: str | None) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Origin": BASE_URL,
        "Referer": urljoin(BASE_URL, "/sales/modelline"),
    })

    if cookie_header:
        ch = cookie_header.strip().strip('"')  # allow quoted values in .env
        for part in ch.split(";"):
            if "=" in part:
                name, value = part.strip().split("=", 1)
                # set for exact host and parent domain
                for dom in ("oms-b.nnanet.com", ".nnanet.com"):
                    s.cookies.set(name, value, domain=dom)
    elif cookie_file:
        with open(cookie_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    domain, flag, path, secure, expiry, name, value = line.split("\t")
                    s.cookies.set(name, value, domain=domain, path=path)
                except ValueError:
                    continue
    else:
        print("ERROR: no cookie provided.", file=sys.stderr)
        sys.exit(2)

    return s

def set_selling_days(session: requests.Session, roll_days: int, sell_days: int) -> None:
    params = {
        "startDate": "" if roll_days in (30, 90) else "",
        "rollDays": str(roll_days) if roll_days in (30, 90) else "",
        "endDate": "",
        "sourcePage": "selldays",
        "targetPage": "modelline",
        "sellDays": str(sell_days),
    }
    url = urljoin(BASE_URL, "/sales/selldays")
    r = session.get(url, params=params, allow_redirects=True, timeout=30)
    r.raise_for_status()

def download_excel(session: requests.Session, out_path: Path, dlr: str, roll_days: int) -> None:
    form = {
        "dlrNum": dlr,
        "startDate": "" if roll_days in (30, 90) else "",
        "endDate": "",
        "rollDays": str(roll_days) if roll_days in (30, 90) else "",
        "sellDays": "",
        "modelLine": "",
        "targetPage": "modelline",
        "sourcePage": "modelline",
        "sortBy": "",
        "sortFlag": "",
        "contentType": "Excel",
    }
    url = urljoin(BASE_URL, "/sales/modelline")
    r = session.post(url, data=form, stream=True, timeout=60)
    ct = r.headers.get("Content-Type", "").lower()
    if "text/html" in ct and "excel" not in ct:
        sample = r.content[:4000].decode(errors="ignore")
        if "login" in sample.lower() or "sign in" in sample.lower():
            r.close()
            raise RuntimeError("Got login HTML. Session unauthenticated or expired.")
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

def env_cookie_for(store_name: str) -> str | None:
    # No fallback to OMS_COOKIE. Enforce per-store cookies.
    return os.getenv(f"{store_name.upper()}_COOKIE")

def short_cookie_id(cookie_header: str) -> str:
    ch = cookie_header.strip().strip('"')
    for part in ch.split(";"):
        p = part.strip()
        if p.startswith("JSESSIONID="):
            return "JSESSIONID:" + p.split("=", 1)[1][-8:]
    return (ch[:24] + "...") if len(ch) > 24 else ch

def main():
    load_env()

    date_suffix = datetime.now().strftime("%Y%m%d") if ADD_DATE_STAMP else ""
    script_dir = Path(__file__).resolve().parent
    out_dir = (script_dir / OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0

    for job in JOBS:
        name = job["name"]
        dlr = job["dlr"]

        cookie_header = env_cookie_for(name)
        if not cookie_header and not COOKIE_FILE:
            print(f"[{name}] ERROR: set {name.upper()}_COOKIE in .env or provide COOKIE_FILE.", file=sys.stderr)
            failures += 1
            continue

        s = make_session_from_cookie_string(cookie_header, COOKIE_FILE)
        print(f"[{name}] using cookie → {short_cookie_id(cookie_header or 'cookies.txt')}")

        # quick auth check
        home = urljoin(BASE_URL, "/sales/modelline")
        resp = s.get(home, timeout=30)
        if resp.status_code == 401 or "login" in resp.text.lower():
            print(f"[{name}] Authentication failed. Check {name.upper()}_COOKIE.", file=sys.stderr)
            failures += 1
            continue

        # set selling-days basis
        try:
            set_selling_days(s, ROLL_DAYS, SELL_DAYS)
        except Exception as e:
            print(f"[{name}] ERROR setting sell days: {e}", file=sys.stderr)
            failures += 1
            continue

        base = f"{name}{ROLL_DAYS}"
        if date_suffix:
            base = f"{base}_{date_suffix}"
        xls_path = out_dir / f"{base}.xls"

        print(f"[{name}] dlr={dlr} → {xls_path.name}")
        try:
            download_excel(s, xls_path, dlr, ROLL_DAYS)
            print(f"  saved: {xls_path}")
        except Exception as e:
            failures += 1
            print(f"  ERROR: {e}", file=sys.stderr)

    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()
