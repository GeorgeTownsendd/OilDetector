from flask import Flask, render_template
from keras.models import load_model
import cv2
import os
import json

# email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Constants
image_size_width = 255
image_size_height = 255
sender_email = 'sea.sentry.com@gmail.com'
sender_password = os.environ.get('PASSWORD') 
model = load_model('best_model.h5')
point_off_coast_of_scotland_1 = (57, -1)
point_off_coast_of_scotland_2 = (56, -2)

TESTING_NO_EMAIL = False
TESTING_NO_MODEL = True
TESTING_NO_PRICE_PREDICTION = True

# Create a Flask app
app = Flask(__name__)

locations_of_oil_spills = [(11, -60)]


# Request satellite data from sentinel (we define where we want to look for oil spills).
# 5km between each point, this is about a difference of 0.05 in latitude and longitude.
def generate_lat_long_points(range_upper_left = (90, 180), range_bottom_right = (-90, -180), buffer=0.05):
    # Generate a list of lat and lon points to search for oil spills.
    (x1, x2) = range_upper_left
    (y1, y2) = range_bottom_right
    lat_points = [i for i in range(x1 * 20, x2 * 20, int(buffer * 20))]
    lon_points = [i for i in range(y1 * 20, y2 * 20, int(buffer * 20))]
    return [(lat / 20, lon  / 20) for lat in lat_points for lon in lon_points]


# Run trained model on image and if it is an oil spill, add it to the list of oil spills.
def predict_oil_spill(image_url, lat, lon):
    # Run the model on the image and return the result.
    image = cv2.imread(image_url)
    image = cv2.resize(image, (image_size_width, image_size_height))
    bool_ret = False
    if model.predict(image) == 1:
        bool_ret = True
    return bool_ret

# Notify investor of oil any oil spills, using email client.
def send_email(receiver_email = "thomas.c.smail@gmail.com", subject = "Oil Spill Alert", message = "There is an oil spill. You should buy now, before the price spikes and sell when the oil price is high."):
    # Send an email to the investor if there are any oil spills.
    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    body = message
    message.attach(MIMEText(body, "plain"))

    # Connect to the SMTP server
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    # Login to the email account
    server.login(sender_email, sender_password)

    # Send email
    server.sendmail(sender_email, receiver_email, message.as_string())

    # Close the SMTP server connection
    server.quit()

# Return the map to the user.
@app.route('/')
def homepage_func():
    # Check if there is an oil spill
    is_spill = False
    for lat, lon in generate_lat_long_points(point_off_coast_of_scotland_1, point_off_coast_of_scotland_2):
        if is_spill:
            break

        # make requests to the sentinel API to get the image
        if TESTING_NO_MODEL:
            is_spill = False
        else:
            image = "GET_IMAGE_FROM_SENTINEL_API"
            is_spill = predict_oil_spill(image, lat, lon, "2021-01-01")
            locations_of_oil_spills.append((lat, lon))
    json_data = json.dumps(locations_of_oil_spills)

    # Save json data to file
    with open('static/data.json', 'w') as f:
        f.write(json_data)
    

    if is_spill:
        if TESTING_NO_PRICE_PREDICTION:
            sell_price = 100
        else:
            sell_price = 100 
            # max(heston_price(true))
        if TESTING_NO_EMAIL:
            print(f"There is an oil spill at {lat}, {lon} you should buy now, before the price spikes and sell when the oil price is {sell_price}.")
        else:
            send_email(message=f"There is an oil spill at {lat}, {lon} you should buy now, before the price spikes and sell when the oil price is {sell_price}.")
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)