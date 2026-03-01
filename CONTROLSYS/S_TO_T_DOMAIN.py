import sys
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SDomainViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("S-Domain ↔ Real-Domain Visualizer")
        self.setMinimumSize(1000, 500)

        # ---- Main layout ----
        main_layout = QVBoxLayout(self)

        # ---- Plot area ----
        plot_layout = QHBoxLayout()
        main_layout.addLayout(plot_layout)

        self.fig = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        plot_layout.addWidget(self.canvas)

        self.ax_s = self.fig.add_subplot(1, 2, 1)
        self.ax_t = self.fig.add_subplot(1, 2, 2)

        # ---- Sliders ----
        slider_layout = QVBoxLayout()
        main_layout.addLayout(slider_layout)

        # σ slider
        self.sigma_label = QLabel("σ = -0.2")
        slider_layout.addWidget(self.sigma_label)

        self.sigma_slider = QSlider(Qt.Horizontal)
        self.sigma_slider.setRange(-200, 200)  # scaled by 100
        self.sigma_slider.setValue(-20)
        slider_layout.addWidget(self.sigma_slider)

        # ω slider
        self.omega_label = QLabel("ω = 5")
        slider_layout.addWidget(self.omega_label)

        self.omega_slider = QSlider(Qt.Horizontal)
        self.omega_slider.setRange(-1000, 1000)  # scaled by 100
        self.omega_slider.setValue(500)
        slider_layout.addWidget(self.omega_slider)

        # ---- Connect sliders ----
        self.sigma_slider.valueChanged.connect(self.update_plot)
        self.omega_slider.valueChanged.connect(self.update_plot)

        self.update_plot()

    def update_plot(self):
        sigma = self.sigma_slider.value() / 100
        omega = self.omega_slider.value() / 100

        self.sigma_label.setText(f"σ = {sigma:.2f}")
        self.omega_label.setText(f"ω = {omega:.2f}")

        t = np.linspace(0, 10, 1000)
        y = np.exp(sigma * t) * np.cos(omega * t)

        # ---- S-domain plot ----
        self.ax_s.clear()
        self.ax_s.set_title("S Domain")
        self.ax_s.set_xlabel("σ (Real)")
        self.ax_s.set_ylabel("jω (Imag)")
        self.ax_s.set_xlim(-2, 2)
        self.ax_s.set_ylim(-10, 10)
        self.ax_s.grid(True)

        self.ax_s.plot(sigma, omega, 'ro', markersize=10)

        # ---- Time-domain plot ----
        self.ax_t.clear()
        self.ax_t.set_title("Real Domain Response")
        self.ax_t.set_xlabel("Time")
        self.ax_t.set_ylabel("y(t)")
        self.ax_t.plot(t, y)

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SDomainViewer()
    window.show()
    sys.exit(app.exec())
