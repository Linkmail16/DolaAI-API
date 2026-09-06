import base64
import datetime
import gzip
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
import zlib
import requests

if sys.platform == "win32":
    import subprocess
    subprocess.run(["chcp", "65001"], capture_output=True, shell=True)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

from signer import sign as _sign_request

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def _load_config() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


_CFG = _load_config()

BOT_ID = UID = DEVICE_ID = INSTALL_ID = CDID = ""
LANG = CARRIER = SYS_REGION = TZ = DEV_TYPE = DEV_BRAND = OS_VER = APP_VER = APP_VNAME = ""
BASE_PARAMS = BASE_URL = BASE_URL_IM = BASE_PARAMS_IM = ""
HEADERS: dict = {}


def _init_globals(cfg: dict):
    global _CFG, BOT_ID, UID, DEVICE_ID, INSTALL_ID, CDID
    global LANG, CARRIER, SYS_REGION, TZ, DEV_TYPE, DEV_BRAND, OS_VER, APP_VER, APP_VNAME
    global BASE_PARAMS, BASE_URL, BASE_URL_IM, BASE_PARAMS_IM, HEADERS

    _CFG       = cfg
    BOT_ID     = cfg.get("bot_id",     "7241547611541340167")
    UID        = cfg.get("uid", "")
    DEVICE_ID  = cfg.get("device_id",  "7681452747673093652")
    INSTALL_ID = cfg.get("install_id", "7681561912517068597")
    CDID       = cfg.get("cdid",       "ee3c4d85-c8f0-4c57-8027-1ec83293a5d5")
    LANG       = cfg.get("language",   "es")
    CARRIER    = cfg.get("carrier_region", "co")
    SYS_REGION = cfg.get("sys_region", "US")
    TZ         = cfg.get("tz_name",    "America%2FBogota")
    DEV_TYPE   = cfg.get("device_type",  "SM-A525M")
    DEV_BRAND  = cfg.get("device_brand", "samsung")
    OS_VER     = cfg.get("os_version",   "14")
    APP_VER    = cfg.get("app_version_code", "14080001")
    APP_VNAME  = cfg.get("app_version_name", "14.8.0")

    _common = (
        f"device_platform=android&os=android&ssmix=a"
        f"&cdid={CDID}&channel=googleplay&aid=489823"
        f"&app_name=nova_ai&version_code={APP_VER}&version_name={APP_VNAME}"
        f"&manifest_version_code=14080005&update_version_code=14080040"
        f"&resolution=1080*2186&dpi=420&device_type={DEV_TYPE}&device_brand={DEV_BRAND}"
        f"&language={LANG}&os_api=34&os_version={OS_VER}&ac=wifi"
        f"&uid={UID}&app_language={LANG}&carrier_region={CARRIER}&flow_app_variant=cici"
        f"&sys_region={SYS_REGION}&tz_name={TZ}&system_language_detail={LANG}-US"
        f"&user_is_login=1&is_new_user=0&region=US&lang={LANG}&pkg_type=release_version"
        f"&iid={INSTALL_ID}&device_id={DEVICE_ID}"
        f"&doubao_update_version_code=14080040&doubao_os_version={OS_VER}"
        f"&doubao_device_type={DEV_TYPE}&doubao_device_brand={DEV_BRAND}"
        f"&doubao_device_platform=android&region=US&flow_sdk_version=14080040"
    )
    BASE_PARAMS    = "flow_im_arch=v2&is_retry=0&" + _common
    BASE_URL       = "https://api16-normal-i18n-myb.dola.com/chat/completion"
    BASE_URL_IM    = "https://api16-normal-i18n-myb.dola.com/im/chain/cmd"
    BASE_PARAMS_IM = "flow_im_arch=v2&" + _common

    _odin_tt  = cfg.get("odin_tt", "")
    _d_ticket = cfg.get("d_ticket", "")
    _sid      = cfg.get("sessionid", "")
    _sid_guard = cfg.get("sid_guard", "")
    _store_idc = cfg.get("store-idc", cfg.get("store_idc", "mya"))

    HEADERS = {
        "Host":                    "api16-normal-i18n-myb.dola.com",
        "Connection":              "keep-alive",
        "Cookie": (
            f"store-idc={_store_idc}; store-country-code={CARRIER}; store-country-code-src=uid; "
            f"install_id={INSTALL_ID}; "
            "ttreq=1$993e412ea6d9e18bdd45df95c2f8a2892070234e; "
            f"odin_tt={_odin_tt}; "
            f"d_ticket={_d_ticket}; "
            f"sid_guard={_sid_guard}; "
            f"sessionid={_sid}; sessionid_ss={_sid}; sid_tt={_sid}"
        ),
        "X-OMNI-REQUEST":          "1",
        "sdk-version":             "2",
        "x-tt-passport-mfa-token": cfg.get("x_tt_passport_mfa_token", ""),
        "X-Tt-Token":              cfg.get("x_tt_token", ""),
        "x-tt-token-supplement":   cfg.get("x_tt_token_supplement", ""),
        "passport-sdk-settings":   "device_transfer_s_0,device_transfer_ab_0",
        "passport-sdk-version":    "60592",
        "Content-Type":            "application/json; encoding=utf-8",
        "x-tt-store-region":       CARRIER,
        "x-tt-store-region-src":   "uid",
        "X-SS-DP":                 "489823",
        "User-Agent": (
            f"com.larus.wolf/14080005 (Linux; U; Android {OS_VER}; {LANG}_US; {DEV_TYPE}; "
            "Build/UP1A.231005.007; Cronet/TTNetVersion:f5f9daf9 2026-08-06 "
            "QuicVersion:cad331fc 2026-06-29)"
        ),
        "ttzip-tlb":       "1",
        "Accept-Encoding": "gzip, deflate, br, ttzip",
    }


