import gspread
import pandas as pd
import os
import base64
import json
from datetime import datetime
import uuid

class GoogleSheetsHandler:
    """
    Handles all interactions with Google Sheets for logging queries.
    This version includes detailed error handling to help diagnose connection issues.
    """
    def __init__(self):
        self.client = self._get_client()
        if self.client:
            self.resolved_sheet = self._open_sheet("RESOLVED_SHEET_URL", "Resolved Queries")
            self.knowledge_gap_sheet = self._open_sheet("KNOWLEDGE_GAP_SHEET_URL", "Knowledge Gaps")
        else:
            # If client failed to initialize, set sheets to None
            self.resolved_sheet = None
            self.knowledge_gap_sheet = None

    def _get_client(self):
        """Authenticates with Google Sheets and returns a client object."""
        creds_base64 = os.getenv("GOOGLE_SHEETS_CREDENTIALS_BASE64")
        if not creds_base64:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_BASE64 environment variable not set.")
        
        try:
            creds_json_str = base64.b64decode(creds_base64).decode('utf-8')
            creds_json = json.loads(creds_json_str)
            
            # Extract the service account email for clear error messages
            self.service_account_email = creds_json.get("client_email")

            # Define the necessary scopes
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            return gspread.service_account_from_dict(creds_json, scopes=scopes)
        
        except (json.JSONDecodeError, base64.binascii.Error):
            raise ValueError("Failed to decode GOOGLE_SHEETS_CREDENTIALS_BASE64. Please ensure it's a valid base64-encoded string from your credentials.json file.")
        except Exception as e:
            # Catch any other unexpected errors during client initialization
            raise ValueError(f"An unexpected error occurred during Google Sheets client initialization: {e}")

    def _open_sheet(self, url_env_var, sheet_name_for_logs):
        """Opens a specific sheet by URL and returns the worksheet object."""
        sheet_url = os.getenv(url_env_var)
        if not sheet_url:
            print(f"Warning: {url_env_var} is not set in the .env file. Logging for '{sheet_name_for_logs}' will be disabled.")
            return None

        try:
            spreadsheet = self.client.open_by_url(sheet_url)
            return spreadsheet.sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"ERROR opening '{sheet_name_for_logs}': The Google Sheet was not found at the provided URL. Please double-check the URL in your .env file for {url_env_var}.")
            return None
        except gspread.exceptions.APIError as e:
            # This is often a permissions error
            error_details = e.response.json()
            if error_details.get("error", {}).get("status") == "PERMISSION_DENIED":
                print(f"ERROR opening '{sheet_name_for_logs}': Permission denied. Please ensure you have SHARED the Google Sheet with the service account email: {self.service_account_email}")
            else:
                print(f"An API error occurred while trying to open '{sheet_name_for_logs}': {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while opening the '{sheet_name_for_logs}' sheet: {e}")
            return None

    def _ensure_headers(self, sheet, headers):
        """Checks if headers are present and adds them if not."""
        if not sheet: return
        try:
            # Check if the first row is empty or doesn't match headers
            if not sheet.row_values(1):
                sheet.append_row(headers)
        except gspread.exceptions.APIError:
            # Handle cases where the sheet might be protected or have other issues
            pass

    def log_resolved_query(self, query, context, response):
        """Logs a resolved query to the 'Resolved' sheet."""
        if not self.resolved_sheet:
            print("Cannot log resolved query, client not initialized.")
            return
        
        headers = ["ID", "Timestamp", "Query", "Retrieved Context", "Generated Response", "Status"]
        self._ensure_headers(self.resolved_sheet, headers)
        
        log_entry = [
            str(uuid.uuid4()),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query,
            context,
            response,
            "Resolved"
        ]
        try:
            self.resolved_sheet.append_row(log_entry)
        except gspread.exceptions.APIError as e:
            error_details = e.response.json()
            if error_details.get("error", {}).get("status") == "PERMISSION_DENIED":
                print(f"ERROR writing to 'Resolved Queries' sheet: Permission denied. Please ensure you have SHARED the Google Sheet with the service account email: '{self.service_account_email}' and given it EDITOR permissions.")
            else:
                print(f"An API error occurred while writing to the 'Resolved Queries' sheet: {e}")


    def log_knowledge_gap(self, query, response):
        """Logs an unresolved query to the 'Knowledge Gap' sheet."""
        if not self.knowledge_gap_sheet:
            print("Cannot log knowledge gap, client not initialized.")
            return
            
        headers = ["ID", "Timestamp", "Query", "Generated Response", "Status"]
        self._ensure_headers(self.knowledge_gap_sheet, headers)
        
        log_entry = [
            str(uuid.uuid4()),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query,
            response,
            "Knowledge Gap"
        ]
        try:
            self.knowledge_gap_sheet.append_row(log_entry)
        except gspread.exceptions.APIError as e:
            error_details = e.response.json()
            if error_details.get("error", {}).get("status") == "PERMISSION_DENIED":
                print(f"ERROR writing to 'Knowledge Gaps' sheet: Permission denied. Please ensure you have SHARED the Google Sheet with the service account email: '{self.service_account_email}' and given it EDITOR permissions.")
            else:
                print(f"An API error occurred while writing to the 'Knowledge Gaps' sheet: {e}")

    def get_all_data(self, sheet_type):
        """Fetches all data from the specified sheet as a DataFrame."""
        sheet = self.resolved_sheet if sheet_type == 'resolved' else self.knowledge_gap_sheet
        if not sheet:
            return pd.DataFrame()
        try:
            return pd.DataFrame(sheet.get_all_records())
        except Exception:
            return pd.DataFrame()

