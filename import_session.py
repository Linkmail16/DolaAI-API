import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

_KEYS = {
    "sessionid", "odin_tt", "sid_guard", "sid_tt", "ttwid",
    "store-idc", "store-country-code", "store-country-code-src",
    "uid_tt", "uid_tt_ss", "sessionid_ss",
}


def _e4c91(raw: str) -> dict:
    cookies = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            cookies[k.strip()] = v.strip()
    return cookies


def _f7a03(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()

    lines = raw.splitlines()
    first = lines[0].strip().lower() if lines else ""

    if first == "json:" or (first == "[" or raw.lstrip().startswith("[")):
        start = raw.find("[")
        entries = json.loads(raw[start:])
        return {e["name"]: e["value"] for e in entries if "name" in e}

    if first == "header string":
        for line in lines[1:]:
            line = line.strip()
            if line and "=" in line:
                return _e4c91(line)
        return {}

    if first.startswith("# netscape") or first.startswith("# http"):
        cookies = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#HttpOnly_"):
                line = line[len("#HttpOnly_"):]
            elif line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
        return cookies

    if "=" in raw and "\n" not in raw.strip():
        return _e4c91(raw)

    cookies = {}
    for line in lines:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            cookies[k.strip()] = v.strip()
    return cookies


def load_web_session(path: str) -> dict:
    cookies = _f7a03(path)

    sessionid = cookies.get("sessionid", "")
    odin_tt   = cookies.get("odin_tt", "")
    sid_guard = cookies.get("sid_guard", "")
    store_idc = cookies.get("store-idc", "maliva")
    carrier   = cookies.get("store-country-code", "us").lower()
    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    config = {
        **existing,
        "uid":             existing.get("uid", ""),
        "bot_id":          "7241547611541340167",
        "device_id":       existing.get("device_id",  "7681452747673093652"),
        "install_id":      existing.get("install_id", "7681561912517068597"),
        "cdid":            existing.get("cdid", "ee3c4d85-c8f0-4c57-8027-1ec83293a5d5"),
        "x_tt_token":      existing.get("x_tt_token", ""),
        "x_tt_token_supplement":   existing.get("x_tt_token_supplement", ""),
        "x_tt_passport_mfa_token": existing.get("x_tt_passport_mfa_token", ""),
        "odin_tt":         odin_tt,
        "d_ticket":        existing.get("d_ticket", ""),
        "sessionid":       sessionid,
        "sid_guard":       sid_guard,
        "store-idc":       store_idc,
        "carrier_region":  carrier,
        "language":        existing.get("language", "es"),
        "sys_region":      existing.get("sys_region", "US"),
        "tz_name":         existing.get("tz_name", "America%2FBogota"),
        "device_type":     existing.get("device_type", "SM-A525M"),
        "device_brand":    existing.get("device_brand", "samsung"),
        "os_version":      existing.get("os_version", "14"),
        "app_version_code": existing.get("app_version_code", "14080001"),
        "app_version_name": existing.get("app_version_name", "14.8.0"),
        "name":            existing.get("name", ""),
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python import_session.py <cookies_file>")
        sys.exit(1)
    cfg = load_web_session(sys.argv[1])
    print(f"session imported. uid: {cfg['uid'] or '(not found)'}")
    print(f"sessionid: {cfg['sessionid'][:20]}...")
