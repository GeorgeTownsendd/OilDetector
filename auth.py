from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

CREDENTIALS_PATH = 'data/credentials.txt'


def read_client_credentials(filepath='data/credentials'):
    """Reads client ID and secret from a specified file."""
    with open(filepath, 'r') as file:
        client_id = file.readline().strip()
        client_secret = file.readline().strip()
    return client_id, client_secret


def create_oauth_session(client_id, client_secret):
    """Creates an OAuth2 session for authentication."""
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.fetch_token(
        token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
        client_id=client_id, client_secret=client_secret, include_client_id=True)
    return oauth


