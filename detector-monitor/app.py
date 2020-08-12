"""

An MQTT-based envent driven web app for monitoring the visual inferencing results.

By Bright Zheng

"""

import eventlet
import json
import sys
import logging

from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

# Variables
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_BIND_PORT = 5200
MQTT_BROKER_URL = 'detector-mqtt'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_DETECT = '/detect'

# Logging config
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

eventlet.monkey_patch()
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'detector-mqtt'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_CLEAN_SESSION'] = True

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
  return render_template('index.html')

# Prevent caching everywhere
@app.after_request
def add_header(r):
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  return r

# MQTT on message
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  logging.info("handle_mqtt_message called")
  logging.info("from topic: %s", message.topic)
  # emit a mqtt_message event to the socket containing the message data
  socketio.emit('mqtt_message', data=message.payload.decode())

if __name__ == '__main__':

  # Subscribe to the "/detect" topic
  mqtt.subscribe(MQTT_TOPIC_DETECT)

  # important: Do not use reloader because this will create two Flask instances.
  # Flask-MQTT only supports running with one instance
  socketio.run(app, host=FLASK_BIND_ADDRESS, port=FLASK_BIND_PORT, use_reloader=False, debug=False)
