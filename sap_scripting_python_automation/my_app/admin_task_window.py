import os
import subprocess
import sys
import time
import json

from PyQt5.QtCore import QDate, QRunnable, QThreadPool, Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QCheckBox,
    QPushButton, QTextEdit, QDateEdit, QMessageBox, QLineEdit, QFileDialog, QComboBox, QRadioButton, QGridLayout
)

# Imports for handling SAP prompt via Windows API
import win32gui
import win32con

# Import the SAP launcher module.
from sap_automate_64bit.my_app.app_utils import sap_launch
from sap_automate_64bit.utils.sap_connection import connect_to_idle_sap
from sap_automate_64bit.config_loader import load_config, resource_path



# ------------------------------
# Worker Signals for SAP launch
# ------------------------------
class WorkerSignals(QObject):
    finished = pyqtSignal(bool)  # Emits True if SAP launch succeeded, False otherwise.

# ------------------------------
# SAP Launch Worker using QRunnable
# ------------------------------
class SapLaunchWorker(QRunnable):
    def __init__(self):
        super(SapLaunchWorker, self).__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = sap_launch.launch_sap()
        except Exception:
            result = False
        self.signals.finished.emit(result)

# ------------------------------
# For Concurrent Mode: TransactionTask remains unchanged.
# ------------------------------
class TransactionTask(QRunnable):
    def __init__(self, script_path, transaction_name, from_date, to_date, excel_path, callback):
        super().__init__()
        self.script_path = script_path
        self.transaction_name = transaction_name
        self.from_date = from_date
        self.to_date = to_date
        self.excel_path = excel_path
        self.callback = callback

    def run(self):
        try:
            # Section Header for this transaction
            self.callback("\n" + "=" * 60)
            self.callback(f"📄 <b>{self.transaction_name}</b>")
            self.callback("=" * 60 + "\n")
            self.callback(f"🚀 <i>Running Script:</i> {self.script_path}")
            self.callback(f"📅 <i>From:</i> {self.from_date}    <i>To:</i> {self.to_date}")
            self.callback(f"📂 <i>Excel:</i> {self.excel_path}")
            self.callback("🛠️ <i>Executing...</i>\n")

            # Build and run the subprocess command
            cmd = ["python", self.script_path, self.from_date]
            cmd.append(self.to_date if self.to_date else "None")
            cmd.append(self.excel_path)
            print(f"Executing: {' '.join(cmd)}")
            sys.stdout.flush()

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    self.callback(output.strip())
                    print(output.strip())
                    sys.stdout.flush()

            # Collect final outputs
            stdout, stderr = process.communicate()

            # Show output summary
            if process.returncode == 0:
                self.callback("\n✅ <b>Transaction Completed Successfully.</b>")
            else:
                self.callback("\n❌ <b>Transaction Failed!</b>")
                self.callback(f"🔻 <pre>{stderr.strip()}</pre>")

            # Section Footer
            self.callback("\n" + "-" * 60 + "\n")

        except Exception as e:
            error_msg = f"⚠️ Error running {self.transaction_name}: {str(e)}"
            self.callback(error_msg)
            print(error_msg)
            sys.stdout.flush()


# ------------------------------
# HELPER FUNCTION to find the SAP Logon prompt window
# ------------------------------
def find_sap_prompt_window():
    """
    Returns the handle (HWND) of the top-level window whose title contains "SAP Logon".
    Returns None if not found.
    """
    found_hwnd = None

    def enum_callback(hwnd, _):
        nonlocal found_hwnd
        window_text = win32gui.GetWindowText(hwnd)
        if "sap logon" in window_text.lower():
            found_hwnd = hwnd
            return False  # Stop enumeration
        return True

    win32gui.EnumWindows(enum_callback, None)
    return found_hwnd

