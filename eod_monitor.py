#!/usr/bin/env python3
"""
EOD Monitor - Polls Google Drive for new End-of-Day reports
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
import httpx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EODMonitor:
    """Monitor Google Drive folder for new EOD documents"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.drive_service = self._init_drive_service()
        self.state_file = Path(self.config['monitor']['state_file'])
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
            
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def _init_drive_service(self):
        """Initialize Google Drive API service"""
        creds_path = self.config['google_drive']['credentials_path']
        scopes = self.config['google_drive']['scopes']
        
        if not Path(creds_path).exists():
            logger.error(f"Credentials file not found: {creds_path}")
            sys.exit(1)
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=scopes
        )
        
        return build('drive', 'v3', credentials=credentials)
    
    def _load_state(self) -> Dict:
        """Load last check state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "last_check": None,
            "processed_files": []
        }
    
    def _save_state(self, state: Dict):
        """Save check state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def check_for_new_documents(self) -> List[Dict]:
        """Check Google Drive folder for new/updated documents"""
        folder_id = self.config['google_drive']['folder_id']
        state = self._load_state()
        
        try:
            # Query for files in the EOD folder
            query = f"'{folder_id}' in parents and trashed = false"
            
            if state.get('last_check'):
                # Only get files modified after last check
                query += f" and modifiedTime > '{state['last_check']}'"
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            # Filter out already processed files
            new_files = [
                f for f in files 
                if f['id'] not in state.get('processed_files', [])
            ]
            
            logger.info(f"Found {len(new_files)} new document(s)")
            
            return new_files
            
        except HttpError as error:
            logger.error(f"Drive API error: {error}")
            return []
    
    def trigger_webhook(self, document: Dict) -> bool:
        """Trigger FastAPI webhook for new document"""
        webhook_url = self.config['webhook']['url']
        timeout = self.config['webhook']['timeout']
        
        payload = {
            "event": "new_eod_document",
            "document": {
                "id": document['id'],
                "name": document['name'],
                "mimeType": document['mimeType'],
                "modifiedTime": document['modifiedTime'],
                "webViewLink": document.get('webViewLink')
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = httpx.post(
                webhook_url,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            logger.info(f"Webhook triggered successfully for: {document['name']}")
            return True
            
        except httpx.HTTPError as error:
            logger.error(f"Webhook failed: {error}")
            return False
    
    def run(self, test_mode: bool = False):
        """Run the monitor check"""
        logger.info("Starting EOD monitor check...")
        
        new_documents = self.check_for_new_documents()
        
        if not new_documents:
            logger.info("No new documents found")
            return
        
        state = self._load_state()
        processed_files = state.get('processed_files', [])
        
        for doc in new_documents:
            logger.info(f"Processing: {doc['name']} (ID: {doc['id']})")
            
            if test_mode:
                logger.info("[TEST MODE] Would trigger webhook")
            else:
                if self.trigger_webhook(doc):
                    processed_files.append(doc['id'])
        
        # Update state
        state['last_check'] = datetime.utcnow().isoformat() + 'Z'
        state['processed_files'] = processed_files[-1000:]  # Keep last 1000
        self._save_state(state)
        
        logger.info("EOD monitor check completed")


def main():
    parser = argparse.ArgumentParser(description='EOD Monitor')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (no webhook triggers)'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to config file'
    )
    
    args = parser.parse_args()
    
    monitor = EODMonitor(config_path=args.config)
    monitor.run(test_mode=args.test)


if __name__ == '__main__':
    main()
