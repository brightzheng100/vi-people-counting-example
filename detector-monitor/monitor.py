#
# Debug client for monitoring/debugging the achatina examples
#
# Written by Glen Darling, October 2019.
#

import json
import os
import subprocess
import threading
import time
from datetime import datetime
import base64

from io import BytesIO
from flask import Flask, send_file, render_template

# Configuration constants
MQTT_SUB_COMMAND = 'mosquitto_sub -h detector-mqtt -p 1883 -C 1 '
MQTT_DETECT_TOPIC = '/detect'
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 5200
DUMMY_DETECT_IMAGE='/dummy_detect.jpg'

# Globals for the cached JSON data (last messages on these MQTT topics)
last_detect = None

# Let's Flask
webapp = Flask('monitor')
webapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@webapp.route("/images/detect.jpg")
def get_detect_image():
  if last_detect:
    j = json.loads(last_detect)
    i = base64.b64decode(j['detect']['image'])
    buffer = BytesIO()
    buffer.write(i)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/jpg')
  else:
    return send_file(DUMMY_DETECT_IMAGE)

@webapp.route("/json")
def get_json():
  if last_detect:
    return last_detect.decode("utf-8") + '\n'
  else:
    return '{}\n'

@webapp.route("/")
def get_results():
  if None == last_detect: return '{"error":"Server not ready."}'

  j = json.loads(last_detect)
  n = j['deviceid']
  entities = j['detect']['entities']
  ct = j['detect']['camtime']
  it = j['detect']['time']
  s = j['source']
  u = j['source-url']
  # print(s, u)
  kafka_msg = 'Nothing is being published to EventStreams (kafka)!'
  if 'kafka-sub' in j:
    sub = j['kafka-sub']
    kafka_msg = 'This data is also being published to EventStreams (kafka). Subscribe with: ' + sub + '\n'
  
  # Render
  return render_template("index.html", 
    device_id=n, 
    entities=entities, 
    camera_time=ct, 
    inferencing_time=it,
    kafka_msg=kafka_msg)

# Prevent caching everywhere
@webapp.after_request
def add_header(r):
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  return r

if __name__ == '__main__':

  # Loop forever collecting object detection / classification data from MQTT
  class DetectThread(threading.Thread):
    def run(self):
      global last_detect
      # print("\nMQTT \"" + MQTT_DETECT_TOPIC + "\" topic monitor thread started!")
      DETECT_COMMAND = MQTT_SUB_COMMAND + '-t ' + MQTT_DETECT_TOPIC
      while True:
        last_detect = subprocess.check_output(DETECT_COMMAND, shell=True)
        # print("\n\nMessage received on detect topic...\n")
        # print(last_detect)

  # Main program (instantiates and starts monitor threads and then web server)
  monitor_detect = DetectThread()
  monitor_detect.start()
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)

