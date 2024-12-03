import sys
import time
import json
import random
import paho.mqtt.client as mqtt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QLineEdit
from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MqttClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.connected = True
        self.client.subscribe(window.topic_input.text())

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
        self.connected = False

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        temperature = data.get("temperature", "N/A")
        humidity = data.get("humidity", "N/A")
        window.update_labels(temperature, humidity)

    def connect(self, broker, port, topic):
        self.client.connect(broker, int(port), 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload):
        if self.connected:
            self.client.publish(topic, payload)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.plot()

    def plot(self, x_data=None, y_data=None, title="Temperature Plot", ylabel="Temperature (°C)"):
        self.axes.clear()
        if x_data is not None and y_data is not None:
            self.axes.plot(x_data, y_data, 'r-', label='Temperature')
        self.axes.set_title(title)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel("Time")
        self.axes.legend(loc='upper left')
        self.draw()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.mqtt_client = MqttClient()
        self.temperature_data = []
        self.time_data = []

    def initUI(self):
        self.setWindowTitle("MQTT Data Acquisition")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        # Horizontal layout for broker, port, and topic
        input_layout = QHBoxLayout()
        self.broker_input = QLineEdit("broker.hivemq.com")
        self.broker_input.setMaxLength(20)
        self.port_input = QLineEdit("1883")
        self.port_input.setMaxLength(20)
        self.topic_input = QLineEdit("testmazenkovic/topic1")
        self.topic_input.setMaxLength(20)
        input_layout.addWidget(QLabel("Broker:"))
        input_layout.addWidget(self.broker_input)
        input_layout.addWidget(QLabel("Port:"))
        input_layout.addWidget(self.port_input)
        input_layout.addWidget(QLabel("Topic:"))
        input_layout.addWidget(self.topic_input)
        self.layout.addLayout(input_layout)

        self.label = QLabel("MQTT Messages:", self)
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        # Horizontal layout for temperature and humidity
        data_layout = QHBoxLayout()
        self.humidity_label = QLabel("Humidity: N/A", self)
        data_layout.addWidget(self.humidity_label)
        self.temperature_label = QLabel("Temperature: N/A", self)
        data_layout.addWidget(self.temperature_label)
        self.layout.addLayout(data_layout)

        button_layout = QHBoxLayout()

        self.connect_button = QPushButton()
        self.connect_button.setIcon(QIcon("power-button.png"))
        self.connect_button.setIconSize(QSize(24, 24))
        self.connect_button.clicked.connect(self.connect_mqtt)
        button_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton()
        self.disconnect_button.setIcon(QIcon("power-on.png"))
        self.disconnect_button.setIconSize(QSize(24, 24))
        self.disconnect_button.clicked.connect(self.disconnect_mqtt)
        button_layout.addWidget(self.disconnect_button)

        self.layout.addLayout(button_layout)

        self.plot_canvas = PlotCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.plot_canvas)

        self.setLayout(self.layout)

    def connect_mqtt(self):
        broker = self.broker_input.text()
        port = self.port_input.text()
        topic = self.topic_input.text()
        self.mqtt_client.connect(broker, port, topic)

    def disconnect_mqtt(self):
        self.mqtt_client.disconnect()

    def update_labels(self, temperature, humidity):
        self.temperature_label.setText(f"Temperature: {temperature} °C")
        self.humidity_label.setText(f"Humidity: {humidity} %")
        self.text_edit.append(f"Received: Temperature={temperature} °C, Humidity={humidity} %")
        self.update_plots(temperature)

    def update_plots(self, temperature):
        self.time_data.append(time.time())
        self.temperature_data.append(temperature)
        self.plot_canvas.plot(self.time_data, self.temperature_data, title="Temperature Plot", ylabel="Temperature (°C)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Start publishing data in a separate thread
    import threading
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
            window.mqtt_client.publish(window.topic_input.text(), payload)
            print(f"Published: {payload}")
            # Wait for 5 seconds before publishing next data
            time.sleep(5)

    threading.Thread(target=publish_data).start()

    sys.exit(app.exec())
