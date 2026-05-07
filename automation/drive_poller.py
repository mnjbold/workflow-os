"""
Google Drive EOD Folder Poller
Replaces Apps Script — runs via OpenClaw cron every 15 minutes.
Uses Google Workspace CLI / Drive API to detect new/updated EOD docs.

Auth: gcloud application-default credentials OR GOOGLE_API_KEY env var
Setup: run `gcloud auth application-default login` once to authenticate.
"""
import os
import json
import hashlib
import requests
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path

FOLDER_ID = "1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM"
WEBHOOK_URL = os.getenv("WORKFLOW_OS_WEBHOOK_URL", "http://localhost:8000/webhook/eod")
STATE_FILE = Path.home() / ".openclaw" / "workflow-os-poller-state.json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def get_access_token() -> str:
    """Get OAuth token via gcloud ADC."""
    import subprocess
    result = subprocess.run(
        ["/data/google-cloud-sdk/bin/gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    raise RuntimeError(f"gcloud auth failed: {result.stderr}")

def list_recent_docs(since_minutes: int = 20) -> list[dict]:
    """List docs in EOD folder modified in the last N minutes."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()
    params = {
        "q": f"'{FOLDER_ID}' in parents and modifiedTime > '{cutoff}' and mimeType = 'application/vnd.google-apps.document'",
        "fields": "files(id,name,modifiedTime,webViewLink)",
        "orderBy": "modifiedTime desc",
    }
    headers = {}
    if GOOGLE_API_KEY:
        params["key"] = GOOGLE_API_KEY
    else:
        params["access_token"] = get_access_token()

    resp = httpx.get("https://www.googleapis.com/drive/v3/files", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json().get("files", [])

def get_doc_content(doc_id: str) -> str:
    """Export Google Doc as plain text."""
    params = {"mimeType": "text/plain"}
    if GOOGLE_API_KEY:
        params["key"] = GOOGLE_API_KEY
    else:
        params["access_token"] = get_access_token()
    resp = httpx.get(f"https://www.googleapis.com/drive/v3/files/{doc_id}/export", params=params)
    resp.raise_for_status()
    return resp.text

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"processed": {}}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def doc_fingerprint(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def send_to_webhook(doc_id: str, doc_name: str, content: str):
    payload = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "folder_id": FOLDER_ID,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "drive_poller"
    }
    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=30)
    resp.raise_for_status()
    print(f"  ✅ Sent to webhook: {resp.status_code}")
    return resp.json()

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling Drive folder {FOLDER_ID}...")
    state = load_state()
    docs = list_recent_docs(since_minutes=20)

    if not docs:
        print("  No recent docs found.")
        return

    for doc in docs:
        doc_id = doc["id"]
        doc_name = doc["name"]
        print(f"  Found: {doc_name} (modified: {doc['modifiedTime']})")

        try:
            content = get_doc_content(doc_id)
            fingerprint = doc_fingerprint(content)

            # Skip if already processed with same content
            if state["processed"].get(doc_id) == fingerprint:
                print(f"  ⏭️  No change since last poll, skipping.")
                continue

            print(f"  📤 New/updated content detected, sending to webhook...")
            send_to_webhook(doc_id, doc_name, content)
            state["processed"][doc_id] = fingerprint
            save_state(state)

        except Exception as e:
            print(f"  ❌ Error processing {doc_name}: {e}")

    print("Done.")

if __name__ == "__main__":
    main()
