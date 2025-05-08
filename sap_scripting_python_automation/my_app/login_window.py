# login_window.py

import socket
import os, sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QCheckBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFormLayout, QFileDialog, QDateEdit)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QDate

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the task windows so they can be opened after login.
from my_app.admin_task_window import AdminTaskWindow
from my_app.user1_task_window import UserTaskWindow



def resource_path(relative_path):
    """
    Return the correct path for bundled or development environments.
    """
    try:
        base_path = sys._MEIPASS  # Set by PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        window_title = "Wieland TS - Wheeling, IL SAP Data Extraction App"
        self.setWindowTitle(window_title)
        # Make the window non-resizable.
        self.setFixedSize(500, 400)

        # Main widget and layout.
        widget = QWidget()
        main_layout = QVBoxLayout(widget)

        # Create a form layout for the Username and Password fields.
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        label_font = QFont("Arial", 12, QFont.Bold)
        input_font = QFont("Arial", 11)

        # --- Username Row ---
        self.label_username = QLabel("Username:")
        self.label_username.setFont(label_font)
        self.text_username = QLineEdit(self)
        self.text_username.setFont(input_font)
        self.text_username.setFixedWidth(300)
        form_layout.addRow(self.label_username, self.text_username)

        # --- "Forgot username/password" hyperlink row ---
        self.forgot_link = QLabel('<a href="#">Forgot username/password?</a>')
        self.forgot_link.setFont(QFont("Arial", 10))
        self.forgot_link.setAlignment(Qt.AlignRight)
        self.forgot_link.setTextFormat(Qt.RichText)
        self.forgot_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.forgot_link.setOpenExternalLinks(False)
        self.forgot_link.linkActivated.connect(self.forgot_me)
        form_layout.addRow("", self.forgot_link)

        # --- Password Row ---
        self.label_password = QLabel("Password:")
        self.label_password.setFont(label_font)

        password_layout = QHBoxLayout()
        self.text_password = QLineEdit(self)
        self.text_password.setFont(input_font)
        self.text_password.setEchoMode(QLineEdit.Password)
        self.text_password.setFixedWidth(260)

        # Eye icon for toggling password visibility.
        eye_icon_path = resource_path("my_app/icons/password_eye_icon.png")
        # eye_icon_path = os.path.join(os.path.dirname(__file__), "icons", "password_eye_icon.png")
        if os.path.exists(eye_icon_path):
            eye_icon_pixmap = QPixmap(eye_icon_path).scaled(20, 20, Qt.KeepAspectRatio)
            eye_icon = QIcon(eye_icon_pixmap)
            self.button_show_password = QPushButton()
            self.button_show_password.setIcon(eye_icon)
            self.button_show_password.setFixedSize(30, 30)
            self.button_show_password.setCheckable(True)
            self.button_show_password.clicked.connect(self.toggle_password_visibility)
            password_layout.addWidget(self.text_password)
            password_layout.addWidget(self.button_show_password)
        else:
            QMessageBox.warning(self, "Icon Missing", f"Eye icon not found at: {eye_icon_path}")
        form_layout.addRow(self.label_password, password_layout)

        # --- "Remember Me" Checkbox Row ---
        self.checkbox_remember = QCheckBox("Remember Me")
        self.checkbox_remember.setFont(QFont("Arial", 11))
        form_layout.addRow("", self.checkbox_remember)

        main_layout.addLayout(form_layout)

        # --- Centered Sign In Button ---
        self.button_sign_in = QPushButton("Sign In")
        self.button_sign_in.setFont(QFont("Arial", 11))
        self.button_sign_in.setFixedWidth(100)
        self.button_sign_in.clicked.connect(self.sign_in)
        sign_in_layout = QHBoxLayout()
        sign_in_layout.addStretch()
        sign_in_layout.addWidget(self.button_sign_in)
        sign_in_layout.addStretch()
        main_layout.addLayout(sign_in_layout)

        # --- Close Button ---
        self.button_close = QPushButton("Close")
        self.button_close.setFont(QFont("Arial", 11))
        self.button_close.setFixedWidth(100)
        self.button_close.clicked.connect(self.close_app)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(self.button_close)
        close_layout.addStretch()
        main_layout.addLayout(close_layout)

        # --- Footer Layout for Connection Status and App Info ---
        footer_layout = QHBoxLayout()
        self.status_icon_label = QLabel()
        self.status_text_label = QLabel()
        self.status_text_label.setFont(QFont("Arial", 10))
        self.update_connection_status()
        footer_layout.addWidget(self.status_icon_label, alignment=Qt.AlignLeft)
        footer_layout.addWidget(self.status_text_label, alignment=Qt.AlignLeft)
        footer_layout.addStretch()
        self.footer_label = QLabel("Wieland Thermal Solutions, Wheeling\nApp owner: BNW")
        self.footer_label.setFont(QFont("Arial", 10))
        footer_layout.addWidget(self.footer_label, alignment=Qt.AlignRight)
        main_layout.addLayout(footer_layout)

        self.setCentralWidget(widget)

    def update_connection_status(self):
        ip_to_check = self.get_ip_address()
        company_ip_ranges = {
            "Company Ethernet": "10.156.",
            "Company Wi-Fi": "10.156.",
            "Company VPN": "10.147.",
        }
        connection_type = None
        for key, ip_prefix in company_ip_ranges.items():
            if ip_to_check.startswith(ip_prefix):
                connection_type = key
                break
        if connection_type:
            icon_path = resource_path("my_app/icons/connection_established.png")
            # icon_path = os.path.join(os.path.dirname(__file__), "icons", "connection_established.png")
            message = f"Connected to {connection_type}"
        else:
            icon_path = resource_path("my_app/icons/no_connection.png")
            # icon_path = os.path.join(os.path.dirname(__file__), "icons", "no_connection.png")
            message = "Not connected to company's connection type"
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path).scaled(20, 20, Qt.KeepAspectRatio)
            self.status_icon_label.setPixmap(icon_pixmap)
        else:
            self.status_icon_label.clear()
            QMessageBox.warning(self, "Icon Missing", f"Status icon not found at: {icon_path}")
        self.status_text_label.setText(f"  {message}")

    def get_ip_address(self):
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except Exception:
            return ""

    def toggle_password_visibility(self):
        if self.button_show_password.isChecked():
            self.text_password.setEchoMode(QLineEdit.Normal)
        else:
            self.text_password.setEchoMode(QLineEdit.Password)

    def sign_in(self):
        username = self.text_username.text()
        password = self.text_password.text()
        # For demonstration, we have two hardcoded user credentials.
        if username == "Burzin" and password == "password123":
            self.task_window = AdminTaskWindow()
            self.task_window.show()
            self.hide()
        elif username == "user" and password == "userpass":
            self.task_window = UserTaskWindow()
            self.task_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def forgot_me(self):
        QMessageBox.information(self, "Forgot Credentials", "Send an email at burzin.wadia@wieland.com")

    def close_app(self):
        self.close()
