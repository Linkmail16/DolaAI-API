import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
PKG = "com.larus.wolf"
PREFS = f"/data/data/{PKG}/shared_prefs"


def _c3a7f(cmd: str) -> str:
    r = subprocess.run(["adb", "shell", cmd], capture_output=True, text=True, timeout=15)
    return r.stdout.strip()


def _d1b82(xml_str: str) -> dict:
    if not xml_str or "<map" not in xml_str:
        return {}
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return {}
    out = {}
    for child in root:
        name = child.attrib.get("name", "")
        if child.tag == "string":
            out[name] = child.text or ""
        elif child.tag in ("int", "long", "boolean"):
            out[name] = child.attrib.get("value", "")
    return out


def main():
    r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
    devices = [l for l in r.stdout.splitlines() if "\tdevice" in l]
    if not devices:
        print("no adb device connected")
        sys.exit(1)
    print(f"device: {devices[0].split()[0]}")

    print("reading session...")
    script = (
        f"su -c '"
        f"echo ===TOKEN===; cat {PREFS}/token_shared_preference.xml; "
        f"echo ===EXTRA===; cat {PREFS}/passport_extra_header.xml; "
        f"echo ===DTICKET===; cat {PREFS}/account_sdk_d_ticket.xml; "
        f"echo ===ACCOUNT===; cat {PREFS}/com.bytedance.sdk.account_setting.xml; "
        f"'"
    )
    out = _c3a7f(script)

    def _e9f04(tag: str) -> str:
        start = out.find(f"==={tag}===")
        end   = out.find("===", start + len(tag) + 6)
        if start == -1:
            return ""
        return out[start + len(tag) + 6: end if end != -1 else None].strip()

    tokens  = _d1b82(_e9f04("TOKEN"))
    extra   = _d1b82(_e9f04("EXTRA"))
    dticket = _d1b82(_e9f04("DTICKET"))
    account = _d1b82(_e9f04("ACCOUNT"))

    x_tt_token  = tokens.get("X-Tt-Token", "")
    mfa_token   = tokens.get("mfa_token", "")
    supplement  = extra.get("x-tt-token-supplement", "")
    d_ticket    = next(iter(dticket.values()), "")
    uid         = account.get("user_id", "") or account.get("uid", "")
    name        = account.get("user_name", "") or account.get("name", "")

    if not uid and x_tt_token.startswith("03"):
        candidate = x_tt_token[2:20]
        if candidate.isdigit():
            uid = candidate

    if not x_tt_token:
        print("X-Tt-Token not found, make sure you are logged in to the app")
        sys.exit(1)

    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    config = {
        **existing,
        "uid":                     uid or existing.get("uid", ""),
        "bot_id":                  "7241547611541340167",
        "device_id":               existing.get("device_id",  "7681452747673093652"),
        "install_id":              existing.get("install_id", "7681561912517068597"),
        "cdid":                    existing.get("cdid", "ee3c4d85-c8f0-4c57-8027-1ec83293a5d5"),
        "x_tt_token":              x_tt_token,
        "x_tt_token_supplement":   supplement,
        "x_tt_passport_mfa_token": mfa_token,
        "d_ticket":                d_ticket or existing.get("d_ticket", ""),
        "odin_tt":                 existing.get("odin_tt", ""),
        "sessionid":               existing.get("sessionid", ""),
        "carrier_region":          existing.get("carrier_region", "co"),
        "language":                existing.get("language", "es"),
        "sys_region":              existing.get("sys_region", "US"),
        "tz_name":                 existing.get("tz_name", "America%2FBogota"),
        "device_type":             existing.get("device_type", "SM-A525M"),
        "device_brand":            existing.get("device_brand", "samsung"),
        "os_version":              existing.get("os_version", "14"),
        "app_version_code":        existing.get("app_version_code", "14080001"),
        "app_version_name":        existing.get("app_version_name", "14.8.0"),
        "name":                    name or existing.get("name", ""),
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"uid:        {config['uid'] or '(not found)'}")
    print(f"name:       {config['name'] or '(not found)'}")
    print(f"x-tt-token: {x_tt_token[:40]}...")
    print(f"d_ticket:   {d_ticket or '(not found)'}")
    print(f"config saved to: {CONFIG_PATH}")


if __name__ == "__main__":
    main()
