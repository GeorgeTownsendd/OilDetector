from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os
import csv
import os
import datetime
import io

import numpy as np
from PIL import Image
import geopandas as gpd
from shapely.geometry import Point, Polygon
import random

def load_ocean_outlines(filepath):
    """Loads ocean outlines from a GeoPackage file."""
    gdf = gpd.read_file(filepath, layer='goas_v01')
    return gdf


def generate_random_point_in_ocean(gdf):
    """Generates a random point within the ocean outlines."""
    valid_point = False
    while not valid_point:
        # Generate a random longitude and latitude
        lon = random.uniform(-180, 180)
        lat = random.uniform(-70, 70)
        point = Point(lon, lat)
        # Check if the point is within any of the ocean polygons
        if any(gdf.contains(point)):
            valid_point = True
    print(lon, lat)
    return lon, lat



def create_ocean_dataset(n, output_folder, gdf_filename='data/inputs/oceans.gpkg'):
    """Creates a dataset of n random ocean points, downloads Sentinel images,
    and records the points in a CSV file.
    """

    if not output_folder.startswith('data/'):
        output_folder = 'data/datasets/' + output_folder

    gdf = gpd.read_file(gdf_filename, layer='oceans')

    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define the path for the CSV file to record the points
    csv_file_path = os.path.join(output_folder, 'ocean_points.csv')

    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Number', 'Latitude', 'Longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for i in range(n):
            lon, lat = generate_random_point_in_ocean(gdf)
            # Record the generated point in the CSV file
            writer.writerow({'Number': i + 1, 'Latitude': lat, 'Longitude': lon})

            # Define your time range and other parameters as needed
            start_date = datetime.date(2023, 1, 1)  # Example start date
            end_date = datetime.date(2023, 1, 31)  # Example end date
            output_filename = os.path.join(output_folder, f"ocean_point_{i + 1}.jpg")
            # Download the image for the generated point
            download_image(lat, lon, start_date, end_date, output_filename=output_filename)
            print(f"Downloaded {i + 1}/{n} images.")

    print(f"Completed downloading images and recording points in {csv_file_path}.")


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



def download_image(
    lat,
    lon,
    start_date,
    end_date,
    credentials_path='data/credentials.txt',
    instance_id='7155b573-d6a9-4712-be56-b4b3e34c5706',
    layer_name='NDVI',
    image_format='image/jpeg',
    resolution=(512, 512),
    buffer=0.1,
):
    """Downloads a Sentinel image for the given coordinates and time range and returns it as a NumPy array.

    Args:
        lat (float): Latitude of the image center.
        lon (float): Longitude of the image center.
        start_date (datetime.date): Start date of the desired time range.
        end_date (datetime.date): End date of the desired time range.
        credentials_path (str, optional): Path to the credentials file. Defaults to 'data/credentials.txt'.
        instance_id (str, optional): Sentinel Hub instance ID.
        layer_name (str, optional): The layer to download.
        image_format (str, optional): Format of the output image.
        resolution (tuple, optional): Image resolution in pixels (width, height).
        buffer (float, optional): Buffer size to add around the center coordinates.

    Returns:
        np.array: The image as a NumPy array.
    """

    bbox = (lon - buffer, lat - buffer, lon + buffer, lat + buffer)
    client_id, client_secret = read_client_credentials(credentials_path)
    oauth = create_oauth_session(client_id, client_secret)

    start_time = start_date.strftime('%Y-%m-%d')
    end_time = end_date.strftime('%Y-%m-%d')

    wms_url = f"https://services-uswest2.sentinel-hub.com/ogc/wms/{instance_id}?service=WMS&request=GetMap&layers={layer_name}&styles=&format={image_format}&transparent=false&version=1.1.1&width={resolution[0]}&height={resolution[1]}&srs=EPSG:4326&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&time={start_time}/{end_time}"

    response = oauth.get(wms_url)

    if response.status_code == 200:
        image_data = io.BytesIO(response.content)
        image = Image.open(image_data)
        image_array = np.array(image)
        return image_array
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}, Response content: {response.text}")




def process_incidents_and_download(csv_file, output_folder, max_downloads=100, dataset_name='default', layer_name='TRUE-COLOR'):
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
                open_date = datetime.datetime.strptime(open_date_str, '%Y/%m/%d').date()
                start_of_month = open_date.replace(day=1)
                end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

                folder_path = f'data/datasets/{dataset_name}/'
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)

                fn = folder_path + f'id - {row["id"]} - v1.jpg'
                image = download_image(lat, lon, start_date=start_of_month, end_date=end_of_month, layer_name=layer_name)

                pil_image = Image.fromarray(image)
                pil_image.save(fn)

                print(f"Downloaded image for row: {row['ID']}")

                downloads += 1

            except ZeroDivisionError:#ValueError:
                print(f"Error parsing date for row: {row['ID']}")


if __name__ == '__main__':
    #create_ocean_dataset(100, 'set4-baseline')
    csv_file = 'data/inputs/filtered_incidents.csv'
    output_folder = 'downloaded_images'

    layer_names = ['TRUE-COLOR', 'NDVI', 'NDWI', 'THERMAL']

    process_incidents_and_download(csv_file, output_folder, dataset_name='ndvi', max_downloads=10, layer_name=layer_names[3])