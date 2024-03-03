import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import random
import datetime
from datetime import timedelta, timedelta
import requests
from shapely.geometry import Point, Polygon
from rasterio.io import MemoryFile
import json
import numpy as np

from auth import *


client_id, client_secret = read_client_credentials(CREDENTIALS_PATH)
AUTH_TOKEN = create_oauth_session(client_id, client_secret).token['access_token']
ENDPOINT_URL = 'https://creodias.sentinel-hub.com/api/v1/catalog/1.0.0/search'


def search_imagery(lat, lon, datetime, collections=["sentinel-3-olci"], limit=5):
    """
    Searches for imagery of a point within +- a week of a given time using Sentinel Hub Catalog API.

    Args:
        lat (float): Latitude of the point.
        lon (float): Longitude of the point.
        datetime_obj (datetime.datetime): Datetime object for the given time.
        collections (list): List of collections to search within. Default is ["sentinel-1-grd"].
        limit (int): Number of search results to return. Default is 5.
        auth_token (str): Authentication token for Sentinel Hub services.

    Returns:
        dict: The search results.
    """

    # Calculate the date range of +-1 week from the given datetime
    start_date = (datetime - timedelta(weeks=1)).isoformat() + "Z"
    end_date = (datetime + timedelta(weeks=1)).isoformat() + "Z"

    # Construct the search payload
    data = {
        "bbox": [lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1],
        "datetime": f"{start_date}/{end_date}",
        "collections": collections,
        "limit": limit,
        "filter-lang": "cql2-json"
    }

    # Headers including the updated Accept header and Authorization
    headers = {
        "Accept": "application/geo+json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    response = requests.post(ENDPOINT_URL, json=data, headers=headers)

    # Check for successful response before returning data
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to search imagery. Status code: {response.status_code}, Response content: {response.text}")


def download_image(lat, lon, date_time=datetime.datetime.now(), bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07']):
    """
    Downloads imagery for a specific location, date, and bands using Sentinel Hub Process API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        date_time (datetime.datetime): The date and time for the imagery.
        bands (list): List of spectral bands to download.

    Returns:
        Response content: Image data or error message.
    """
    # Format date_time to ISO format
    date_start = (date_time - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    date_end = date_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    buffer = 0.01
    bbox = [lon - buffer, lat - buffer, lon + buffer, lat + buffer]

    # Setup API request payload
    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {
                    "datetime": date_start
                }
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": date_start,
                        "to": date_end
                    }
                }
            }]
        },
        "evalscript": f"""
        //VERSION=3
        function setup() {{
          return {{
            input: {json.dumps(bands)},
            output: {{
              bands: {len(bands)},
              format: "image/png"
            }}
          }};
        }}
        function evaluatePixel(sample) {{
          return [{', '.join([f'sample.{band}' for band in bands])}];
        }}
        """
    }

    # Set headers
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    # Perform the API request
    response = requests.post('https://services.sentinel-hub.com/api/v1/process', json=payload, headers=headers)

    if response.status_code == 200:
        with MemoryFile(response.content) as memfile:
            with memfile.open() as dataset:
                image_array = dataset.read()
        return image_array
    else:
        raise Exception(
            f"Failed to download imagery. Status code: {response.status_code}, Response content: {response.text}")



# download_image(lat, lon, datetime_obj, bands=['B02', 'B03', 'B04'], access_token='your_access_token')


def test(
    lat,
    lon,
    start_date='default',
    end_date='default',
    credentials_path='data/credentials.txt',
    instance_id='7155b573-d6a9-4712-be56-b4b3e34c5706',
    layer_name='NDVI',
    image_format='image/tiff',
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

    if start_date == 'default':
        start_time = datetime.datetime.now()
    else:
        start_time = start_date.strftime('%Y-%m-%d')
    if end_date == 'default':
        end_time = datetime.datetime.now() - datetime.timedelta(weeks=1)
    else:
        end_time = end_date.strftime('%Y-%m-%d')

    wms_url = f"https://services-uswest2.sentinel-hub.com/ogc/wms/{instance_id}?service=WMS&request=GetMap&layers={layer_name}&styles=&format={image_format}&transparent=false&version=1.1.1&width={resolution[0]}&height={resolution[1]}&srs=EPSG:4326&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&time={start_time}/{end_time}"

    response = oauth.get(wms_url)

    if response.status_code == 200:
        with MemoryFile(response.content) as memfile:
            with memfile.open() as dataset:
                image_array = dataset.read()

        return image_array
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}, Response content: {response.text}")


