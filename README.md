# dola-client

Unofficial Python implementation of the [Dola AI](https://dola.com) API

This project targets the Android app API, it was easier to capture and reverse from the phone traffic than from the web client. That said, web browser cookies also work and are supported as an alternative session source.

The CLI client (`dola_client.py`) is just a usage example. The signing logic and API calls can be reused for whatever you want, bots, automation, integrations, etc.

## Requirements

- Python 3.11+
- `pip install requests pillow`

## Setup

### Option A: Android device (recommended, full session)

Requires a rooted device or emulator with the Dola app installed and logged in, and ADB in PATH.

```bash
python extract_session.py
```

This reads session tokens directly from the app's shared preferences via root and writes them to `config.json`

### Option B: Web browser cookies

1. Go to [https://www.dola.com](https://www.dola.com) and log in
2. Install the [Cookie-Editor](https://cookie-editor.com) browser extension
3. Open it on the dola.com tab and export cookies
4. Save the file (JSON, header string, or Netscape format are all supported)

```bash
python dola_client.py path/to/cookies.json
```

Or just run `python dola_client.py` and follow the prompts.


### Start the client

```bash
python dola_client.py
```

If no session is found, the client will ask whether to extract via ADB or import from a browser cookies file.

## Commands

| Command | Description |
|---|---|
| `exit` | Exit the client |
| `/temp` | Enable temporary mode, chat is not saved and is deleted from the server on exit |
| `/chats` | List saved chats |
| `/load <n\|id>` | Load a saved chat by index or ID suffix |
| `/delete <n\|id>` | Delete a chat from the server and local storage |
| `/session` | Re-extract session from ADB (updates credentials or switches account) |
| `/memory on\|off` | Enable or disable the bot's memory feature |
| `/img <path> [text]` | Send an image with optional text |

## Notes

- Chats are saved locally in `~/.dola_chats/` as JSON files.
- The local conversation ID is persistent per installation (stored in `~/.dola_chats/_identity.json`).

