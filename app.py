from flask import Flask, render_template
from keras.models import load_model
import cv2
import os

# email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Constants
image_size_width = 255
image_size_height = 255
sender_email = 'sea.sentry.com@gmail.com'
sender_password = os.environ.get('PASSWORD') 
# model = load_model('final_model.h5')

# Create a Flask app
app = Flask(__name__)

locations_of_oil_spills = []


# Request satellite data from sentinel (we define where we want to look for oil spills).
# 5km between each point, this is about a difference of 0.05 in latitude and longitude.
def generate_lat_long_points(range_upper_left = (90, 180), range_bottom_right = (-90, -180), buffer=0.05):
    # Generate a list of lat and lon points to search for oil spills.
    (x1, x2) = range_upper_left
    (y1, y2) = range_bottom_right
    lat_points = [i for i in range(x1, x2, buffer)]
    lon_points = [i for i in range(y1, y2, buffer)]
    return [(lat, lon) for lat in lat_points for lon in lon_points]


# Run trained model on image and if it is an oil spill, add it to the list of oil spills.
def predict_oil_spill(image_url, lat, lon, open_date_str):
    # Run the model on the image and return the result.
    image = cv2.imread(image_url)
    image = cv2.resize(image, (image_size_width, image_size_height))
    # if model.predict(image) == 1:
    #     locations_of_oil_spills.append((lat, lon, open_date_str))
    

# Notify investor of oil any oil spills, using email client.
def send_email(receiver_email = "thomas.c.smail@gmail.com", subject = "Oil Spill Alert", message = "There is an oil spill at one of your investments."):
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
    # Return the html file with the 
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)