# FOURIER_WINDING_QT_FULL.py
# Clean + Optimized + Proper Scaling

import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fourier Winding Visualization")
        self.setFixedSize(1200, 650)

        # -------- Parameters --------
        self.A = 4
        self.B = 2
        self.w = 8

        self.t = np.linspace(0, 10, 600)

        # -------- Sliders --------
        self.slider_A = self.make_slider(20, "A", self.A)
        self.slider_B = self.make_slider(80, "B", self.B)
        self.slider_w = self.make_slider(140, "Winding ω", self.w)

        # -------- Time Domain Chart --------
        self.series_time = QLineSeries()

        self.chart_time = QChart()
        self.chart_time.addSeries(self.series_time)
        self.chart_time.createDefaultAxes()
        self.chart_time.setTitle("Time Domain: sin(A t) + cos(B t)")

        self.chart_time.axes(Qt.Horizontal)[0].setRange(0, 10)
        self.chart_time.axes(Qt.Vertical)[0].setRange(-3, 3)

        self.view_time = QChartView(self.chart_time, self)
        self.view_time.setRenderHint(QPainter.Antialiasing)
        self.view_time.setGeometry(20, 220, 550, 380)

        # -------- Complex Winding Chart --------
        self.series_complex = QLineSeries()

        self.series_com = QScatterSeries()
        self.series_com.setMarkerSize(14)
        self.series_com.setColor(Qt.red)

        self.chart_complex = QChart()
        self.chart_complex.addSeries(self.series_complex)
        self.chart_complex.addSeries(self.series_com)
        self.chart_complex.createDefaultAxes()
        self.chart_complex.setTitle("Complex Winding")

        self.chart_complex.axes(Qt.Horizontal)[0].setRange(-3, 3)
        self.chart_complex.axes(Qt.Vertical)[0].setRange(-3, 3)

        self.view_complex = QChartView(self.chart_complex, self)
        self.view_complex.setRenderHint(QPainter.Antialiasing)
        self.view_complex.setGeometry(620, 220, 550, 380)

        self.update_plot()

    # -------- Slider Factory --------
    def make_slider(self, y_pos, name, value):
        label = QLabel(f"{name}: {value}", self)
        label.move(20, y_pos)

        slider = QSlider(Qt.Horizontal, self)
        slider.setGeometry(120, y_pos, 300, 20)
        slider.setMinimum(1)
        slider.setMaximum(20)
        slider.setValue(value)

        slider.valueChanged.connect(
            lambda val, n=name, l=label: self.update_value(n, val, l)
        )

        return slider

    # -------- Update Parameter --------
    def update_value(self, name, val, label):
        label.setText(f"{name}: {val}")

        if name == "A":
            self.A = val
        elif name == "B":
            self.B = val
        elif name == "Winding ω":
            self.w = val

        self.update_plot()

    # -------- Fourier Logic --------
    def update_plot(self):

        # ----- Time domain -----
        y = np.sin(self.A * self.t) + np.cos(self.B * self.t)

        time_points = [QPointF(self.t[i], y[i]) for i in range(len(self.t))]
        self.series_time.replace(time_points)

        # ----- Complex winding -----
        complex_signal = y * np.exp(-1j * self.w * self.t)

        real = np.real(complex_signal)
        imag = np.imag(complex_signal)

        complex_points = [QPointF(real[i], imag[i]) for i in range(len(real))]
        self.series_complex.replace(complex_points)

        # ----- Center of mass -----
        com = np.mean(complex_signal)
        self.series_com.replace([QPointF(com.real, com.imag)])

        # ----- Dynamic axis scaling (prevents clipping) -----
        max_val = max(np.max(np.abs(real)), np.max(np.abs(imag))) + 0.5
        max_val = max(max_val, 1.5)

        self.chart_complex.axes(Qt.Horizontal)[0].setRange(-max_val, max_val)
        self.chart_complex.axes(Qt.Vertical)[0].setRange(-max_val, max_val)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
