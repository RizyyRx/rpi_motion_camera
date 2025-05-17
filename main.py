from pymongo import MongoClient
import json
import os
import time
import subprocess

def get_config(key):
    config_file = "/home/riz/iot_config.json"

    # Using 'with open' to handle file operations safely
    with open(config_file, "r") as file:
        config = json.load(file)  # json.load converts JSON data to a Python dictionary

    if key in config:
        return config[key]
    else:
        raise Exception("The key {} is not found in config.json",format(key))
    
# Process variable for motion detection
PROCESS = None

def start_motion_detection():
    """Start the motion detection process if not already running."""
    global PROCESS
    if PROCESS is None or PROCESS.poll() is not None:
        print("🟢 Starting motion detection...")

        PROCESS = subprocess.Popen(["python3", "motion_camera.py"])

    else:
        print("✅ Motion detection is already running.")

def stop_motion_detection():
    """Stop the motion detection process."""
    global PROCESS
    if PROCESS is not None:
        print("🛑 Stopping motion detection...")
        PROCESS.terminate()
        PROCESS.wait()
        PROCESS = None
    else:
        print("❌ Motion detection is not running.")
    
# connect to db    
try:
    client = MongoClient(get_config("mongodb_connection_string"))
    db = client[get_config("mongodb_database")]

    if db is not None:
        print("Connected successfully")
    else:
        print("Not connected")
except Exception as e:
    print(f"Error: {e}")
    
previous_value = None
try:
    while True:
        result = db.devices.find_one({"user":get_config("username")})

        present_value = result["device_status"]
        print(f"current value is {present_value}")

        if present_value == previous_value:
            print("Value is same, sleeping for 10secs....")
            time.sleep(10)
            continue
        
        previous_value = present_value

        if result["device_status"] == "on":
            start_motion_detection()

        elif result["device_status"] == "off":
            stop_motion_detection()

        elif result["device_status"] == "sleep":
            duration = result["sleep_time"]
            if duration is not None and isinstance(duration, (int, float)) and duration > 0:
                print(f"😴 Sleeping for {duration} seconds...")
                stop_motion_detection()
                time.sleep(duration)
                print("⏰ Waking up!")

                # Update device status on db to "on"
                update_result = db.devices.update_one(
                    {"user": get_config("username")},
                    {"$set": {"device_status":"on","sleep_time":None}}
                )

            else:
                print("⚠️ Invalid sleep duration received. Ignoring.")
except KeyboardInterrupt:
    stop_motion_detection()
    print("Goodbye.....")


