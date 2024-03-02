from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os


def read_client_credentials(filepath):
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


def download_image(lat, lon, credentials_path='data/credentials.txt', instance_id='7155b573-d6a9-4712-be56-b4b3e34c5706', layer_name='TRUE-COLOR', image_format='image/jpeg', resolution=(512, 512), buffer=0.01):
    """Downloads an image for a given latitude and longitude."""
    bbox = (lon - buffer, lat - buffer, lon + buffer, lat + buffer)  # (minLon, minLat, maxLon, maxLat)
    client_id, client_secret = read_client_credentials(credentials_path)
    oauth = create_oauth_session(client_id, client_secret)

    start_time = '2023-01-01'
    end_time = '2023-01-31'

    wms_url = f"https://services-uswest2.sentinel-hub.com/ogc/wms/{instance_id}?service=WMS&request=GetMap&layers={layer_name}&styles=&format={image_format}&transparent=false&version=1.1.1&width={resolution[0]}&height={resolution[1]}&srs=EPSG:4326&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&time={start_time}/{end_time}"
    response = oauth.get(wms_url)

    if response.status_code == 200:
        image_path = 'downloaded_image.jpg'
        with open(image_path, 'wb') as f:
            f.write(response.content)
        print("Image downloaded successfully to:", image_path)
    else:
        print(f"Failed to download image. Status code: {response.status_code}")
        print(f"Request URL: {wms_url}")
        print(f"Response content: {response.text}")


lat, lon = 46.16, -1.15
download_image(lat, lon)
