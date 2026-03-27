import sys
import math
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, 
    QLabel, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QTabWidget, QTextEdit, QSplitter
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen


class LandingGearAnalysis(QWidget):
    def __init__(self):
        super().__init__()

        # ---- Window setup ----
        self.setWindowTitle("Aircraft Landing Gear Analysis - Mass-Spring-Damper System")
        self.resize(1400, 1000)  # Much larger window

        # Main layout
        main_layout = QVBoxLayout(self)

        # ---- Input Section ----
        input_group = QGroupBox("System Parameters (2-DOF Landing Gear Model)")
        input_layout = QVBoxLayout()

        # Aircraft mass (m1)
        m1_layout = QHBoxLayout()
        m1_layout.addWidget(QLabel("Aircraft Mass m₁ (kg):"))
        self.input_m1 = QLineEdit()
        self.input_m1.setPlaceholderText("e.g., 5000")
        self.input_m1.setText("5000")
        m1_layout.addWidget(self.input_m1)
        input_layout.addLayout(m1_layout)

        # Landing gear mass (m2)
        m2_layout = QHBoxLayout()
        m2_layout.addWidget(QLabel("Landing Gear Mass m₂ (kg):"))
        self.input_m2 = QLineEdit()
        self.input_m2.setPlaceholderText("e.g., 500")
        self.input_m2.setText("500")
        m2_layout.addWidget(self.input_m2)
        input_layout.addLayout(m2_layout)

        # Shock absorber spring constant (k1)
        k1_layout = QHBoxLayout()
        k1_layout.addWidget(QLabel("Shock Absorber Stiffness k₁ (N/m):"))
        self.input_k1 = QLineEdit()
        self.input_k1.setPlaceholderText("e.g., 500000")
        self.input_k1.setText("500000")
        k1_layout.addWidget(self.input_k1)
        input_layout.addLayout(k1_layout)

        # Tire spring constant (k2)
        k2_layout = QHBoxLayout()
        k2_layout.addWidget(QLabel("Tire Stiffness k₂ (N/m):"))
        self.input_k2 = QLineEdit()
        self.input_k2.setPlaceholderText("e.g., 2000000")
        self.input_k2.setText("2000000")
        k2_layout.addWidget(self.input_k2)
        input_layout.addLayout(k2_layout)

        # Damping coefficient (b)
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Damping Coefficient b (Ns/m):"))
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("e.g., 50000 (or leave blank to calculate)")
        self.input_b.setText("50000")
        b_layout.addWidget(self.input_b)
        input_layout.addLayout(b_layout)

        # Impact velocity
        force_layout = QHBoxLayout()
        force_layout.addWidget(QLabel("Impact Velocity V (m/s):"))
        self.input_v = QLineEdit()
        self.input_v.setPlaceholderText("e.g., 3.0")
        self.input_v.setText("3.0")
        force_layout.addWidget(self.input_v)
        input_layout.addLayout(force_layout)

        # Analysis type selection
        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel("Analysis Type:"))
        self.analysis_type = QComboBox()
        self.analysis_type.addItems([
            "Time Response (Given b)",
            "Find Critical Damping",
            "Find Damping for Max Displacement",
            "Frequency Response"
        ])
        analysis_layout.addWidget(self.analysis_type)
        input_layout.addLayout(analysis_layout)

        # Calculate button
        self.btn_calculate = QPushButton("Calculate & Plot")
        self.btn_calculate.setMinimumHeight(40)
        self.btn_calculate.clicked.connect(self.calculate_and_plot)
        input_layout.addWidget(self.btn_calculate)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # ---- Results Display ----
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(120)
        self.results_text.setMaximumHeight(180)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # ---- Charts Section ----
        charts_group = QGroupBox("Response Plots")
        charts_layout = QVBoxLayout()  # Vertical stack for larger plots

        # Create splitter for resizable charts
        splitter = QSplitter(Qt.Vertical)

        # Displacement plot - MUCH LARGER
        self.disp_chart = QChart()
        self.disp_chart.setTitle("Displacement Response")
        self.disp_chart.setTitleFont(self.font())
        self.disp_chart.titleFont().setPointSize(14)
        self.disp_chart.titleFont().setBold(True)
        
        self.disp_series_m1 = QLineSeries()
        self.disp_series_m1.setName("Aircraft (m₁)")
        pen1 = QPen(QColor(255, 0, 0))
        pen1.setWidth(3)  # Thicker line
        self.disp_series_m1.setPen(pen1)
        
        self.disp_series_m2 = QLineSeries()
        self.disp_series_m2.setName("Landing Gear (m₂)")
        pen2 = QPen(QColor(0, 0, 255))
        pen2.setWidth(3)  # Thicker line
        self.disp_series_m2.setPen(pen2)

        self.disp_chart.addSeries(self.disp_series_m1)
        self.disp_chart.addSeries(self.disp_series_m2)
        self.disp_chart.createDefaultAxes()
        
        # Make axes labels larger
        axis_x = self.disp_chart.axisX()
        axis_y = self.disp_chart.axisY()
        axis_x.setTitleText("Time (s)")
        axis_y.setTitleText("Displacement (m)")
        axis_x.setTitleFont(self.font())
        axis_y.setTitleFont(self.font())
        axis_x.setLabelsFont(self.font())
        axis_y.setLabelsFont(self.font())

        self.disp_chart_view = QChartView(self.disp_chart)
        self.disp_chart_view.setRenderHint(self.disp_chart_view.renderHints())
        self.disp_chart_view.setMinimumHeight(350)  # Much taller
        
        splitter.addWidget(self.disp_chart_view)

        # Velocity plot - MUCH LARGER
        self.vel_chart = QChart()
        self.vel_chart.setTitle("Velocity Response")
        self.vel_chart.setTitleFont(self.font())
        self.vel_chart.titleFont().setPointSize(14)
        self.vel_chart.titleFont().setBold(True)
        
        self.vel_series_m1 = QLineSeries()
        self.vel_series_m1.setName("Aircraft (m₁)")
        self.vel_series_m1.setPen(pen1)
        
        self.vel_series_m2 = QLineSeries()
        self.vel_series_m2.setName("Landing Gear (m₂)")
        self.vel_series_m2.setPen(pen2)

        self.vel_chart.addSeries(self.vel_series_m1)
        self.vel_chart.addSeries(self.vel_series_m2)
        self.vel_chart.createDefaultAxes()
        
        axis_x2 = self.vel_chart.axisX()
        axis_y2 = self.vel_chart.axisY()
        axis_x2.setTitleText("Time (s)")
        axis_y2.setTitleText("Velocity (m/s)")
        axis_x2.setTitleFont(self.font())
        axis_y2.setTitleFont(self.font())
        axis_x2.setLabelsFont(self.font())
        axis_y2.setLabelsFont(self.font())

        self.vel_chart_view = QChartView(self.vel_chart)
        self.vel_chart_view.setRenderHint(self.vel_chart_view.renderHints())
        self.vel_chart_view.setMinimumHeight(350)  # Much taller
        
        splitter.addWidget(self.vel_chart_view)
        
        charts_layout.addWidget(splitter)
        charts_group.setLayout(charts_layout)
        main_layout.addWidget(charts_group, stretch=1)  # Give charts stretch priority

        self.setLayout(main_layout)

    def calculate_and_plot(self):
        try:
            # Get input values
            m1 = float(self.input_m1.text())
            m2 = float(self.input_m2.text())
            k1 = float(self.input_k1.text())
            k2 = float(self.input_k2.text())
            v_impact = float(self.input_v.text())
            
            b_input = self.input_b.text()
            b = float(b_input) if b_input else None

            analysis = self.analysis_type.currentText()

            # Clear previous series
            self.disp_series_m1.clear()
            self.disp_series_m2.clear()
            self.vel_series_m1.clear()
            self.vel_series_m2.clear()

            results = []

            if analysis == "Time Response (Given b)":
                if b is None:
                    self.results_text.setText("Error: Please provide damping coefficient b")
                    return
                results = self.time_response_analysis(m1, m2, k1, k2, b, v_impact)

            elif analysis == "Find Critical Damping":
                results = self.find_critical_damping(m1, m2, k1, k2, v_impact)

            elif analysis == "Find Damping for Max Displacement":
                results = self.find_optimal_damping(m1, m2, k1, k2, v_impact)

            elif analysis == "Frequency Response":
                if b is None:
                    self.results_text.setText("Error: Please provide damping coefficient b")
                    return
                results = self.frequency_response(m1, m2, k1, k2, b)

            self.results_text.setText("\n".join(results))

        except ValueError as e:
            self.results_text.setText(f"Invalid input: {str(e)}\nPlease enter numeric values.")

    def time_response_analysis(self, m1, m2, k1, k2, b, v_impact):
        """Solve the 2-DOF system and plot time response"""
        
        M = np.array([[m1, 0], [0, m2]])
        K = np.array([[k1, -k1], [-k1, k1 + k2]])
        C = np.array([[b, -b], [-b, b]])
        
        Minv = np.linalg.inv(M)
        
        A = np.zeros((4, 4))
        A[0:2, 2:4] = np.eye(2)
        A[2:4, 0:2] = -Minv @ K
        A[2:4, 2:4] = -Minv @ C
        
        x0 = np.array([0, 0, v_impact, 0])
        
        dt = 0.001
        t_max = 2.0
        t = np.arange(0, t_max, dt)
        
        x = np.zeros((4, len(t)))
        x[:, 0] = x0
        
        for i in range(len(t) - 1):
            k1_rk = dt * (A @ x[:, i])
            k2_rk = dt * (A @ (x[:, i] + 0.5 * k1_rk))
            k3_rk = dt * (A @ (x[:, i] + 0.5 * k2_rk))
            k4_rk = dt * (A @ (x[:, i] + k3_rk))
            x[:, i+1] = x[:, i] + (k1_rk + 2*k2_rk + 2*k3_rk + k4_rk) / 6
        
        # Plot every 5th point for smoother curves
        plot_step = 5
        for i in range(0, len(t), plot_step):
            self.disp_series_m1.append(t[i], x[0, i])
            self.disp_series_m2.append(t[i], x[1, i])
            self.vel_series_m1.append(t[i], x[2, i])
            self.vel_series_m2.append(t[i], x[3, i])
        
        # Update axes with padding
        y_min_disp = min(np.min(x[0]), np.min(x[1])) * 1.1
        y_max_disp = max(np.max(x[0]), np.max(x[1])) * 1.1
        
        self.disp_chart.axisX().setRange(0, t_max)
        self.disp_chart.axisY().setRange(y_min_disp, y_max_disp)
        
        y_min_vel = min(np.min(x[2]), np.min(x[3])) * 1.1
        y_max_vel = max(np.max(x[2]), np.max(x[3])) * 1.1
        
        self.vel_chart.axisX().setRange(0, t_max)
        self.vel_chart.axisY().setRange(y_min_vel, y_max_vel)

        max_disp_m1 = np.max(np.abs(x[0]))
        max_disp_m2 = np.max(np.abs(x[1]))
        max_vel_m1 = np.max(np.abs(x[2]))
        max_vel_m2 = np.max(np.abs(x[3]))
        
        omega_n = np.sqrt(k1 / m1)
        zeta = b / (2 * np.sqrt(m1 * k1))
        
        results = [
            f"=== TIME RESPONSE ANALYSIS ===",
            f"Damping Coefficient b: {b:,.2f} Ns/m",
            f"Natural Frequency ωn: {omega_n:.2f} rad/s",
            f"Damping Ratio ζ: {zeta:.4f}",
            f"",
            f"Maximum Displacements:",
            f"  Aircraft (m₁): {max_disp_m1:.4f} m",
            f"  Landing Gear (m₂): {max_disp_m2:.4f} m",
            f"",
            f"Maximum Velocities:",
            f"  Aircraft (m₁): {max_vel_m1:.4f} m/s",
            f"  Landing Gear (m₂): {max_vel_m2:.4f} m/s",
            f"",
            f"System is {'Underdamped' if zeta < 1 else 'Critically Damped' if zeta == 1 else 'Overdamped'}"
        ]
        
        return results

    def find_critical_damping(self, m1, m2, k1, k2, v_impact):
        """Calculate critical damping for the system"""
        
        b_crit_1dof = 2 * np.sqrt(m1 * k1)
        
        M = np.array([[m1, 0], [0, m2]])
        K = np.array([[k1, -k1], [-k1, k1 + k2]])
        
        eigvals, eigvecs = np.linalg.eig(np.linalg.inv(M) @ K)
        omega_natural = np.sqrt(np.abs(eigvals))
        
        results = [
            f"=== CRITICAL DAMPING ANALYSIS ===",
            f"",
            f"1-DOF Approximation (Aircraft on shock absorber):",
            f"  Critical Damping b_crit = 2√(m₁k₁) = {b_crit_1dof:,.2f} Ns/m",
            f"",
            f"2-DOF System Natural Frequencies:",
            f"  Mode 1: {omega_natural[0]:.2f} rad/s ({omega_natural[0]/(2*np.pi):.2f} Hz)",
            f"  Mode 2: {omega_natural[1]:.2f} rad/s ({omega_natural[1]/(2*np.pi):.2f} Hz)",
            f"",
            f"Recommended Damping Range:",
            f"  Underdamped (oscillatory): b < {b_crit_1dof:,.0f} Ns/m",
            f"  Critically Damped: b ≈ {b_crit_1dof:,.0f} Ns/m",
            f"  Overdamped (slow return): b > {b_crit_1dof:,.0f} Ns/m",
            f"",
            f"For landing gear, typical design uses 0.3-0.7 of critical damping",
            f"Suggested range: {0.3*b_crit_1dof:,.0f} to {0.7*b_crit_1dof:,.0f} Ns/m"
        ]
        
        self.input_b.setText(f"{0.5*b_crit_1dof:.0f}")
        
        return results

    def find_optimal_damping(self, m1, m2, k1, k2, v_impact):
        """Find damping coefficient that minimizes maximum displacement"""
        
        results = [
            f"=== OPTIMAL DAMPING SEARCH ===",
            f"Searching for damping that minimizes peak displacement...",
            f""
        ]
        
        b_values = np.linspace(1000, 500000, 100)
        max_disps = []
        
        M = np.array([[m1, 0], [0, m2]])
        K = np.array([[k1, -k1], [-k1, k1 + k2]])
        Minv = np.linalg.inv(M)
        
        for b in b_values:
            C = np.array([[b, -b], [-b, b]])
            
            A = np.zeros((4, 4))
            A[0:2, 2:4] = np.eye(2)
            A[2:4, 0:2] = -Minv @ K
            A[2:4, 2:4] = -Minv @ C
            
            x0 = np.array([0, 0, v_impact, 0])
            
            dt = 0.001
            t_short = np.arange(0, 1.0, dt)
            x = x0
            
            max_d = 0
            for i in range(len(t_short)):
                k1_rk = dt * (A @ x)
                k2_rk = dt * (A @ (x + 0.5 * k1_rk))
                k3_rk = dt * (A @ (x + 0.5 * k2_rk))
                k4_rk = dt * (A @ (x + k3_rk))
                x = x + (k1_rk + 2*k2_rk + 2*k3_rk + k4_rk) / 6
                max_d = max(max_d, abs(x[0]))
            
            max_disps.append(max_d)
        
        optimal_idx = np.argmin(max_disps)
        b_optimal = b_values[optimal_idx]
        min_disp = max_disps[optimal_idx]
        
        self.disp_series_m1.clear()
        self.disp_series_m2.clear()
        
        for i in range(0, len(b_values), 5):
            self.disp_series_m1.append(b_values[i], max_disps[i])
        
        self.disp_chart.axisX().setRange(0, max(b_values))
        self.disp_chart.axisY().setRange(0, max(max_disps) * 1.1)
        self.disp_chart.setTitle("Max Displacement vs Damping Coefficient")
        self.disp_chart.axisX().setTitleText("Damping b (Ns/m)")
        self.disp_chart.axisY().setTitleText("Max Displacement (m)")
        
        self.vel_series_m1.clear()
        self.vel_series_m2.clear()

        results.extend([
            f"Optimal Damping Coefficient: {b_optimal:,.2f} Ns/m",
            f"Minimum Peak Displacement: {min_disp:.4f} m",
            f"",
            f"Damping Ratio at Optimal: {b_optimal/(2*np.sqrt(m1*k1)):.4f}",
            f"",
            f"Note: Lower damping reduces initial force but increases oscillation.",
            f"Higher damping increases initial force but reduces rebound."
        ])
        
        self.input_b.setText(f"{b_optimal:.0f}")
        
        return results

    def frequency_response(self, m1, m2, k1, k2, b):
        """Calculate frequency response of the system"""
        
        frequencies = np.logspace(-1, 2, 500)
        omega = 2 * np.pi * frequencies
        
        M = np.array([[m1, 0], [0, m2]])
        K = np.array([[k1, -k1], [-k1, k1 + k2]])
        
        H = []
        
        for w in omega:
            C = np.array([[b, -b], [-b, b]])
            Z = K - w**2 * M + 1j * w * C
            H_matrix = np.linalg.inv(Z)
            H.append(abs(H_matrix[0, 0]))
        
        H = np.array(H)
        
        self.disp_series_m1.clear()
        self.disp_series_m2.clear()
        
        for i in range(len(frequencies)):
            self.disp_series_m1.append(frequencies[i], 20*np.log10(H[i] + 1e-10))
        
        self.disp_chart.axisX().setRange(min(frequencies), max(frequencies))
        self.disp_chart.axisY().setRange(min(20*np.log10(H + 1e-10)) * 1.1, 
                                         max(20*np.log10(H + 1e-10)) * 1.1)
        self.disp_chart.setTitle("Frequency Response (Bode Magnitude)")
        self.disp_chart.axisX().setTitleText("Frequency (Hz)")
        self.disp_chart.axisY().setTitleText("Magnitude (dB)")
        
        self.vel_series_m1.clear()
        self.vel_series_m2.clear()

        peak_idx = np.argmax(H)
        f_resonant = frequencies[peak_idx]
        
        results = [
            f"=== FREQUENCY RESPONSE ANALYSIS ===",
            f"Damping Coefficient b: {b:,.2f} Ns/m",
            f"",
            f"Resonant Frequency: {f_resonant:.2f} Hz",
            f"Peak Magnitude: {20*np.log10(H[peak_idx]):.2f} dB",
            f"",
            f"Static Displacement (F/k): {1/k1:.6f} m/N",
            f"",
            f"Isolation Frequency (>√2×fn): {np.sqrt(2)*f_resonant:.2f} Hz",
            f"Above this frequency, the system provides vibration isolation."
        ]
        
        return results


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LandingGearAnalysis()
    window.show()
    sys.exit(app.exec())
