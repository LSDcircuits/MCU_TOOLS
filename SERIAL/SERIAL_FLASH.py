import os
import sys
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QMessageBox, QFileDialog,
    QLineEdit
)


# ---------------- Worker Threads ----------------
class CommandWorker(QThread):
    output = Signal(str)
    finished_ok = Signal(bool)

    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd

    def run(self):
        try:
            self.output.emit(f"$ {' '.join(self.command)}")
            process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                self.output.emit(line.rstrip())

            process.wait()
            self.finished_ok.emit(process.returncode == 0)

        except Exception as e:
            self.output.emit(f"[ERROR] {e}")
            self.finished_ok.emit(False)


# ---------------- Main App ----------------
class LPC845Flasher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LPC845 OpenOCD Flasher")
        self.setMinimumSize(800, 520)

        self.flash_worker = None

        self.init_ui()
        self.refresh_devices()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ---- Debug probe row ----
        probe_row = QHBoxLayout()
        probe_row.addWidget(QLabel("Connected Debug Device:"))

        self.device_combo = QComboBox()
        probe_row.addWidget(self.device_combo)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        probe_row.addWidget(self.refresh_btn)

        layout.addLayout(probe_row)

        # ---- Flash type row ----
        flash_row = QHBoxLayout()
        flash_row.addWidget(QLabel("Flash Type:"))

        self.flash_type_combo = QComboBox()
        self.flash_type_combo.addItems(["CMSIS-DAP", "J-Link"])
        flash_row.addWidget(self.flash_type_combo)

        layout.addLayout(flash_row)

        # ---- Project directory row ----
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Project Directory:"))

        self.project_dir_edit = QLineEdit()
        self.project_dir_edit.setPlaceholderText("Select your project root folder...")
        dir_row.addWidget(self.project_dir_edit)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.select_project_dir)
        dir_row.addWidget(self.browse_btn)

        layout.addLayout(dir_row)

        # ---- Firmware file row ----
        fw_row = QHBoxLayout()
        fw_row.addWidget(QLabel("Detected Firmware:"))

        self.firmware_edit = QLineEdit()
        self.firmware_edit.setReadOnly(True)
        fw_row.addWidget(self.firmware_edit)

        self.scan_btn = QPushButton("Scan Build")
        self.scan_btn.clicked.connect(self.scan_firmware)
        fw_row.addWidget(self.scan_btn)

        layout.addLayout(fw_row)

        # ---- Tool check row ----
        tool_row = QHBoxLayout()

        self.check_tools_btn = QPushButton("Check Tools")
        self.check_tools_btn.clicked.connect(self.check_tools)
        tool_row.addWidget(self.check_tools_btn)

        self.flash_btn = QPushButton("Flash")
        self.flash_btn.clicked.connect(self.flash_firmware)
        tool_row.addWidget(self.flash_btn)

        layout.addLayout(tool_row)

        # ---- Output ----
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    # ---------------- UI Helpers ----------------
    def log(self, text):
        self.output.append(text)

    def select_project_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            self.project_dir_edit.setText(directory)
            self.scan_firmware()

    # ---------------- Device Detection ----------------
    def refresh_devices(self):
        self.device_combo.clear()

        devices = self.detect_debug_devices()

        if not devices:
            self.device_combo.addItem("No supported debug probes found")
        else:
            for dev in devices:
                self.device_combo.addItem(dev)

        self.log("[INFO] Device list refreshed")

    def detect_debug_devices(self):
        """
        On macOS, parse 'system_profiler SPUSBDataType' and look for common
        debug probes such as CMSIS-DAP, J-Link, LPC-Link, ST-Link.
        """
        keywords = [
            "cmsis-dap",
            "j-link",
            "jlink",
            "lpc-link",
            "daplink",
            "st-link",
            "segger",
            "mbed"
        ]

        found = []

        try:
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                check=False
            )
            text = result.stdout.splitlines()

            current_block = []
            for line in text:
                if line.strip() == "":
                    if current_block:
                        block_text = "\n".join(current_block).lower()
                        if any(k in block_text for k in keywords):
                            # Try to extract a readable device name
                            pretty_name = current_block[0].strip().rstrip(":")
                            found.append(pretty_name)
                        current_block = []
                else:
                    current_block.append(line)

            # Final block
            if current_block:
                block_text = "\n".join(current_block).lower()
                if any(k in block_text for k in keywords):
                    pretty_name = current_block[0].strip().rstrip(":")
                    found.append(pretty_name)

        except Exception as e:
            self.log(f"[ERROR] Could not scan USB devices: {e}")

        # Remove duplicates while preserving order
        unique = []
        for item in found:
            if item not in unique:
                unique.append(item)

        return unique

    # ---------------- Tool Checking ----------------
    def check_tools(self):
        self.log("[INFO] Checking required tools...")

        self.run_simple_check(["arm-none-eabi-gcc", "--version"], "arm-none-eabi-gcc")
        self.run_simple_check(["openocd", "--version"], "openocd")

    def run_simple_check(self, command, tool_name):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
                self.log(f"[OK] {tool_name}: {first_line}")
            else:
                err = result.stderr.strip() if result.stderr else "not found"
                self.log(f"[ERROR] {tool_name}: {err}")

        except FileNotFoundError:
            self.log(f"[ERROR] {tool_name} is not installed or not in PATH")
        except Exception as e:
            self.log(f"[ERROR] Failed checking {tool_name}: {e}")

    # ---------------- Firmware Detection ----------------
    def scan_firmware(self):
        project_dir = self.project_dir_edit.text().strip()
        if not project_dir:
            self.firmware_edit.setText("")
            return

        firmware = self.find_firmware_file(project_dir)
        if firmware:
            self.firmware_edit.setText(str(firmware))
            self.log(f"[INFO] Found firmware: {firmware}")
        else:
            self.firmware_edit.setText("")
            self.log("[WARN] No firmware found in project/build directory")

    def find_firmware_file(self, project_dir):
        """
        Prefer ELF-like executable with no extension or .elf.
        Fall back to .bin if needed.
        """
        project_path = Path(project_dir)
        build_dir = project_path / "build"

        if not build_dir.exists():
            return None

        # 1) Prefer exact known project target if present
        preferred_names = [
            "lpc845_project",
            "lpc845_project.elf",
            "firmware.elf",
            "firmware",
        ]

        for name in preferred_names:
            candidate = build_dir / name
            if candidate.exists() and candidate.is_file():
                return candidate

        # 2) Search for ELF-like files
        elf_candidates = list(build_dir.glob("*.elf"))
        if elf_candidates:
            return elf_candidates[0]

        # 3) Search for extensionless executable-ish files
        for f in build_dir.iterdir():
            if f.is_file() and "." not in f.name:
                # Ignore common non-firmware files
                if f.name.lower() not in ["makefile"]:
                    return f

        # 4) Fall back to .bin
        bin_candidates = list(build_dir.glob("*.bin"))
        if bin_candidates:
            return bin_candidates[0]

        return None

    # ---------------- Flashing ----------------
    def flash_firmware(self):
        project_dir = self.project_dir_edit.text().strip()
        firmware = self.firmware_edit.text().strip()
        flash_type = self.flash_type_combo.currentText()

        if not project_dir:
            QMessageBox.warning(self, "Missing Project Directory", "Please select a project directory.")
            return

        if not firmware or not Path(firmware).exists():
            QMessageBox.warning(self, "Firmware Not Found", "No valid firmware file was detected.")
            return

        if shutil.which("openocd") is None:
            QMessageBox.critical(self, "OpenOCD Missing", "openocd is not installed or not in PATH.")
            return

        interface_cfg = self.get_interface_cfg(flash_type)
        target_cfg = "target/lpc8x.cfg"

        command = [
            "openocd",
            "-f", interface_cfg,
            "-f", target_cfg,
            "-c", self.build_program_command(firmware),
        ]

        self.flash_btn.setEnabled(False)
        self.log("[INFO] Starting flash...")

        self.flash_worker = CommandWorker(command, cwd=project_dir)
        self.flash_worker.output.connect(self.log)
        self.flash_worker.finished_ok.connect(self.on_flash_finished)
        self.flash_worker.start()

    def get_interface_cfg(self, flash_type):
        if flash_type == "CMSIS-DAP":
            return "interface/cmsis-dap.cfg"
        return "interface/jlink.cfg"

    def build_program_command(self, firmware_path):
        """
        For ELF: OpenOCD can usually program directly.
        For BIN: add base address 0x0.
        """
        ext = Path(firmware_path).suffix.lower()

        if ext == ".bin":
            return f"program {firmware_path} 0x0 verify reset exit"
        else:
            return f"program {firmware_path} verify reset exit"

    def on_flash_finished(self, ok):
        self.flash_btn.setEnabled(True)
        if ok:
            self.log("[OK] Flash complete")
            QMessageBox.information(self, "Success", "Firmware flashed successfully.")
        else:
            self.log("[ERROR] Flash failed")
            QMessageBox.critical(self, "Flash Failed", "OpenOCD reported an error. Check the output log.")


# ---------------- Main ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LPC845Flasher()
    window.show()
    sys.exit(app.exec())