if _CFG.get("uid"):
    _init_globals(_CFG)


def _make_payload(text: str, conversation_id: str, last_message_index: int,
                  last_section_id: str, local_conv_id: str,
                  image_info: dict | None = None) -> str:
    now_ms = int(time.time() * 1000)
    unique_key = f"{UID}_{uuid.uuid4()}"

    has_image = image_info is not None
    send_scene = "album" if has_image else "keyboard"
    enter_method = "plus_panel" if has_image else ""

    if has_image:
        img_local_id = str(uuid.uuid4())
        txt_local_id = str(uuid.uuid4())
        messages = [
            {
                "content_block": [{
                    "append_fields": [],
                    "block_id": str(uuid.uuid4()),
                    "block_type": 10052,
                    "content": {"attachment_block": {"attachments": [{
                        "identifier": str(uuid.uuid4()),
                        "image": {
                            "image_ori": {
                                "height": image_info["height"],
                                "width":  image_info["width"],
                            },
                            "md5": image_info["md5"],
                            "uri": image_info["uri"],
                        },
                        "parse_state": 1,
                        "progress": 100,
                        "review_state": 1,
                        "type": 1,
                        "upload_status": 1,
                    }]}},
                    "is_finish": False,
                    "meta_info": [],
                    "parent_id": "",
                }],
                "local_message_id": img_local_id,
                "message_specific_ext": {"before_content_type": 800, "send_message_scene": "album"},
                "message_status": 0,
            },
            {
                "content_block": [{
                    "append_fields": [],
                    "block_id": str(uuid.uuid4()),
                    "block_type": 10000,
                    "content": {"text_block": {"text": text, "text_block_scene": 0}},
                    "is_finish": False,
                    "meta_info": [],
                    "parent_id": "",
                }],
                "local_message_id": txt_local_id,
                "message_specific_ext": {"before_content_type": 1, "send_message_scene": "keyboard"},
                "message_status": 0,
            },
        ]
    else:
        messages = [{
            "content_block": [{
                "append_fields": [],
                "block_id": str(uuid.uuid4()),
                "block_type": 10000,
                "content": {"text_block": {"text": text, "text_block_scene": 0}},
                "is_finish": False,
                "meta_info": [],
                "parent_id": "",
            }],
            "local_message_id": str(uuid.uuid4()),
            "message_specific_ext": {"before_content_type": 1, "send_message_scene": "keyboard"},
            "message_status": 0,
        }]

    ext = {
        "answer_with_suggest": "1",
        "commerce_credit_config_enable": "0",
        "content_source": "upload" if has_image else "",
        "create_time_ms": str(now_ms),
        "delay_request_interval_ms": "",
        "enter_method_trace": enter_method,
        "gen_music_create_type": "ai" if not has_image else "",
        "is_app_background": "0",
        "is_audio": "false",
        "is_douyin_installed": "0",
        "is_luna_installed": "0",
        "media_player_business_scene": "",
        "media_search_type": "0",
        "need_deep_think": "0",
        "previous_page_trace": "",
        "record_status": "1",
        "search_engine_type": "1",
        "send_message_scene": send_scene,
        "sub_conv_firstmet_type": "1",
        "sub_conv_source_message": "[]",
        "system_language": "es",
        "tts": "1",
        "voice_mix_input": "0",
        "wiki": "1",
    }
    if has_image:
        ext["vlm_da"] = json.dumps({"picture_num": 1})

    payload = {
        "client_meta": {
            "biz_type": "",
            "bot_id": BOT_ID,
            "conversation_id": conversation_id,
            "history_message_list": [],
            "last_message_index": last_message_index,
            "last_section_id": last_section_id,
            "local_conversation_id": local_conv_id,
            "local_onboarding_message_id": "",
            "local_permissions": [
                {"permission_name": "ACCESS_FINE_LOCATION",       "status": 2},
                {"permission_name": "ACCESS_COARSE_LOCATION",     "status": 2},
                {"permission_name": "ACCESS_BACKGROUND_LOCATION", "status": 2},
                {"permission_name": "RECORD_AUDIO",               "status": 2},
                {"permission_name": "BLUETOOTH",                  "status": 1},
                {"permission_name": "CAMERA",                     "status": 2},
                {"permission_name": "WRITE_CONTACTS",             "status": 2},
                {"permission_name": "CALENDAR",                   "status": 2},
            ],
            "scene_type": 0,
            "section_id": "",
        },
        "ext": ext,
        "messages": messages,
        "option": {
            "ab_launch_only": False,
            "agent_mode": 2,
            "aggregate_params": {"mode_id": "", "model_item_key": "0", "provider_id": "", "reasoning_effort": ""},
            "answer_with_suggest": True,
            "append_system_prompts": [],
            "banner_send_ext": {},
            "chat_entry_source": {"from_origin_message_id": "", "is_chat_flow_collapsed": False, "is_first_open_in_source_page": False, "source_type": 0},
            "click_clear_context": False,
            "collect_id": "",
            "connector_info_list": [],
            "conversation_init_ext": {"mode_id": "", "model_item_key": "0"} if not conversation_id else {},
            "conversation_init_option": {"independent_sites": [], "need_ack_conversation": True},
            "create_time_ms": now_ms,
            "disable_sse_cache": False,
            "dora_vision_info": "",
            "edit_query_id": [],
            "from_suggest": False,
            "history_messages": [],
            "is_audio": False,
            "is_from_click_option": False,
            "is_from_click_softlink": False,
            "is_regen": False,
            "is_replace": False,
            "lark_mention": False,
            "message_from": 0,
            "moa_model_name": "",
            "model_config": {"model_extra_params": {}, "model_item_key": "0"},
            "need_create_conversation": False,
            "need_deep_think": 0,
            "no_replace_for_regen": False,
            "permission_interact": 0,
            "prompt_modification": "",
            "regen_instruction": "",
            "regen_query_id": [],
            "related_deleted_message_ids": {},
            "resend_for_regen": False,
            "select_text_action": "",
            "send_message_scene": "keyboard",
            "shared_app_name": "",
            "sse_recv_event_options": {"support_chunk_delta": True},
            "start_seq": 0,
            "unique_key": unique_key,
            "user_ug_source_info": {},
        },
        "user_context": [],
    }
    return json.dumps(payload, ensure_ascii=False)


