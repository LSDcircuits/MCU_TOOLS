# this file contains a winding coming from the print of a MCU potentially useful sor sound analysy.
import sys
import time
import numpy as np
import serial
import serial.tools.list_ports

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QLabel, QSlider
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries
from PySide6.QtCore import Qt, QThread, Signal, QPointF
from PySide6.QtGui import QPainter


# ---------------- Serial Thread ----------------
class SerialReader(QThread):

    data_received = Signal(float)

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True

    def run(self):

        ser = serial.Serial(self.port, self.baudrate, timeout=1)

        while self.running:

            try:
                line = ser.readline().decode().strip()

                if line:
                    val = float(line)
                    self.data_received.emit(val)

            except:
                pass

        ser.close()

    def stop(self):
        self.running = False
        self.wait()


# ---------------- GUI ----------------
class FourierSerialMonitor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial Fourier Winding Analyzer")
        self.setFixedSize(1200, 700)

        self.reader = None

        # ----- Data buffers -----
        self.timestamps = []
        self.values = []

        self.max_buffer = 5000

        # ----- Parameters -----
        self.time_window = 1.0
        self.w = 10

        self.init_ui()
        self.refresh_ports()

    # ---------------- UI ----------------
    def init_ui(self):

        layout = QVBoxLayout(self)

        # ----- Serial Controls -----
        port_row = QHBoxLayout()

        port_row.addWidget(QLabel("Port"))

        self.port_combo = QComboBox()
        port_row.addWidget(self.port_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(refresh_btn)

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_serial)
        port_row.addWidget(connect_btn)

        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self.disconnect_serial)
        port_row.addWidget(disconnect_btn)

        layout.addLayout(port_row)

        # ----- Sliders -----

        slider_row = QHBoxLayout()

        slider_row.addWidget(QLabel("Time Window"))

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(1)
        self.time_slider.setMaximum(10)
        self.time_slider.setValue(10)
        self.time_slider.valueChanged.connect(self.update_time_window)

        slider_row.addWidget(self.time_slider)

        slider_row.addWidget(QLabel("Winding ω"))

        self.w_slider = QSlider(Qt.Horizontal)
        self.w_slider.setMinimum(1)
        self.w_slider.setMaximum(200)
        self.w_slider.setValue(10)
        self.w_slider.valueChanged.connect(self.update_w)

        slider_row.addWidget(self.w_slider)

        layout.addLayout(slider_row)

        # ----- Charts -----

        chart_row = QHBoxLayout()

        # Time chart
        self.series_time = QLineSeries()

        self.chart_time = QChart()
        self.chart_time.addSeries(self.series_time)
        self.chart_time.createDefaultAxes()
        self.chart_time.setTitle("Time Signal")

        self.view_time = QChartView(self.chart_time)
        self.view_time.setRenderHint(QPainter.Antialiasing)

        chart_row.addWidget(self.view_time)

        # Fourier winding chart
        self.series_complex = QLineSeries()

        self.series_com = QScatterSeries()
        self.series_com.setMarkerSize(12)

        self.chart_complex = QChart()
        self.chart_complex.addSeries(self.series_complex)
        self.chart_complex.addSeries(self.series_com)
        self.chart_complex.createDefaultAxes()
        self.chart_complex.setTitle("Fourier Winding")

        self.view_complex = QChartView(self.chart_complex)
        self.view_complex.setRenderHint(QPainter.Antialiasing)

        chart_row.addWidget(self.view_complex)

        layout.addLayout(chart_row)

    # ---------------- Serial ----------------
    def refresh_ports(self):

        self.port_combo.clear()

        for p in serial.tools.list_ports.comports():
            self.port_combo.addItem(p.device)

    def connect_serial(self):

        port = self.port_combo.currentText()

        if not port:
            return

        self.reader = SerialReader(port)
        self.reader.data_received.connect(self.on_data)
        self.reader.start()

    def disconnect_serial(self):

        if self.reader:
            self.reader.stop()
            self.reader = None

    # ---------------- Data Handling ----------------
    def on_data(self, value):

        t = time.time()

        self.timestamps.append(t)
        self.values.append(value)

        if len(self.timestamps) > self.max_buffer:
            self.timestamps.pop(0)
            self.values.pop(0)

        self.update_plots()

    # ---------------- Sliders ----------------
    def update_time_window(self, val):

        self.time_window = val / 10.0
        self.update_plots()

    def update_w(self, val):

        self.w = val
        self.update_plots()

    # ---------------- Plotting ----------------
    def update_plots(self):

        if len(self.timestamps) < 5:
            return

        now = self.timestamps[-1]

        # Select time window
        t = []
        y = []

        for i in range(len(self.timestamps)):

            if now - self.timestamps[i] <= self.time_window:
                t.append(self.timestamps[i])
                y.append(self.values[i])

        if len(t) < 5:
            return

        t = np.array(t)
        y = np.array(y)

        t = t - t[0]

        # ----- Time plot -----
        pts = [QPointF(t[i], y[i]) for i in range(len(t))]
        self.series_time.replace(pts)

        self.chart_time.axes(Qt.Horizontal)[0].setRange(0, max(t))

        # ----- Fourier winding -----

        complex_signal = y * np.exp(-1j * self.w * t)

        real = np.real(complex_signal)
        imag = np.imag(complex_signal)

        pts_complex = [QPointF(real[i], imag[i]) for i in range(len(real))]
        self.series_complex.replace(pts_complex)

        # Center of mass
        com = np.mean(complex_signal)

        self.series_com.replace([QPointF(np.real(com), np.imag(com))])

        m = max(np.max(np.abs(real)), np.max(np.abs(imag))) + 0.5

        self.chart_complex.axes(Qt.Horizontal)[0].setRange(-m, m)
        self.chart_complex.axes(Qt.Vertical)[0].setRange(-m, m)

    # ---------------- Cleanup ----------------
    def closeEvent(self, event):

        self.disconnect_serial()
        event.accept()


# ---------------- Main ----------------
if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = FourierSerialMonitor()
    win.show()

    sys.exit(app.exec())
