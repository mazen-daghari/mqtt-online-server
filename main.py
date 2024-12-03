import paho.mqtt.client as mqtt

# MQTT settings
broker = "broker.hivemq.com"
port = 1883
topic = "testmazenkovic/topic1"

# Create an MQTT client
client = mqtt.Client()

# Define the callback function for when a message is received
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()}")

# Set the on_message callback function
client.on_message = on_message

# Connect to the MQTT broker
client.connect(broker, port, 60)

# Subscribe to the MQTT topic
client.subscribe(topic)

# Start the MQTT client loop
client.loop_forever()
