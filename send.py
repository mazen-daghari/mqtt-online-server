import paho.mqtt.client as mqtt
import time
import json
import random

# MQTT settings
broker = "broker.hivemq.com"
port = 1883
topic = "testmazenkovic/topic1"

# Create an MQTT client
client = mqtt.Client()

# Connect to the MQTT broker
client.connect(broker, port, 60)

# Function to publish data
def publish_data():
    while True:
        # Simulate sensor data
        data = {
            "temperature": round(random.uniform(20.0, 30.0), 2),
            "humidity": round(random.uniform(30.0, 60.0), 2)
        }
        # Convert data to JSON string
        payload = json.dumps(data)
        # Publish data to the MQTT topic
        client.publish(topic, payload)
        print(f"Published: {payload}")
        # Wait for 5 seconds before publishing next data
        time.sleep(5)

# Start publishing data
publish_data()
