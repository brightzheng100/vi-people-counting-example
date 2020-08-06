#
# The pump that calls the CPU yolo REST API, then pushes the results to kafka.
# It can also (optionally) push the data to the local MQTT for debug purposes.
#
# Written by Glen Darling, March 2020.
#

EXAMPLE_TITLE = 'YOLO (COCO) -- for CPU'
EXAMPLE_URL = 'https://github.com/MegaMosquito/achatina/tree/master/yolocpu'

import json
import os
import socket
import subprocess
import threading
import time
from datetime import datetime
import base64
import requests
import urllib.parse
import sys
import logging

# Configuration from the environment
def get_from_env(v, d):
  if v in os.environ and '' != os.environ[v]:
    return os.environ[v]
  else:
    return d

# Logging config
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

DEFAULT_HZN_DEVICE_ID = '** NO DEVICE ID ** PUBLISHING TO KAFKA IS DISABLED **'
HZN_DEVICE_ID = get_from_env('HZN_DEVICE_ID', DEFAULT_HZN_DEVICE_ID)
EVENTSTREAMS_BROKER_URLS = get_from_env('EVENTSTREAMS_BROKER_URLS', '')
EVENTSTREAMS_API_KEY = get_from_env('EVENTSTREAMS_API_KEY', '')
EVENTSTREAMS_PUB_TOPIC = get_from_env('EVENTSTREAMS_PUB_TOPIC', '')
DEFAULT_CAM_URL = get_from_env('DEFAULT_CAM_URL', '')
CAM_URL = get_from_env('CAM_URL', '')
MQTT_PUB_TOPIC = get_from_env('MQTT_PUB_TOPIC', '/detect')
SLEEP_BETWEEN_CALLS = get_from_env('SLEEP_BETWEEN_CALLS', '10')

# Try to compute some kind of value for the CAM URL if one was not provided
if '' == CAM_URL:
  if '' != DEFAULT_CAM_URL:
    # Use the IP Address provided by the Makefile (for dev purposes only)
    CAM_URL = DEFAULT_CAM_URL
  else:
    # If cam service is in Horizon requiredServices, then its name can be used
    try:
      addr = socket.gethostbyname('detector-cam')
      CAM_URL = 'http://' + addr + ':80/'
    except:
      # If all else fails, just give 'em Queen
      CAM_URL = 'https://upload.wikimedia.org/wikipedia/commons/e/e7/QueenPerforming1977.jpg'

# Additional configuration constants
TEMP_FILE = '/tmp/yolo.json'
YOLO_URL = 'http://detector-service:80/detect?kind=jpg&url=' + urllib.parse.quote(CAM_URL)
MQTT_PUB_COMMAND = 'mosquitto_pub -h detector-mqtt -p 1883'
DEBUG_PUB_COMMAND = MQTT_PUB_COMMAND + ' -t ' + MQTT_PUB_TOPIC + ' -f '
if '' != EVENTSTREAMS_BROKER_URLS and '' != EVENTSTREAMS_API_KEY and '' != EVENTSTREAMS_PUB_TOPIC:
  KAFKA_PUB_COMMAND = 'kafkacat -P -b ' + EVENTSTREAMS_BROKER_URLS + ' -X api.version.request=true -X security.protocol=sasl_ssl -X sasl.mechanisms=PLAIN -X sasl.username=token -X sasl.password="' + EVENTSTREAMS_API_KEY + '" -t ' + EVENTSTREAMS_PUB_TOPIC + ' '
else:
  KAFKA_PUB_COMMAND = ''

logging.info("DEFAULT_CAM_URL: %s", DEFAULT_CAM_URL)
logging.info("CAM_URL: %s", CAM_URL)
logging.info("MQTT_PUB_COMMAND: %s", MQTT_PUB_COMMAND)
logging.info("YOLO_URL: %s", YOLO_URL)

if __name__ == '__main__':

  # Logging config
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

  while True:
    try:
      # Pause briefly (to not hog the CPU too much)
      logging.info('Sleeping for %s seconds...', SLEEP_BETWEEN_CALLS)
      time.sleep(int(SLEEP_BETWEEN_CALLS))

      # Request one run from the yolo REST service...
      logging.info('Initiating a request...')
      logging.info('URL is: %s', YOLO_URL)

      r = requests.get(YOLO_URL)
      if (r.status_code > 299):
          logging.error('Yolo request failed. Response Code: %d', r.status_code)
          time.sleep(10)
          continue
      logging.info('Successful response received!')

      j = r.json()
      d = datetime.fromtimestamp(j['detect']['date']).strftime('%Y-%m-%d %H:%M:%S')
      logging.debug('Date: %s, Cam: %0.2f sec, Yolo: %0.2f msec.', d, j['detect']['camtime'], j['detect']['time'] * 1000.0)

      # Add info into the JSON about this example
      j['source'] = EXAMPLE_TITLE
      j['source-url'] = EXAMPLE_URL
      j['deviceid'] = HZN_DEVICE_ID

      # Push JSON to a file (so we can publish it, since it overflows the CLI)
      with open(TEMP_FILE, 'w') as temp_file:
        json.dump(j, temp_file)

      # Publish to kafka if a device ID and appropriate creds were provided
      if HZN_DEVICE_ID != DEFAULT_HZN_DEVICE_ID and '' != KAFKA_PUB_COMMAND:
        logging.info('Kafka: %s %s', KAFKA_PUB_COMMAND, TEMP_FILE)
        discard = subprocess.run(KAFKA_PUB_COMMAND + TEMP_FILE, shell=True)
      else:
        logging.warn('Kafka: *** PUBLICATION DISABLED **')

      # (Optionally) publish to the debug topic (with subscribe info if approp)
      if '' != MQTT_PUB_TOPIC:
        # Did we publish this stuff to kafka?
        if '' != KAFKA_PUB_COMMAND:
          # Provide info to the caller about how to subscribe to this kafka stream
          j['kafka-sub'] = 'kafkacat -C -b ' + EVENTSTREAMS_BROKER_URLS + ' -X api.version.request=true -X security.protocol=sasl_ssl -X sasl.mechanisms=PLAIN -X sasl.username=token -X sasl.password="' + EVENTSTREAMS_API_KEY + '" -t ' + EVENTSTREAMS_PUB_TOPIC
          # Rewrite the file with the updated JSON
          with open(TEMP_FILE, 'w') as temp_file:
            json.dump(j, temp_file)
        logging.info('MQTT: %s %s', DEBUG_PUB_COMMAND, TEMP_FILE)
        discard = subprocess.run(DEBUG_PUB_COMMAND + TEMP_FILE, shell=True)

    except Exception as e:
      logging.error("Exception occurred in main loop!", exc_info=True)
      pass
