"""
GCP OAuth authentication for Gemini API
Allows using GCP billing/credits instead of free tier
"""
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import Optional

# Scopes required for Gemini API
SCOPES = ['https://www.googleapis.com/auth/generative-language']


class GCPAuthManager:
    """Manages GCP OAuth authentication for Gemini API"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        project_id: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        """
        Initialize GCP auth manager

        Args:
            client_id: GCP OAuth client ID
            client_secret: GCP OAuth client secret
            project_id: GCP project ID (optional)
            token_path: Path to store token (defaults to ./gcp_token.json)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.project_id = project_id
        self.token_path = token_path or str(Path.cwd() / "gcp_token.json")
        self.credentials: Optional[Credentials] = None

    def get_credentials(self) -> Credentials:
        """
        Get valid OAuth credentials

        Returns:
            Valid OAuth credentials
        """
        # Try to load existing token
        if os.path.exists(self.token_path):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_path,
                    SCOPES
                )
            except Exception as e:
                print(f"Failed to load existing token: {e}")
                self.credentials = None

        # Refresh if expired
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self._save_credentials()
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                self.credentials = None

        # Run OAuth flow if no valid credentials
        if not self.credentials or not self.credentials.valid:
            self.credentials = self._run_oauth_flow()
            self._save_credentials()

        return self.credentials

    def _run_oauth_flow(self) -> Credentials:
        """
        Run OAuth flow to get new credentials

        Returns:
            New OAuth credentials
        """
        # Create OAuth config
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost:50000/"]
            }
        }

        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES
        )

        # Run local server flow
        print("\n" + "="*60)
        print("GCP OAuth Authentication Required")
        print("="*60)
        print("\nOpening browser for Google authentication...")
        print("Please sign in with your GCP account.\n")
        print("Using redirect URI: http://localhost:50000/")

        try:
            credentials = flow.run_local_server(
                port=50000,
                authorization_prompt_message="",
                success_message="Authentication successful! You can close this window.",
                open_browser=True
            )

            print("\n✓ Successfully authenticated with GCP!")
            print("="*60 + "\n")

            return credentials

        except Exception as e:
            print("\n" + "="*60)
            print("❌ OAuth Authentication Failed")
            print("="*60)
            print(f"\nError: {str(e)}\n")

            if "invalid" in str(e).lower() or "access_denied" in str(e).lower():
                print("This error usually means your OAuth Consent Screen is not configured.")
                print("\nPlease follow these steps:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials/consent")
                print("2. Configure OAuth Consent Screen (choose 'External')")
                print("3. Add your email as a test user")
                print("4. Add scope: https://www.googleapis.com/auth/generative-language")
                print("\nSee OAUTH_CONSENT_FIX.md for detailed instructions.")

            print("="*60 + "\n")
            raise

    def _save_credentials(self):
        """Save credentials to file"""
        if self.credentials:
            try:
                with open(self.token_path, 'w') as token_file:
                    token_file.write(self.credentials.to_json())
            except Exception as e:
                print(f"Warning: Failed to save credentials: {e}")

    def get_api_key(self) -> str:
        """
        Get API key from credentials (for compatibility)

        Returns:
            Access token to use as API key
        """
        creds = self.get_credentials()
        return creds.token


def get_authenticated_client(client_id: str, client_secret: str, project_id: Optional[str] = None):
    """
    Get authenticated Gemini client using GCP OAuth

    Args:
        client_id: GCP OAuth client ID
        client_secret: GCP OAuth client secret
        project_id: GCP project ID (optional)

    Returns:
        Authenticated genai.Client
    """
    from google import genai

    auth_manager = GCPAuthManager(client_id, client_secret, project_id)
    credentials = auth_manager.get_credentials()

    # Create client with OAuth credentials
    client = genai.Client(
        http_options={'credentials': credentials}
    )

    return client
