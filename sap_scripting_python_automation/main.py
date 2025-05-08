import sys
import os
import os, sys

from PyQt5.QtWidgets import QApplication
from sap_automate_64bit.my_app.login_window import LoginWindow  # Import your existing login window


# def resource_path(relative_path):
#     """Get absolute path to resource, works for development and for PyInstaller bundle."""
#     try:
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())




if __name__ == '__main__':
    main()
