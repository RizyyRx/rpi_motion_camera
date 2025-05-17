import RPi.GPIO as GPIO
import time
import os
import json
# from ratelimit import limits
from uuid import uuid4
from threading import Thread
import requests

def get_config(key):
    config_file = "/home/riz/iot_config.json"

    # Using 'with open' to handle file operations safely
    with open(config_file, "r") as file:
        config = json.load(file)  # json.load converts JSON data to a Python dictionary

    if key in config:
        return config[key]
    else:
        raise Exception("The key {} is not found in config.json",format(key))

print("started motion_camera.py script")
DEVICE_ID = "raspi_cam_1"
STORAGE_LOCATION = "motion_captures"

if not os.path.exists(STORAGE_LOCATION):
    os.mkdir(STORAGE_LOCATION)

GPIO.setmode(GPIO.BCM)
channel = 27
GPIO.setup(channel,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

def upload_picture(filename):
    name = filename.split("/")[-1]

    url = "http://192.168.125.202:5000/api/motion/capture"

    payload = {}
    files=[
    ('file',(name, open(filename,'rb'),'image/jpeg'))
    ]
    headers = {
    'X-Authorization': 'Bearer ' + get_config("api_key"), #api key
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    print(response.text)

def click_picture():
    print("taking pic..")
    uuid = str(uuid4())
    os.system('libcamera-still -o '+STORAGE_LOCATION+ "/" +uuid+'.jpg --timeout 1000 --verbose 0')
    print("done")
    t = Thread(target = upload_picture, args=(STORAGE_LOCATION+ "/" +uuid+'.jpg',))
    t.start()

try:
    while True:
        if GPIO.input(channel):
            try:
                print("motion detected")
                click_picture()
            except Exception as e:
                print(f"Error taking picture: {e}")
            time.sleep(5)
except KeyboardInterrupt:
	print("zzzzz")
	GPIO.cleanup()
