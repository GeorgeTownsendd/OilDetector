import ee

# Initialize the Google Earth Engine module.
ee.Initialize()

def get_sentinel_image(lat, lon, start_date='2018-01-01', end_date='2023-12-31', cloud_cover_max=10):
    """
    Exports the most recent Sentinel-2 image with minimal cloud cover for a specified area to Google Drive.

    Parameters:
    lat (float): Latitude of the point of interest.
    lon (float): Longitude of the point of interest.
    start_date (str): Start date for the image collection in 'YYYY-MM-DD' format. Default is '2018-01-01'.
    end_date (str): End date for the image collection in 'YYYY-MM-DD' format. Default is '2023-12-31'.
    cloud_cover_max (int): Maximum allowed cloud cover percentage for the images. Default is 10.
    """
    # Define the Area of Interest (AOI) as a buffer around the specified latitude and longitude
    aoi = ee.Geometry.Point([lon, lat]).buffer(10000)  # Buffer by 10 km

    # Create a Sentinel-2 image collection filtered by date, AOI, and cloud cover
    collection = ee.ImageCollection('COPERNICUS/S2') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max)) \
        .sort('system:time_start', False)  # Sort by descending date

    # Get the most recent image from the filtered collection
    image = collection.first()

    # Select the RGB bands (B4, B3, B2) for the image
    rgb_image = image.select(['B4', 'B3', 'B2'])

    # Set up the export task parameters for exporting the image to Google Drive
    export_params = {
        'image': rgb_image,
        'description': 'sentinel_image',
        'scale': 10,
        'region': aoi,
        'fileFormat': 'GeoTIFF'
    }

    # Start the export task
    task = ee.batch.Export.image.toDrive(**export_params)
    task.start()

    print("Export to Google Drive started. Check the Tasks tab in your Earth Engine account.")

# Example usage of the function
get_sentinel_image(40.7128, -74.0060)  # Coordinates for New York City, for example