# ------------------------------
# Admin Task Window Class
# ------------------------------
class AdminTaskWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Task Window - Burzin Wadia")
        self.setFixedSize(800, 600)

        # Load configuration using the standardized helper.
        self.config = load_config()

        # Get Excel file path from config (or use default if not set)
        self.excel_path = self.config.get("excel_file_path", "<Excel File Name>.xlsx")

        # Dictionary mapping transaction names to their script file paths.
        self.transaction_scripts = {
            "<transation.py file name 1>": resource_path(r"<your folder path>\<file name 1>.py"),
            "<transation.py file name 2>": resource_path(r"<your folder path>\<file name 2>.py")

        }

        # Global thread pool for concurrent tasks
        self.thread_pool = QThreadPool.globalInstance()

        # SAP session and user selections
        self.session = None
        self.from_date = None
        self.to_date = None
        self.start_time = None
        self.first_prompt_handled = False

        self.init_ui()

    def load_config(self):
        """Load configuration from the config file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def save_config(self):
        """Save the current configuration back to the config file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def browse_excel_file(self):
        """Open a file dialog to select an Excel file and update the config."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.excel_path = file_path
            self.excel_path_edit.setText(file_path)
            self.status_text_edit.append(f"📂 Selected Excel File: {file_path}")
            # Update configuration with the new path and save it
            self.config["excel_file_path"] = file_path
            self.save_config()

    def init_ui(self):
        """Build the user interface."""
        main_layout = QVBoxLayout()

        # Section 1: Excel File Selection
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel File:"))
        self.excel_path_edit = QLineEdit(self)
        self.excel_path_edit.setText(self.excel_path)
        excel_layout.addWidget(self.excel_path_edit)
        browse_button = QPushButton("Browse", self)
        browse_button.clicked.connect(self.browse_excel_file)
        excel_layout.addWidget(browse_button)
        main_layout.addLayout(excel_layout)

        # Section 2: Date Selection
        date_layout = QHBoxLayout()
        date_layout.setAlignment(Qt.AlignLeft)
        date_layout.addWidget(QLabel("From Date:"))
        self.from_date_edit = QDateEdit(self)
        self.from_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDate(QDate.currentDate())
        self.from_date_edit.setFixedWidth(150)
        date_layout.addWidget(self.from_date_edit)
        date_layout.addSpacing(20)
        date_layout.addWidget(QLabel("To Date:"))
        self.to_date_edit = QDateEdit(self)
        self.to_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setFixedWidth(150)
        date_layout.addWidget(self.to_date_edit)
        self.disable_to_date_checkbox = QCheckBox("Disable To Date", self)
        self.disable_to_date_checkbox.stateChanged.connect(
            lambda state: self.to_date_edit.setDisabled(state == Qt.Checked))
        date_layout.addWidget(self.disable_to_date_checkbox)
        main_layout.addLayout(date_layout)

        # Section 3: Transaction Checkboxes
        trans_group_layout = QVBoxLayout()
        trans_group_layout.addWidget(QLabel("Select Transactions:"))
        self.select_all_radio = QRadioButton("Select All Transactions", self)
        self.select_all_radio.toggled.connect(
            lambda checked: [cb.setChecked(checked) for cb in self.transaction_checkboxes.values()])
        trans_group_layout.addWidget(self.select_all_radio)
        grid_layout = QGridLayout()
        self.transaction_checkboxes = {}
        col_count = 2
        row = col = 0
        for transaction in self.transaction_scripts.keys():
            checkbox = QCheckBox(transaction, self)
            self.transaction_checkboxes[transaction] = checkbox
            grid_layout.addWidget(checkbox, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1
        trans_group_layout.addLayout(grid_layout)
        main_layout.addLayout(trans_group_layout)

        # Section 4: Execution Status Display
        self.status_text_edit = QTextEdit(self)
        self.status_text_edit.setReadOnly(True)
        main_layout.addWidget(self.status_text_edit)

        # Section 5: Execution Mode and Buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Execution Mode:"))
        self.exec_mode_combo = QComboBox(self)
        self.exec_mode_combo.addItems(["Sequential", "Concurrent"])
        button_layout.addWidget(self.exec_mode_combo)
        self.verify_button = QPushButton("Verify Mappings", self)
        self.verify_button.clicked.connect(self.verify_script_mappings)
        button_layout.addWidget(self.verify_button)
        self.run_button = QPushButton("Run Transactions", self)
        self.run_button.clicked.connect(self.run_transactions)
        button_layout.addWidget(self.run_button)
        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(lambda: os._exit(0))
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)



    def verify_script_mappings(self):
        """Check that each transaction script exists on disk."""
        self.status_text_edit.clear()
        self.status_text_edit.append("🔍 Verifying script mappings...\n")
        all_valid = True
        for transaction, script_path in self.transaction_scripts.items():
            if os.path.exists(script_path):
                self.status_text_edit.append(f"✅ {transaction}: Found -> {script_path}")
            else:
                self.status_text_edit.append(f"❌ {transaction}: Not Found! -> {script_path}")
                all_valid = False
        if all_valid:
            self.status_text_edit.append("\n🎯 All scripts are correctly mapped.\n")
        else:
            self.status_text_edit.append("\n⚠️ Some scripts are missing! Please check the paths.\n")

    def run_transactions(self):
        """Collect user selections and execute the selected transactions."""
        self.start_time = time.perf_counter()
        from_date_obj = self.from_date_edit.date()
        self.from_date = from_date_obj.toString("MM/dd/yyyy")
        if self.disable_to_date_checkbox.isChecked():
            self.to_date = None
        else:
            to_date_obj = self.to_date_edit.date()
            if to_date_obj < from_date_obj:
                QMessageBox.warning(self, "Invalid Dates",
                                    "The 'To Date' must be equal to or later than the 'From Date'.")
                return
            self.to_date = to_date_obj.toString("MM/dd/yyyy")

        self.status_text_edit.clear()
        self.status_text_edit.append(f"Selected Dates:\n  - From Date: {self.from_date}\n  - To Date: {self.to_date}\n")
        self.status_text_edit.append("🔍 Checking for idle SAP session...\n")
        self.session = connect_to_idle_sap()
        if not self.session:
            self.status_text_edit.append("🚀 No idle session found. Launching SAP application...\n")
            QTimer.singleShot(100, self.launch_sap_main_thread)
            return
        else:
            self.status_text_edit.append("Connected to SAP session\n")
            self.process_transactions()

    def launch_sap_main_thread(self):
        """Launch SAP on the main thread and wait for connection."""
        try:
            result = sap_launch.launch_sap()
        except Exception as e:
            self.status_text_edit.append(f"❌ Error launching SAP application: {e}\n")
            return
        if result:
            self.status_text_edit.append("SAP application launched.\n⏳ Waiting for SAP to launch...\n")
            QTimer.singleShot(5000, self.check_sap_connection_and_continue)
        else:
            self.status_text_edit.append("❌ Error launching SAP application.\n")

    def check_sap_connection_and_continue(self):
        """Ensure an SAP session is available, then process transactions."""
        self.session = connect_to_idle_sap()
        if not self.session:
            self.status_text_edit.append(
                "❌ Could not connect to SAP session. Please ensure SAP is running and try again.\n")
            return
        self.status_text_edit.append("Connected to SAP session\n")
        self.process_transactions()

    def process_transactions(self):
        """Execute each selected transaction script."""
        transaction_counter = 1
        for transaction, checkbox in self.transaction_checkboxes.items():
            if checkbox.isChecked():
                script_path = self.transaction_scripts.get(transaction)
                if script_path and os.path.exists(script_path):
                    self.status_text_edit.append(f"{transaction_counter}. Transaction: {transaction}\n")
                    cmd = ["Python", script_path, self.from_date, self.to_date if self.to_date else "None",
                           self.excel_path_edit.text()]
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
                    self.status_text_edit.append(result.stdout + "\n")
                    if result.returncode == 0:
                        self.status_text_edit.append(f"✅ {transaction} completed successfully.\n")
                        try:
                            self.session.findById("wnd[0]/tbar[0]/okcd").text = "/n"
                            self.session.findById("wnd[0]").sendVKey(0)
                            self.status_text_edit.append("🔄 SAP clear command executed.\n")
                        except Exception as e:
                            self.status_text_edit.append(f"⚠️ Error executing SAP clear command: {e}\n")
                    else:
                        self.status_text_edit.append(f"❌ {transaction} failed. Error: {result.stderr}\n")
                    self.check_and_handle_sap_prompt()
                    transaction_counter += 1
                else:
                    self.status_text_edit.append(f"⚠️ Skipping {transaction}: Script not found!\n")
        elapsed_time = time.perf_counter() - self.start_time
        self.status_text_edit.append(f"⏱️ All transactions completed in {elapsed_time:.2f} seconds.")

    def check_and_handle_sap_prompt(self):
        """Look for a SAP Logon prompt and auto-click OK if needed."""
        hwnd = find_sap_prompt_window()
        if hwnd:
            if self.first_prompt_handled:
                self.auto_click_prompt(hwnd)
            else:
                QTimer.singleShot(1000, self.check_and_handle_sap_prompt)
        else:
            self.first_prompt_handled = True

    def auto_click_prompt(self, hwnd):
        """Automatically click the OK button in the SAP Logon prompt."""

        def callback(child_hwnd, _):
            text = win32gui.GetWindowText(child_hwnd)
            if "ok" in text.lower():
                win32gui.SendMessage(child_hwnd, win32con.BM_CLICK, 0, 0)

        win32gui.EnumChildWindows(hwnd, callback, None)

    def exit_app(self):
        os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminTaskWindow()
    window.show()
    sys.exit(app.exec_())