def create_ocean_dataset_from_incidents(n, output_folder, incidents_csv='data/inputs/filtered_incidents.csv',
                                        credentials_path='data/credentials.txt'):
    """Creates a dataset of n random ocean points from incident data, downloads Sentinel images for these points ensuring the date is more than a year different from the 'open_date',
    and records the points in a CSV file.
    Args:
        n (int): Number of points to generate.
        output_folder (str): Folder to store the downloaded images and CSV.
        incidents_csv (str): Path to the incidents CSV file.
        credentials_path (str): Path to the OAuth credentials file.
    """
    # Ensure the output folder exists
    if not output_folder.startswith('data/'):
        output_folder = 'data/datasets/' + output_folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Read incident data
    incidents_df = pd.read_csv(incidents_csv)
    incidents_df['open_date'] = pd.to_datetime(incidents_df['open_date'])

    # Define the path for the CSV file to record the points
    csv_file_path = os.path.join(output_folder, 'ocean_points.csv')
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Number', 'Latitude', 'Longitude', 'Date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in incidents_df.iterrows():
            if index >= n:  # Limit to n incidents
                break

            lat, lon = row['lat'], row['lon']
            open_date = row['open_date']

            # Ensure the date is more than a year different from 'open_date'
            start_date = (open_date + pd.DateOffset(years=1))
            end_date = (start_date + datetime.timedelta(days=30)) # Example range of 30 days

            output_filename = os.path.join(output_folder, f"incident_{index + 1}.jpg")

            try:
                # Download the image for the generated point
                download_image(lat, lon, start_date, end_date, credentials_path=credentials_path)
                writer.writerow({'Number': index + 1, 'Latitude': lat, 'Longitude': lon, 'Date': start_date})
                print(f"Downloaded {index + 1}/{n} images.")
            except ZeroDivisionError:#Exception as e:
                print(f"Failed to download image for incident {index + 1}: {e}")

    print(f"Completed downloading images and recording points in {csv_file_path}.")



def get_row_details(row_id, csv_file='data/inputs/filtered_incidents.csv'):
    """Retrieve details for a given row ID from the CSV file."""
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row['id']) == int(row_id):  # Assuming the row ID column is named 'id'
                return row
    return None


def download_image_for_row_id(row_id, layer_name='TRUE-COLOR', csv_file='data/inputs/filtered_incidents.csv'):
    """Downloads an image for a given row ID and saves it to the specified path."""
    row = get_row_details(row_id, csv_file=csv_file)
    if row is None:
        print(f"Row ID {row_id} not found.")
        return

    lat = float(row['lat'])
    lon = float(row['lon'])
    open_date_str = row['open_date']
    open_date = datetime.datetime.strptime(open_date_str, '%Y/%m/%d').date()
    start_of_month = open_date.replace(day=1)
    end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(weeks=3)
    image_array = download_image(lat, lon, start_of_month, end_of_month, layer_name=layer_name)

    return image_array



def process_incidents_and_download(csv_file, output_folder, max_downloads=100, dataset_name='default',
                                   layer_name='TRUE-COLOR'):
    """Processes incidents from a CSV file and downloads images for each row based on row ID."""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # Create output folder if it doesn't exist

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        downloads = 0

        for row in reader:
            if downloads >= max_downloads:
                break

            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                open_date_str = row['open_date']
                open_date = datetime.datetime.strptime(open_date_str, '%Y/%m/%d').date()

                start_of_month = open_date.replace(day=1) - datetime.timedelta(days=300)
                end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(
                    days=1)

                folder_path = os.path.join(output_folder, dataset_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                output_path = os.path.join(folder_path, f'id - {row["id"]} - v1.tiff')
                image = download_image(lat, lon, start_of_month, end_of_month, layer_name=layer_name)

                # Ensure the image is in the correct shape (Bands, Height, Width)
                bands, height, width = image.shape

                # Using rasterio to save the image with correct metadata
                transform = from_origin(lon, lat, 1, 1)  # Replace with actual transform if available
                with rasterio.open(
                        output_path, 'w', driver='GTiff',
                        height=height, width=width,
                        count=bands, dtype='uint8',  # or use image.dtype if the dtype is variable
                        crs='+proj=latlong', transform=transform
                ) as dst:
                    for i in range(bands):
                        dst.write(image[i, :, :], i + 1)

                print(f"Downloaded and saved image for row ID: {row['id']}")
                downloads += 1

            except Exception as e:  # Catch and handle possible exceptions
                print(f"Error processing row ID: {row['id']}: {e}")



def test():
    csv_file = 'data/inputs/filtered_incidents.csv'
    output_folder = 'downloaded_images'
    layer_names = ['TRUE-COLOR', 'NDWI']#['TRUE-COLOR', 'NDVI', 'NDWI', 'OILSPILL']

    example_row_id = 10728

    # Set up the matplotlib figure and axes for a 2x2 grid of plots
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(f'Different Imagery Sets for Row ID: {example_row_id}')

    # Flatten the Axes array for easy iterating
    axs = axs.flatten()
    images = []

    for i, layer_name in enumerate(layer_names):
        image_array = download_image_for_row_id(example_row_id, layer_name=layer_name)

        # Plot the image in the corresponding subplot
        ax = axs[i]
        ax.imshow(image_array)
        ax.set_title(layer_name)
        ax.axis('off')  # Hide the axis

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust subplots to fit into the figure area.
    plt.show()


if __name__ == '__main__':
    #x = search_imagery(0, 0, datetime.datetime.now())

    lat, lon = 56, 3
    datetime_obj = datetime.datetime.now() - timedelta(days=14)

    x = download_image(lat, lon, datetime_obj)

    #x = download_image(28.8717, -89.34)
                       #start_date=datetime.datetime(year=2009, month=9, day=28),
                       #end_date=datetime.datetime(year=2009, month=10, day=7),
                       #layer_name='NDWI')

    #test()
    #create_ocean_dataset_from_incidents(10, 'test')
    #process_incidents_and_download(csv_file, output_folder, dataset_name='complete2', layer_name='ALLBANDS')