def _parse_sse_stream(response: requests.Response):
    event_type = None
    for raw_bytes in response.iter_lines():
        raw = raw_bytes.decode("utf-8") if isinstance(raw_bytes, bytes) else raw_bytes
        if raw.startswith("event:"):
            event_type = raw[len("event:"):].strip()
        elif raw.startswith("data:"):
            data_str = raw[len("data:"):].strip()
            if data_str and data_str != "{}":
                try:
                    yield event_type, json.loads(data_str)
                except json.JSONDecodeError:
                    pass
            event_type = None


def _extract_text_chunks(response: requests.Response):
    for event, data in _parse_sse_stream(response):
        if event == "STREAM_MSG_NOTIFY":
            blocks = data.get("content", {}).get("content_block", [])
            for b in blocks:
                t = b.get("content", {}).get("text_block", {}).get("text", "")
                if t:
                    yield t

        elif event == "STREAM_CHUNK":
            for op in data.get("patch_op", []):
                blocks = op.get("patch_value", {}).get("content_block", [])
                for b in blocks:
                    t = b.get("content", {}).get("text_block", {}).get("text", "")
                    if t:
                        yield t

        elif event == "SSE_ACK":
            ack = data.get("ack_client_meta", {})
            yield ("__ACK__", ack)


def _aws4_sign(method, host, path, query_params, headers_to_sign, body,
               access_key, secret_key, session_token, region, service, amz_date):
    date_stamp = amz_date[:8]

    canonical_querystring = "&".join(
        f"{k}={v}" for k, v in sorted(query_params.items())
    )
    canonical_headers = "".join(
        f"{k.lower()}:{v}\n" for k, v in sorted(headers_to_sign.items(), key=lambda x: x[0].lower())
    )
    signed_headers = ";".join(sorted(k.lower() for k in headers_to_sign))
    payload_hash = hashlib.sha256(body).hexdigest()

    canonical_request = "\n".join([
        method, path, canonical_querystring,
        canonical_headers, signed_headers, payload_hash,
    ])

    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode()).hexdigest(),
    ])

    def _hmac(key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    signing_key = _hmac(_hmac(_hmac(_hmac(
        f"AWS4{secret_key}".encode(), date_stamp), region), service), "aws4_request")
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    return (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope},"
        f"SignedHeaders={signed_headers},Signature={signature}"
    )


