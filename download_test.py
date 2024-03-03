from sentinelhub import SHConfig
import rasterio
import pandas as pd
from datetime import timedelta

from auth import *


client_id, client_secret = read_client_credentials(CREDENTIALS_PATH)
AUTH_TOKEN = create_oauth_session(client_id, client_secret).token['access_token']

config = SHConfig(sh_client_id=client_id, sh_client_secret=client_secret, instance_id='7155b573-d6a9-4712-be56-b4b3e34c5706')

import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)


def get_latest_image(lat, lon):
    time_interval = (datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now())
    request = generate_image_request(lat, lon, time_interval)
    image_array = image_from_request(request)

    return image_array


def generate_image_request(lat, lon, time_interval, buffer=0.1):
    evalscript_all_bands = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"],
                    units: "DN"
                }],
                output: {
                    bands: 13,
                    sampleType: "INT16",
                    format: "image/tiff"
                }
            };
        }

        function evaluatePixel(sample) {
            return [sample.B01,
                    sample.B02,
                    sample.B03,
                    sample.B04,
                    sample.B05,
                    sample.B06,
                    sample.B07,
                    sample.B08,
                    sample.B8A,
                    sample.B09,
                    sample.B10,
                    sample.B11,
                    sample.B12];
        }
    """

    _bbox = (lon - buffer, lat - buffer, lon + buffer, lat + buffer)
    bbox = BBox(bbox=_bbox, crs=CRS.WGS84)
    size = (512, 512)

    request = SentinelHubRequest(
        evalscript=evalscript_all_bands,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L1C,
                time_interval=time_interval,
                mosaicking_order=MosaickingOrder.LEAST_CC,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )

    return request


def image_from_request(request):
    return request.get_data()[0]


def save_image(image_array, output_path):
    height, width, bands = image_array.shape
    with rasterio.open(output_path, 'w', driver='GTiff', height=height, width=width, count=bands, dtype='uint16', crs='+proj=latlong') as dst:
        for i in range(1, bands + 1):
            dst.write(image_array[:, :, i-1], i)


def create_dataset_from_incidents(incident_list_fn, output_dir='data/datasets/example/', time_offset_days=0, n=1, tag='v1'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    incidents = pd.read_csv(incident_list_fn)
    for incident in incidents.iterrows():
        i, incident = incident
        lat, lon = int(incident[5]), int(incident[6])

        open_date_str = incident['open_date']
        open_date = datetime.datetime.strptime(open_date_str, '%Y/%m/%d').date()
        time_interval = (open_date - timedelta(days=3.5) + timedelta(days=time_offset_days), open_date + timedelta(days=3.5) + timedelta(days=time_offset_days))

        image_filename = output_dir + f'incident_{incident["id"]}_{tag}.tiff'
        incident_image_request = generate_image_request(lat, lon, time_interval)
        image_array = image_from_request(incident_image_request)
        save_image(image_array, image_filename)

        print(f'Saved imagery for incident ID={incident["id"]} ({i} of {len(incidents)})')


incident_list = 'data/inputs/filtered_incidents.csv'

create_dataset_from_incidents(incident_list, output_dir='data/datasets/v1/', n=500)
create_dataset_from_incidents(incident_list, output_dir='data/datasets/v0/', n=500, time_offset_days=-100)

#lat, lon = 43, 3
#output_path = 'test.tiff'
#time_interval = (datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now())

#image_request = generate_image_request(lat, lon, time_interval)
#image_array = image_from_request(image_request)

#save_image(image_array, output_path)