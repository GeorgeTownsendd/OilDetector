from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os
import csv
import os
import datetime


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


import datetime

def download_image(
    lat,
    lon,
    start_date,
    end_date,
    output_filename='downloaded_image.jpg',  # Change from image_path
    credentials_path='data/credentials.txt',
    instance_id='7155b573-d6a9-4712-be56-b4b3e34c5706',
    layer_name='TRUE-COLOR',
    image_format='image/jpeg',
    resolution=(512, 512),
    buffer=0.1,
):
    """Downloads a Sentinel image for the given coordinates and time range.

    Args:
        lat (float): Latitude of the image center.
        lon (float): Longitude of the image center.
        start_date (datetime.date): Start date of the desired time range.
        end_date (datetime.date): End date of the desired time range.
        output_filename (str, optional): Name of the output image file. Defaults to 'downloaded_image.jpg'.
        credentials_path (str, optional): Path to the credentials file. Defaults to 'data/credentials.txt'.
        instance_id (str, optional): Sentinel Hub instance ID.
        layer_name (str, optional): The layer to download.
        image_format (str, optional): Format of the output image.
        resolution (tuple, optional): Image resolution in pixels (width, height).
        buffer (float, optional): Buffer size to add around the center coordinates.
    """

    bbox = (lon - buffer, lat - buffer, lon + buffer, lat + buffer)
    client_id, client_secret = read_client_credentials(credentials_path)
    oauth = create_oauth_session(client_id, client_secret)

    start_time = start_date.strftime('%Y-%m-%d')
    end_time = end_date.strftime('%Y-%m-%d')

    wms_url = f"https://services-uswest2.sentinel-hub.com/ogc/wms/{instance_id}?service=WMS&request=GetMap&layers={layer_name}&styles=&format={image_format}&transparent=false&version=1.1.1&width={resolution[0]}&height={resolution[1]}&srs=EPSG:4326&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&time={start_time}/{end_time}"

    response = oauth.get(wms_url)

    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"Image downloaded successfully to: {output_filename}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")
        print(f"Request URL: {wms_url}")
        print(f"Response content: {response.text}")


def process_incidents_and_download(csv_file, output_folder, max_downloads=100):
    """Processes incidents from a CSV file and downloads images."""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # Create output folder if it doesn't exist

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        downloads = 0

        for row in reader:
            if downloads >= max_downloads:
                break

            open_date_str = row['open_date']
            lat = float(row['lat'])
            lon = float(row['lon'])

            try:
                open_date = datetime.datetime.strptime(open_date_str, '%Y-%m-%d').date()
                start_of_month = open_date.replace(day=1)
                end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

                download_image(lat, lon, start_date=start_of_month, end_date=end_of_month, output_filename=f"data/set2/id-{row['id']}-v1.jpg")
                downloads += 1

            except ValueError:
                print(f"Error parsing date for row: {row}")

if __name__ == '__main__':
    csv_file = 'data/filtered_incidents.csv'
    output_folder = 'downloaded_images'
    process_incidents_and_download(csv_file, output_folder)