def upload_image(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    img_md5   = hashlib.md5(img_bytes).hexdigest()
    img_crc32 = format(zlib.crc32(img_bytes) & 0xFFFFFFFF, '08x')

    width, height = 0, 0
    try:
        from PIL import Image as _Img
        import io as _io
        with _Img.open(_io.BytesIO(img_bytes)) as im:
            width, height = im.size
    except Exception:
        pass

    now_ms = int(time.time() * 1000)
    base_params = (
        "device_platform=android&os=android&ssmix=a"
        f"&_rticket={now_ms}"
        "&cdid=ee3c4d85-c8f0-4c57-8027-1ec83293a5d5&channel=googleplay&aid=489823"
        "&app_name=nova_ai&version_code=14080001&version_name=14.8.0"
        "&manifest_version_code=14080005&update_version_code=14080040"
        "&resolution=1080*2186&dpi=420&device_type=SM-A525M&device_brand=samsung"
        "&language=es&os_api=34&os_version=14&ac=wifi"
        f"&uid={UID}&app_language=es&carrier_region=co&flow_app_variant=cici"
        "&sys_region=US&tz_name=America%2FBogota&system_language_detail=es-US"
        "&user_is_login=1&is_new_user=0&region=US&lang=es&pkg_type=release_version"
        "&iid=7681561912517068597&device_id=7681452747673093652"
        "&doubao_update_version_code=14080040&doubao_os_version=14"
        "&doubao_device_type=SM-A525M&doubao_device_brand=samsung"
        "&doubao_device_platform=android&region=US&flow_sdk_version=14080040"
    )
    prep = _signed_request("alice/resource/prepare_upload", base_params,
                           {"resource_type": 2, "scene_id": "5", "tenant_id": "3"})
    prep.raise_for_status()
    pdata       = prep.json()["data"]
    service_id  = pdata["service_id"]
    auth_token  = pdata["upload_auth_token"]

    sts_raw  = auth_token["session_token"]
    sts_data = json.loads(base64.b64decode(sts_raw[4:] + "=="))
    ak       = sts_data["AccessKeyId"]
    sk       = auth_token["secret_key"]

    now_dt   = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now_dt.strftime("%Y%m%dT%H%M%SZ")
    date_str = now_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

    apply_params = {
        "Action":          "ApplyImageUpload",
        "FileType":        "image",
        "Prefix":          "rc_vlm",
        "ServiceId":       service_id,
        "UploadNum":       "1",
        "Version":         "2018-08-01",
        "appid":           "489823",
        "device_platform": "android",
        "did":             "7681452747673093652",
        "region":          "US",
        "uid":             UID,
        "version_code":    "14080001",
    }
    apply_headers_to_sign = {
        "x-amz-date":           amz_date,
        "x-amz-security-token": sts_raw,
    }
    apply_auth = _aws4_sign(
        "GET", "api16-normal-i18n-myb.dola.com", "/top/v1",
        apply_params, apply_headers_to_sign, b"",
        ak, sk, sts_raw, "sdwdmwlll", "imagex", amz_date,
    )
    apply_resp = requests.get(
        "https://api16-normal-i18n-myb.dola.com/top/v1",
        params=apply_params,
        headers={
            "Authorization":        apply_auth,
            "Date":                 date_str,
            "User-Agent":           f"BDFileUpload({now_ms})",
            "X-Amz-Date":          amz_date,
            "X-Amz-Expires":       "31536000",
            "X-Amz-Security-Token": sts_raw,
            "accept-encoding":     "identity",
            "X-SS-DP":             "489823",
            "X-Neptune":           "-8|50:51:59:30:40:47:49:31:39",
        },
        timeout=30,
    )
    apply_resp.raise_for_status()
    store_infos  = apply_resp.json()["Result"]["UploadAddress"]["StoreInfos"]
    upload_hosts = apply_resp.json()["Result"]["UploadAddress"]["UploadHosts"]
    store      = store_infos[0]
    cdn_auth   = store["Auth"]
    oid_key    = store["StoreUri"]
    cdn_host   = upload_hosts[0]

    cdn_url = f"https://{cdn_host}/upload/v1/{oid_key}"
    now_dt2 = datetime.datetime.now(datetime.timezone.utc)
    cdn_resp = requests.post(
        cdn_url,
        data=img_bytes,
        headers={
            "Authorization":          cdn_auth,
            "Date":                   now_dt2.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "User-Agent":             f"BDFileUpload({int(time.time()*1000)})",
            "X-Upload-Content-CRC32": img_crc32,
            "accept-encoding":        "identity",
            "X-SS-DP":                "489823",
        },
        timeout=60,
    )
    cdn_resp.raise_for_status()
    cdn_json = cdn_resp.json()
    if cdn_json.get("code") != 2000:
        raise RuntimeError(f"CDN upload failed: {cdn_json}")

    img_identifier = str(uuid.uuid4())
    reg_body = gzip.compress(json.dumps({
        "extra": json.dumps({
            "bot_id": BOT_ID,
            "conversation_id": "",
            "device_id": "7681452747673093652",
            "local_message_id": str(uuid.uuid4()),
            "section_id": "",
        }),
        "resource_list": [{
            "meta": {"image_meta": {"data": {
                "md5": img_md5,
                "image_ori": {"width": width, "height": height},
                "local_res_path": f"/storage/emulated/0/DCIM/{os.path.basename(image_path)}",
                "identifier": img_identifier,
                "metadata": {"is_marked": "0"},
            }}},
            "resource_type": 2,
            "uri": oid_key,
        }],
        "scene_id": "5",
        "tenant_id": "3",
    }, ensure_ascii=False).encode())

    now_ms2   = int(time.time() * 1000)
    reg_params = base_params.replace(f"_rticket={now_ms}", f"_rticket={now_ms2}")
    reg_url   = f"https://api16-normal-i18n-myb.dola.com/alice/resource/register?{reg_params}"
    ts2       = now_ms2 // 1000
    sig2      = _sign_request(reg_url, timestamp=ts2)
    reg_resp  = requests.post(reg_url, data=reg_body, headers={
        **HEADERS,
        "X-SS-REQ-TICKET":       str(now_ms2),
        "X-Gorgon":              sig2["X-Gorgon"],
        "X-Khronos":             sig2["X-Khronos"],
        "X-Ladon":               sig2["X-Ladon"],
        "Content-Type":          "application/json; charset=UTF-8",
        "x-bd-content-encoding": "gzip",
    }, timeout=30)
    reg_resp.raise_for_status()
    reg_json = reg_resp.json()
    if reg_json.get("code") != 0:
        raise RuntimeError(f"register failed: {reg_json}")

    resource_id = reg_json["data"].get(oid_key, {}).get("resource_id", "")

    return {"uri": oid_key, "md5": img_md5, "width": width, "height": height,
            "resource_id": resource_id}


def _signed_request(path: str, base_params: str, payload: dict | str,
                    method: str = "POST") -> requests.Response:
    now_ms = int(time.time() * 1000)
    url = f"https://api16-normal-i18n-myb.dola.com/{path}?{base_params}&_rticket={now_ms}"
    ts  = now_ms // 1000
    sig = _sign_request(url, timestamp=ts)
    headers = {
        **HEADERS,
        "X-SS-REQ-TICKET": str(now_ms),
        "X-Gorgon":  sig["X-Gorgon"],
        "X-Khronos": sig["X-Khronos"],
        "X-Ladon":   sig["X-Ladon"],
    }
    body = (json.dumps(payload) if isinstance(payload, dict) else payload).encode("utf-8")
    return requests.request(method, url, data=body, headers=headers, timeout=30)


def delete_conversation(conversation_id: str, bot_id: str = BOT_ID) -> dict:
    seq = str(uuid.uuid4())
    payload = {
        "cmd": 1121,
        "sequence_id": seq,
        "uplink_body": {
            "delete_user_conv_uplink_body": {
                "bot_id": bot_id,
                "conversation_id": conversation_id,
                "conversation_type": 3,
                "mode": 2,
            }
        },
        "version": "1",
    }
    resp = _signed_request("im/chain/cmd", BASE_PARAMS_IM, payload)
    resp.raise_for_status()
    return resp.json()


def set_memory(enabled: bool, bot_id: str = BOT_ID) -> bool:
    payload = {"bot_id": bot_id, "bot_memory_switch_status": enabled}
    resp = _signed_request("alice/bot/update_bot", BASE_PARAMS, payload)
    resp.raise_for_status()
    return resp.json().get("code") == 0


CHATS_DIR = os.path.join(os.path.expanduser("~"), ".dola_chats")


def _chats_dir() -> str:
    os.makedirs(CHATS_DIR, exist_ok=True)
    return CHATS_DIR


def list_saved_chats() -> list[dict]:
    d = _chats_dir()
    chats = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        try:
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                meta = json.load(f)
            if "conversation_id" in meta:
                chats.append(meta)
        except Exception:
            pass
    return chats


def _chat_path(conversation_id: str) -> str:
    return os.path.join(_chats_dir(), f"{conversation_id}.json")


def _get_persistent_local_conv_id() -> str:
    path = os.path.join(_chats_dir(), "_identity.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)["local_conv_id"]
        except Exception:
            pass
    new_id = f"main_{uuid.uuid4()}_{BOT_ID}-local"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"local_conv_id": new_id}, f)
    return new_id


