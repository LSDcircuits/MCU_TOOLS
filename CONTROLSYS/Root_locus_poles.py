# root_locus_interactive.py - Interactive Root Locus Plotter
# Uses PySide6 for GUI and matplotlib for plotting

import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QSlider, QGroupBox,
    QGridLayout, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart, QChartView, QScatterSeries, QLineSeries
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class RootLocusPlotter(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Interactive Root Locus Plotter")
        self.setFixedSize(1000, 800)
        
        # Current poles and zeros
        self.poles = []
        self.zeros = []
        self.current_K = 0
        
        # History of root locus points
        self.root_locus_points = []
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QGroupBox("System Configuration")
        left_layout = QVBoxLayout()
        
        # Pole input section
        pole_group = QGroupBox("Add Poles (Real, Imaginary)")
        pole_layout = QGridLayout()
        
        self.pole_real = QLineEdit()
        self.pole_real.setPlaceholderText("Real part")
        self.pole_imag = QLineEdit()
        self.pole_imag.setPlaceholderText("Imaginary part")
        self.pole_imag.setText("0")
        
        btn_add_pole = QPushButton("Add Pole")
        btn_add_pole.clicked.connect(self.add_pole)
        
        pole_layout.addWidget(QLabel("Real:"), 0, 0)
        pole_layout.addWidget(self.pole_real, 0, 1)
        pole_layout.addWidget(QLabel("Imag:"), 1, 0)
        pole_layout.addWidget(self.pole_imag, 1, 1)
        pole_layout.addWidget(btn_add_pole, 2, 0, 1, 2)
        
        pole_group.setLayout(pole_layout)
        left_layout.addWidget(pole_group)
        
        # Zero input section
        zero_group = QGroupBox("Add Zeros (Real, Imaginary)")
        zero_layout = QGridLayout()
        
        self.zero_real = QLineEdit()
        self.zero_real.setPlaceholderText("Real part")
        self.zero_imag = QLineEdit()
        self.zero_imag.setPlaceholderText("Imaginary part")
        self.zero_imag.setText("0")
        
        btn_add_zero = QPushButton("Add Zero")
        btn_add_zero.clicked.connect(self.add_zero)
        
        zero_layout.addWidget(QLabel("Real:"), 0, 0)
        zero_layout.addWidget(self.zero_real, 0, 1)
        zero_layout.addWidget(QLabel("Imag:"), 1, 0)
        zero_layout.addWidget(self.zero_imag, 1, 1)
        zero_layout.addWidget(btn_add_zero, 2, 0, 1, 2)
        
        zero_group.setLayout(zero_layout)
        left_layout.addWidget(zero_group)
        
        # Preset systems
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "2 Real Poles (s+1)(s+2)",
            "2 Poles 1 Zero - Circle",
            "3 Poles - Asymptotes",
            "Complex Poles - Oscillatory",
            "Double Integrator",
            "PID-like: 2P + 2Z"
        ])
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        
        preset_layout.addWidget(self.preset_combo)
        preset_group.setLayout(preset_layout)
        left_layout.addWidget(preset_group)
        
        # Current system display
        self.system_label = QLabel("System: G(s) = 1")
        self.system_label.setWordWrap(True)
        self.system_label.setStyleSheet("font-weight: bold; color: blue;")
        left_layout.addWidget(self.system_label)
        
        # List of poles/zeros
        self.pz_list = QLabel("Poles: []\nZeros: []")
        self.pz_list.setWordWrap(True)
        left_layout.addWidget(self.pz_list)
        
        # Clear buttons
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all)
        left_layout.addWidget(btn_clear)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(250)
        
        # Right panel - Plot and controls
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.setup_plot()
        
        right_layout.addWidget(self.canvas)
        
        # K value slider
        slider_group = QGroupBox("Gain K Control")
        slider_layout = QVBoxLayout()
        
        self.K_slider = QSlider(Qt.Horizontal)
        self.K_slider.setMinimum(0)
        self.K_slider.setMaximum(1000)
        self.K_slider.setValue(0)
        self.K_slider.valueChanged.connect(self.K_changed)
        
        self.K_label = QLabel("K = 0.00")
        self.K_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # K value input
        K_input_layout = QHBoxLayout()
        self.K_input = QLineEdit("0")
        self.K_input.setFixedWidth(80)
        btn_set_K = QPushButton("Set K")
        btn_set_K.clicked.connect(self.set_K_from_input)
        
        K_input_layout.addWidget(QLabel("Manual K:"))
        K_input_layout.addWidget(self.K_input)
        K_input_layout.addWidget(btn_set_K)
        K_input_layout.addStretch()
        
        slider_layout.addWidget(self.K_label)
        slider_layout.addWidget(self.K_slider)
        slider_layout.addLayout(K_input_layout)
        
        # Info display
        self.info_label = QLabel("Closed-loop poles will appear here")
        self.info_label.setStyleSheet("font-family: monospace;")
        slider_layout.addWidget(self.info_label)
        
        slider_group.setLayout(slider_layout)
        right_layout.addWidget(slider_group)
        
        # Generate root locus button
        btn_generate = QPushButton("Generate Full Root Locus")
        btn_generate.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        btn_generate.clicked.connect(self.generate_root_locus)
        right_layout.addWidget(btn_generate)
        
        right_panel.setLayout(right_layout)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        self.setLayout(main_layout)
        
    def setup_plot(self):
        self.ax.clear()
        self.ax.axhline(y=0, color='k', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linewidth=0.5)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('Real Axis')
        self.ax.set_ylabel('Imaginary Axis')
        self.ax.set_title('Root Locus Plot\nDrag slider to see pole movement')
        
        # Set equal aspect ratio and reasonable limits
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_aspect('equal')
        
        self.canvas.draw()
        
    def add_pole(self):
        try:
            real = float(self.pole_real.text())
            imag = float(self.pole_imag.text())
            self.poles.append(complex(real, imag))
            self.poles.append(complex(real, -imag)) if imag != 0 else None
            if imag != 0 and complex(real, -imag) not in self.poles:
                self.poles.append(complex(real, -imag))
            self.update_system_display()
            self.pole_real.clear()
            self.pole_imag.setText("0")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numbers")
            
    def add_zero(self):
        try:
            real = float(self.zero_real.text())
            imag = float(self.zero_imag.text())
            self.zeros.append(complex(real, imag))
            if imag != 0 and complex(real, -imag) not in self.zeros:
                self.zeros.append(complex(real, -imag))
            self.update_system_display()
            self.zero_real.clear()
            self.zero_imag.setText("0")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numbers")
            
    def clear_all(self):
        self.poles = []
        self.zeros = []
        self.root_locus_points = []
        self.current_K = 0
        self.K_slider.setValue(0)
        self.update_system_display()
        self.setup_plot()
        
    def update_system_display(self):
        # Remove duplicates while preserving order
        self.poles = list(dict.fromkeys(self.poles))
        self.zeros = list(dict.fromkeys(self.zeros))
        
        # Build transfer function string
        num_str = ""
        if self.zeros:
            terms = []
            for z in self.zeros:
                if z.imag == 0:
                    if z.real == 0:
                        terms.append("s")
                    else:
                        terms.append(f"(s{self._format_num(-z.real)})")
                else:
                    terms.append(f"(s²{self._format_num(2*z.real)}s{self._format_num(abs(z)**2)})")
            num_str = "".join(terms)
        else:
            num_str = "1"
            
        den_str = ""
        if self.poles:
            terms = []
            for p in self.poles:
                if p.imag == 0:
                    if p.real == 0:
                        terms.append("s")
                    else:
                        terms.append(f"(s{self._format_num(-p.real)})")
                else:
                    terms.append(f"(s²{self._format_num(2*p.real)}s{self._format_num(abs(p)**2)})")
            den_str = "".join(terms)
        else:
            den_str = "1"
            
        self.system_label.setText(f"G(s) = K·{num_str} / {den_str}")
        self.pz_list.setText(f"Poles: {[f'({p.real:.2f}{p.imag:+.2f}j)' for p in self.poles]}\n"
                            f"Zeros: {[f'({z.real:.2f}{z.imag:+.2f}j)' for z in self.zeros]}")
        
        self.plot_current_state()
        
    def _format_num(self, x):
        if abs(x) < 0.001:
            return ""
        sign = "+" if x < 0 else "-"
        return f"{sign}{abs(x):.2f}"
        
    def K_changed(self):
        self.current_K = self.K_slider.value() / 10.0
        self.K_label.setText(f"K = {self.current_K:.2f}")
        self.K_input.setText(f"{self.current_K:.2f}")
        self.plot_current_state()
        
    def set_K_from_input(self):
        try:
            K = float(self.K_input.text())
            self.K_slider.setValue(int(K * 10))
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid number")
            
    def calculate_closed_loop_poles(self, K):
        """Calculate closed-loop poles for a given K"""
        if not self.poles:
            return []
            
        # Build characteristic equation: 1 + K*G(s) = 0
        # Den(G) + K*Num(G) = 0
        
        # Get polynomial coefficients from poles and zeros
        den_coef = self._poles_to_polynomial(self.poles)
        num_coef = self._poles_to_polynomial(self.zeros) if self.zeros else [1]
        
        # Pad numerator to match denominator degree
        while len(num_coef) < len(den_coef):
            num_coef = [0] + num_coef
            
        # Characteristic polynomial: den + K*num = 0
        char_poly = [d + K*n for d, n in zip(den_coef, num_coef)]
        
        # Find roots
        roots = np.roots(char_poly)
        return roots
        
    def _poles_to_polynomial(self, roots):
        """Convert roots to polynomial coefficients"""
        if not roots:
            return [1]
        coef = [1]
        for r in roots:
            # (s - r) = s - r
            new_coef = [0] * (len(coef) + 1)
            for i, c in enumerate(coef):
                new_coef[i] += c
                new_coef[i+1] += -r * c
            coef = new_coef
        return [c.real for c in coef]  # Should be real for conjugate pairs
        
    def plot_current_state(self):
        self.ax.clear()
        self.setup_plot()
        
        # Plot axes
        self.ax.axhline(y=0, color='k', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linewidth=0.5)
        
        # Plot asymptotes if needed
        n_poles = len(self.poles)
        n_zeros = len(self.zeros)
        if n_poles > n_zeros:
            self.plot_asymptotes()
        
        # Plot root locus history
        if self.root_locus_points:
            all_points = np.array(self.root_locus_points)
            for i in range(all_points.shape[1]):
                points = all_points[:, i]
                real_parts = [p.real for p in points]
                imag_parts = [p.imag for p in points]
                self.ax.plot(real_parts, imag_parts, 'b-', alpha=0.3, linewidth=1)
        
        # Plot open-loop poles (x)
        for p in self.poles:
            self.ax.plot(p.real, p.imag, 'rx', markersize=12, markeredgewidth=2, 
                        label='Open-loop pole' if p == self.poles[0] else "")
            
        # Plot open-loop zeros (o)
        for z in self.zeros:
            self.ax.plot(z.real, z.imag, 'ro', markersize=10, markerfacecolor='none', 
                        markeredgewidth=2, label='Open-loop zero' if z == self.zeros[0] else "")
        
        # Plot closed-loop poles for current K
        if self.poles:
            cl_poles = self.calculate_closed_loop_poles(self.current_K)
            
            # Color based on stability
            for p in cl_poles:
                color = 'green' if p.real < 0 else 'red'
                marker = 's' if p.real < 0 else '^'
                self.ax.plot(p.real, p.imag, color=color, marker=marker, 
                           markersize=10, alpha=0.8, 
                           label='Stable CL pole' if p.real < 0 and p == cl_poles[0] else 
                                 'Unstable CL pole' if p.real >= 0 and p == cl_poles[0] else "")
            
            # Update info
            pole_strs = []
            for p in sorted(cl_poles, key=lambda x: (x.real, x.imag)):
                stability = "STABLE" if p.real < 0 else "UNSTABLE"
                pole_strs.append(f"{p.real:.3f}{p.imag:+.3f}j ({stability})")
            self.info_label.setText(f"K={self.current_K:.2f}:\n" + "\n".join(pole_strs))
        
        self.ax.legend(loc='upper right', fontsize=8)
        self.canvas.draw()
        
    def plot_asymptotes(self):
        """Plot asymptotes for root locus"""
        n_poles = len(self.poles)
        n_zeros = len(self.zeros)
        
        if n_poles <= n_zeros:
            return
            
        # Centroid
        sum_poles = sum(p.real for p in self.poles)
        sum_zeros = sum(z.real for z in self.zeros) if self.zeros else 0
        centroid = (sum_poles - sum_zeros) / (n_poles - n_zeros)
        
        # Asymptote angles
        angles = [(2*k + 1) * 180 / (n_poles - n_zeros) for k in range(n_poles - n_zeros)]
        
        # Plot asymptotes as dashed lines
        for angle in angles:
            rad = np.deg2rad(angle)
            # Line from centroid outward
            t = np.linspace(0, 20, 100)
            x = centroid + t * np.cos(rad)
            y = t * np.sin(rad)
            self.ax.plot(x, y, 'g--', alpha=0.5, linewidth=1)
            self.ax.plot(x, -y, 'g--', alpha=0.5, linewidth=1)
            
        # Mark centroid
        self.ax.plot(centroid, 0, 'g+', markersize=10, markeredgewidth=2, label='Centroid')
        
    def generate_root_locus(self):
        """Generate the full root locus by varying K"""
        if not self.poles:
            QMessageBox.warning(self, "Error", "Add poles first!")
            return
            
        self.root_locus_points = []
        
        # Use logarithmic scale for K to get better resolution at low K
        K_values = np.concatenate([
            np.linspace(0, 1, 100),
            np.linspace(1, 10, 100),
            np.linspace(10, 100, 100),
            np.linspace(100, 1000, 100)
        ])
        
        for K in K_values:
            poles = self.calculate_closed_loop_poles(K)
            self.root_locus_points.append(poles)
            
        self.plot_current_state()
        QMessageBox.information(self, "Done", f"Generated root locus with {len(K_values)} points!")
        
    def load_preset(self, index):
        presets = {
            1: ([-1, -2], []),  # 2 Real poles
            2: ([0, -2], [-4]),  # 2 poles 1 zero - circle
            3: ([0, -1, -2], []),  # 3 poles - asymptotes
            4: ([-1+2j, -1-2j], []),  # Complex poles
            5: ([0, 0], []),  # Double integrator
            6: ([0, -3, -6], [-1, -2]),  # PID-like
        }
        
        if index in presets:
            self.clear_all()
            poles, zeros = presets[index]
            self.poles = [complex(p) if isinstance(p, (int, float)) else p for p in poles]
            self.zeros = [complex(z) if isinstance(z, (int, float)) else z for z in zeros]
            self.update_system_display()
            self.generate_root_locus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set style
    app.setStyle('Fusion')
    
    window = RootLocusPlotter()
    window.show()
    sys.exit(app.exec())
