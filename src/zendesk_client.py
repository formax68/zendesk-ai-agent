import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class ZendeskClient:
    def __init__(self):
        subdomain = os.getenv("ZENDESK_SUBDOMAIN")
        email = os.getenv("ZENDESK_EMAIL")
        token = os.getenv("ZENDESK_API_TOKEN")
        if not all([subdomain, email, token]):
            raise ValueError("Missing Zendesk credentials in environment variables.")
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(f"{email}/token", token)
        self.session.headers.update({"Content-Type": "application/json"})

    def get_tickets(self, status=None):
        """Fetch tickets from Zendesk API. Optionally filter by status."""
        url = f"{self.base_url}/tickets.json"
        params = {}
        if status:
            params["status"] = status
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get("tickets", [])

    def get_ticket_comments(self, ticket_id):
        """Fetch comments for a specific ticket."""
        url = f"{self.base_url}/tickets/{ticket_id}/comments.json"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("comments", [])