class DolaChat:
    def __init__(self, temporary: bool = False):
        self.conversation_id    = ""
        self.section_id         = ""
        self.last_message_index = 0
        self.local_conv_id      = _get_persistent_local_conv_id()
        self.temporary          = temporary
        self.title              = ""

    def save(self):
        if self.temporary or not self.conversation_id:
            return
        data = {
            "conversation_id":    self.conversation_id,
            "section_id":         self.section_id,
            "last_message_index": self.last_message_index,
            "local_conv_id":      self.local_conv_id,
            "title":              self.title,
            "saved_at":           int(time.time()),
        }
        with open(_chat_path(self.conversation_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, conversation_id: str) -> "DolaChat":
        path = _chat_path(conversation_id)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        chat = cls()
        chat.conversation_id    = data["conversation_id"]
        chat.section_id         = data["section_id"]
        chat.last_message_index = data["last_message_index"]
        chat.local_conv_id      = data["local_conv_id"]
        chat.title              = data.get("title", "")
        return chat

    def close(self):
        if self.temporary and self.conversation_id:
            try:
                delete_conversation(self.conversation_id)
            except Exception:
                pass

    def send(self, text: str, image_path: str | None = None,
             stream_print: bool = True) -> str:
        if not self.title:
            self.title = text[:80]

        image_info = None
        if image_path:
            if stream_print:
                print("uploading image...", flush=True)
            image_info = upload_image(image_path)
            if stream_print:
                print(f"uri: {image_info['uri']}", flush=True)

        now_ms = int(time.time() * 1000)
        url = f"{BASE_URL}?{BASE_PARAMS}&_rticket={now_ms}"
        ts  = int(now_ms / 1000)
        sig = _sign_request(url, timestamp=ts)

        headers = {
            **HEADERS,
            "X-SS-REQ-TICKET": str(now_ms),
            "X-Gorgon":  sig["X-Gorgon"],
            "X-Khronos": sig["X-Khronos"],
            "X-Ladon":   sig["X-Ladon"],
        }

        payload = _make_payload(
            text=text,
            conversation_id=self.conversation_id,
            last_message_index=self.last_message_index,
            last_section_id=self.section_id,
            local_conv_id=self.local_conv_id,
            image_info=image_info,
        )

        resp = requests.post(url, data=payload.encode("utf-8"), headers=headers, stream=True, timeout=60)
        resp.raise_for_status()

        full_text = ""
        for chunk in _extract_text_chunks(resp):
            if isinstance(chunk, tuple) and chunk[0] == "__ACK__":
                ack = chunk[1]
                if ack.get("conversation_id"):
                    self.conversation_id = ack["conversation_id"]
                if ack.get("section_id"):
                    self.section_id = ack["section_id"]
            else:
                full_text += chunk
                if stream_print:
                    print(chunk, end="", flush=True)

        if stream_print:
            print()

        self.last_message_index += 3 if image_info else 2
        self.save()
        return full_text


def _print_chat_list(chats: list[dict]):
    if not chats:
        print("  no saved chats")
        return
    for i, c in enumerate(chats, 1):
        ts  = datetime.datetime.fromtimestamp(c.get("saved_at", 0)).strftime("%Y-%m-%d %H:%M")
        tid = c["conversation_id"][-8:]
        print(f"  [{i}] {ts}  ...{tid}  {c.get('title','')[:60]}")


def _setup_session_from_file(path: str):
    from import_session import load_web_session
    cfg = load_web_session(path)
    if not cfg.get("sessionid"):
        print("no sessionid found in file")
        sys.exit(1)
    _init_globals(cfg)


def _prompt_session_setup():
    print("no session found. choose how to set it up:\n")
    print("  [1] extract from android device via adb (requires root + app logged in)")
    print("  [2] import from web browser cookies (dola.com)")
    print()
    try:
        choice = input("option [1/2]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

    if choice == "1":
        import subprocess as _sp
        _r = _sp.run([sys.executable, os.path.join(os.path.dirname(__file__), "extract_session.py")],
                     timeout=30)
        if _r.returncode != 0:
            sys.exit(1)
        cfg = _load_config()
        if not cfg.get("uid"):
            print("failed to extract session")
            sys.exit(1)
        _init_globals(cfg)

    elif choice == "2":
        print()
        print("  1. go to https://www.dola.com and log in")
        print("  2. install the 'Cookie-Editor' browser extension")
        print("  3. open it on the dola.com tab and export cookies")
        print("  4. save the file anywhere (json, header string or netscape format)")
        print()
        try:
            path = input("cookies file path: ").strip().strip('"')
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)
        if not os.path.exists(path):
            print(f"file not found: {path}")
            sys.exit(1)
        _setup_session_from_file(path)

    else:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        _setup_session_from_file(sys.argv[1])
    elif not _CFG.get("uid") and not _CFG.get("sessionid"):
        _prompt_session_setup()
    else:
        _init_globals(_CFG)

    chat = DolaChat()

    print("=== dola chat ===")
    print(f"session: {_CFG.get('name', UID)}  (uid {UID})")
    print("commands: /temp  /chats  /load <n|id>  /delete <n|id>  /session  /memory on|off  /img <path> [text]  exit\n")

    saved = list_saved_chats()
    if saved:
        print("saved chats:")
        _print_chat_list(saved)
        print()

    while True:
        try:
            user_input = input("you: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nexiting")
            chat.close()
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("exiting")
            chat.close()
            break

        if user_input == "/temp":
            if chat.temporary:
                print("already in temporary mode")
            else:
                chat = DolaChat(temporary=True)
                print("temporary mode on. chat will not be saved and will be deleted on exit")
            continue

        if user_input == "/chats":
            _print_chat_list(list_saved_chats())
            continue

        if user_input in ("/getsession", "/session"):
            import subprocess as _sp
            print("extracting session via adb...")
            _r = _sp.run([sys.executable, os.path.join(os.path.dirname(__file__), "extract_session.py")],
                         timeout=30)
            if _r.returncode != 0:
                print("failed to extract session")
                continue
            new_cfg = _load_config()
            if not new_cfg.get("uid"):
                print("failed to read session")
                continue
            old_uid = UID
            _init_globals(new_cfg)
            if old_uid and old_uid != UID:
                chat = DolaChat()
                print(f"account changed: {new_cfg.get('name', UID)}  (uid {UID})")
            else:
                print(f"credentials updated: {new_cfg.get('name', UID)}  (uid {UID})")
            continue

        if user_input in ("/memory on", "/memory off", "/memory"):
            if user_input == "/memory":
                print("usage: /memory on | /memory off")
                continue
            enable = user_input == "/memory on"
            try:
                ok = set_memory(enable)
                print(f"memory {'enabled' if enable else 'disabled'}" if ok else "failed to update memory")
            except Exception as e:
                print(f"error: {e}")
            continue

        if user_input.startswith("/delete ") or user_input == "/delete":
            arg = user_input[8:].strip() if user_input.startswith("/delete ") else ""
            if not arg:
                print("usage: /delete <n|id>")
                continue
            saved_now = list_saved_chats()
            target = None
            if arg.isdigit():
                idx = int(arg) - 1
                if 0 <= idx < len(saved_now):
                    target = saved_now[idx]["conversation_id"]
            else:
                for c in saved_now:
                    if c["conversation_id"].endswith(arg) or c["conversation_id"] == arg:
                        target = c["conversation_id"]
                        break
            if not target:
                print(f"chat not found: {arg}")
                continue
            try:
                delete_conversation(target)
            except Exception as e:
                print(f"error deleting from server: {e}")
            path = _chat_path(target)
            if os.path.exists(path):
                os.remove(path)
            if chat.conversation_id == target:
                chat = DolaChat()
            print("chat deleted")
            continue

        if user_input.startswith("/load "):
            arg = user_input[6:].strip()
            saved_now = list_saved_chats()
            target = None
            if arg.isdigit():
                idx = int(arg) - 1
                if 0 <= idx < len(saved_now):
                    target = saved_now[idx]["conversation_id"]
            else:
                for c in saved_now:
                    if c["conversation_id"].endswith(arg) or c["conversation_id"] == arg:
                        target = c["conversation_id"]
                        break
            if not target:
                print(f"chat not found: {arg}")
                continue
            chat.close()
            chat = DolaChat.load(target)
            print(f"chat loaded: {chat.title[:60]}")
            continue

        image_path = None
        if user_input.startswith("/img "):
            parts = user_input[5:].split(" ", 1)
            image_path = parts[0].strip()
            user_input  = parts[1].strip() if len(parts) > 1 else "describe this image"
            if not os.path.exists(image_path):
                print(f"file not found: {image_path}")
                continue

        print("dola: ", end="")
        chat.send(user_input, image_path=image_path, stream_print=True)
        print()
