import sys
import serial
import time
import paho.mqtt.client as mqtt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# MQTT settings
broker = "broker.hivemq.com"
port = 1883
topic = "test/topic"

# Serial settings
serial_port = "COM4"  # Replace with your Arduino's serial port
baud_rate = 9600

class MqttClient:
    def __init__(self, broker, port, topic):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.broker = broker
        self.port = port
        self.topic = topic

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.client.subscribe(self.topic)

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        print(f"Received message: {msg.payload.decode()}")

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, message):
        self.client.publish(self.topic, message)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.plot()

    def plot(self, x_data=None, y_data=None, title="Plot", ylabel="Value"):
        self.axes.clear()
        if x_data is not None and y_data is not None:
            self.axes.plot(x_data, y_data, 'r-')
        self.axes.set_title(title)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel("Time")
        self.draw()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.mqtt_client = MqttClient(broker, port, topic)
        self.serial_connection = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        self.temperature_data = []
        self.humidity_data = []
        self.time_data = []

    def initUI(self):
        self.setWindowTitle("MQTT Data Acquisition")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.label = QLabel("MQTT Messages:", self)
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        self.humidity_label = QLabel("Humidity: N/A", self)
        self.layout.addWidget(self.humidity_label)

        self.temperature_label = QLabel("Temperature: N/A", self)
        self.layout.addWidget(self.temperature_label)

        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.connect_mqtt)
        self.layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect", self)
        self.disconnect_button.clicked.connect(self.disconnect_mqtt)
        self.layout.addWidget(self.disconnect_button)

        self.temperature_plot = PlotCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.temperature_plot)

        self.humidity_plot = PlotCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.humidity_plot)

        self.setLayout(self.layout)

    def connect_mqtt(self):
        self.mqtt_client.connect()
        self.serial_connection = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize
        self.timer.start(1000)  # Read serial data every second

    def disconnect_mqtt(self):
        self.mqtt_client.disconnect()
        if self.serial_connection:
            self.serial_connection.close()
        self.timer.stop()

    def read_serial_data(self):
        if self.serial_connection and self.serial_connection.in_waiting > 0:
            line = self.serial_connection.readline().decode('utf-8').rstrip()
            self.text_edit.append(f"Received: {line}")
            self.mqtt_client.publish(line)
            self.update_labels(line)
            self.update_plots(line)

    def update_labels(self, data):
        try:
            data_dict = eval(data)
            temperature = data_dict.get("temperature", "N/A")
            humidity = data_dict.get("humidity", "N/A")
            self.temperature_label.setText(f"Temperature: {temperature} °C")
            self.humidity_label.setText(f"Humidity: {humidity} %")
        except:
            pass

    def update_plots(self, data):
        try:
            data_dict = eval(data)
            temperature = data_dict.get("temperature", None)
            humidity = data_dict.get("humidity", None)
            if temperature is not None and humidity is not None:
                self.time_data.append(time.time())
                self.temperature_data.append(temperature)
                self.humidity_data.append(humidity)
                self.temperature_plot.plot(self.time_data, self.temperature_data, title="Temperature", ylabel="Temperature (°C)")
                self.humidity_plot.plot(self.time_data, self.humidity_data, title="Humidity", ylabel="Humidity (%)")
        except:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
