import sys
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RootLocusViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Root Locus Visualizer")
        self.setMinimumSize(1000, 600)

        # Example open-loop poles
        self.p1 = -1
        self.p2 = -3

        # ---- Layout ----
        main_layout = QVBoxLayout(self)

        self.fig = Figure(figsize=(6, 6))
        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas)

        self.ax = self.fig.add_subplot(111)

        # ---- Gain Slider ----
        self.k_label = QLabel("Gain K = 1.0")
        main_layout.addWidget(self.k_label)

        self.k_slider = QSlider(Qt.Horizontal)
        self.k_slider.setRange(0, 1000)
        self.k_slider.setValue(100)
        main_layout.addWidget(self.k_slider)

        self.k_slider.valueChanged.connect(self.update_plot)

        self.update_plot()

    def compute_closed_loop_poles(self, K):
        """
        For:
            G(s) = K / [(s-p1)(s-p2)]

        Closed loop:
            (s-p1)(s-p2) + K = 0

        Expand:
            s² - (p1+p2)s + (p1*p2 + K) = 0
        """

        a = 1
        b = -(self.p1 + self.p2)
        c = self.p1 * self.p2 + K

        return np.roots([a, b, c])

    def compute_root_locus(self):
        K_values = np.linspace(0, 100, 400)
        locus = []

        for K in K_values:
            roots = self.compute_closed_loop_poles(K)
            locus.append(roots)

        return np.array(locus)

    def update_plot(self):
        K = self.k_slider.value() / 10
        self.k_label.setText(f"Gain K = {K:.2f}")

        self.ax.clear()

        # ---- Plot full root locus ----
        locus = self.compute_root_locus()

        for i in range(locus.shape[1]):
            self.ax.plot(locus[:, i].real, locus[:, i].imag, 'b')

        # ---- Current poles ----
        poles = self.compute_closed_loop_poles(K)
        self.ax.plot(poles.real, poles.imag, 'ro', markersize=10, label="Closed-loop poles")

        # ---- Open loop poles ----
        self.ax.plot([self.p1, self.p2], [0, 0], 'kx', markersize=10, label="Open-loop poles")

        # ---- Styling ----
        self.ax.axhline(0, color='black', linewidth=0.5)
        self.ax.axvline(0, color='black', linewidth=0.5)
        self.ax.grid(True)
        self.ax.set_title("Root Locus")
        self.ax.set_xlabel("Real Axis")
        self.ax.set_ylabel("Imag Axis")
        self.ax.legend()

        self.ax.set_xlim(-10, 5)
        self.ax.set_ylim(-10, 10)

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RootLocusViewer()
    window.show()
    sys.exit(app.exec())
