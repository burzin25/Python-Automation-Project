"""
Module: sap_utils
Description: Common utilities for SAP automation.
"""

import logging

# Configure logging once and import it into other modules
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# def get_sap_session():
#     """Establish and return an active SAP GUI session."""
#     try:
#         sap_gui_auto = win32com.client.GetObject("SAPGUI")
#         application = sap_gui_auto.GetScriptingEngine
#         connection = application.Children(0)
#         session = connection.Children(0)
#         logger.info("Connected to SAP GUI.")
#         return session
#     except Exception as e:
#         logger.error(f"Failed to connect to SAP GUI: {e}")
#         return None
