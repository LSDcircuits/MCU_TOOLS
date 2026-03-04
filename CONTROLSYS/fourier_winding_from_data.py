import sys
import numpy as np
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QSlider, QPushButton, QFileDialog
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter


class MyWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fourier Winding Visualization")
        self.setFixedSize(1200, 700)

        # ----- Parameters -----
        self.w = 8

        self.t = np.linspace(0, 10, 600)
        self.y = np.zeros_like(self.t)

        # ----- File Selector -----
        self.file_button = QPushButton("Load Spreadsheet", self)
        self.file_button.setGeometry(20, 20, 200, 30)
        self.file_button.clicked.connect(self.load_file)

        self.file_label = QLabel("No file loaded", self)
        self.file_label.move(240, 25)
        self.file_label.resize(400, 30)

        # ----- Slider -----
        self.slider_w = self.make_slider(80, "Winding ω", self.w)

        # ----- Center of Mass Labels -----
        self.com_label = QLabel("Center of Mass: (0.0 , 0.0)", self)
        self.com_label.move(500, 20)
        self.com_label.resize(400, 30)

        self.mag_label = QLabel("Magnitude |COM|: 0.0", self)
        self.mag_label.move(500, 50)
        self.mag_label.resize(400, 30)

        # ----- Time Chart -----
        self.series_time = QLineSeries()

        self.chart_time = QChart()
        self.chart_time.addSeries(self.series_time)
        self.chart_time.createDefaultAxes()
        self.chart_time.setTitle("Time Domain Signal")

        self.view_time = QChartView(self.chart_time, self)
        self.view_time.setRenderHint(QPainter.Antialiasing)
        self.view_time.setGeometry(20, 250, 550, 400)

        # ----- Complex Chart -----
        self.series_complex = QLineSeries()

        self.series_com = QScatterSeries()
        self.series_com.setMarkerSize(14)
        self.series_com.setColor(Qt.red)

        self.chart_complex = QChart()
        self.chart_complex.addSeries(self.series_complex)
        self.chart_complex.addSeries(self.series_com)
        self.chart_complex.createDefaultAxes()
        self.chart_complex.setTitle("Complex Winding")

        self.view_complex = QChartView(self.chart_complex, self)
        self.view_complex.setRenderHint(QPainter.Antialiasing)
        self.view_complex.setGeometry(620, 250, 550, 400)

    # ----- Slider -----
    def make_slider(self, y_pos, name, value):

        label = QLabel(f"{name}: {value}", self)
        label.move(20, y_pos)

        slider = QSlider(Qt.Horizontal, self)
        slider.setGeometry(120, y_pos, 300, 20)
        slider.setMinimum(1)
        slider.setMaximum(200)
        slider.setValue(int(value))

        slider.valueChanged.connect(
            lambda val, n=name, l=label: self.update_value(n, val, l)
        )

        return slider

    def update_value(self, name, val, label):

        label.setText(f"{name}: {val}")

        if name == "Winding ω":
            self.w = val

        self.update_plot()

    # ----- File Loader -----
    def load_file(self):

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Spreadsheet",
            "",
            "Spreadsheet (*.csv *.xlsx)"
        )

        if not file_name:
            return

        self.file_label.setText(file_name.split("/")[-1])

        try:

            if file_name.endswith(".csv"):
                df = pd.read_csv(file_name, header=None)

            else:
                df = pd.read_excel(file_name, header=None)

            # First two rows
            time_row = df.iloc[0].dropna().values
            value_row = df.iloc[1].dropna().values

            self.t = np.array(time_row, dtype=float)
            self.y = np.array(value_row, dtype=float)

            self.update_plot()

        except Exception as e:

            self.file_label.setText("Error loading file")

    # ----- Fourier Visualization -----
    def update_plot(self):

        if len(self.t) == 0:
            return

        # Time plot
        time_points = [QPointF(self.t[i], self.y[i]) for i in range(len(self.t))]
        self.series_time.replace(time_points)

        self.chart_time.axes(Qt.Horizontal)[0].setRange(min(self.t), max(self.t))

        # Complex winding
        complex_signal = self.y * np.exp(-1j * self.w * self.t)

        real = np.real(complex_signal)
        imag = np.imag(complex_signal)

        complex_points = [QPointF(real[i], imag[i]) for i in range(len(real))]
        self.series_complex.replace(complex_points)

        # Center of Mass
        com = np.mean(complex_signal)

        com_real = np.real(com)
        com_imag = np.imag(com)
        magnitude = np.abs(com)

        self.series_com.replace([QPointF(com_real, com_imag)])

        self.com_label.setText(
            f"Center of Mass: ({com_real:.4f} , {com_imag:.4f})"
        )

        self.mag_label.setText(
            f"Magnitude |COM|: {magnitude:.4f}"
        )

        max_val = max(np.max(np.abs(real)), np.max(np.abs(imag))) + 0.5
        max_val = max(max_val, 1.5)

        self.chart_complex.axes(Qt.Horizontal)[0].setRange(-max_val, max_val)
        self.chart_complex.axes(Qt.Vertical)[0].setRange(-max_val, max_val)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MyWindow()
    window.show()

    sys.exit(app.exec())
