import sys, os
import win32com.client
import time
import ctypes  # For bringing SAP to the front

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.sap_utils import logger
from my_app.app_utils.sap_launch import launch_sap
 # Import the SAP launcher module

############################################# For Direct SAP session Connection ##############################################
def get_sap_session():
    """Establishes and returns an active SAP GUI session."""
    try:
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
        application = sap_gui_auto.GetScriptingEngine
        connection = application.Children(0)
        session = connection.Children(0)
        logger.info("\n✅ Connected to SAP GUI.")
        return session
    except Exception as e:
        logger.error(f"Failed to connect to SAP GUI: {e}")
        return None

############################################## Idle SAP session connection ############################################
def get_sap_sessions():
    """
    Retrieves all active SAP sessions.

    Returns:
        list: A list of active SAP session objects.
    """
    try:
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        if not SapGuiAuto:
            logger.error("SAP GUI Scripting is not available.")
            return []

        application = SapGuiAuto.GetScriptingEngine
        if not application:
            logger.error("Could not retrieve SAP scripting engine.")
            return []

        if application.Children.Count == 0:
            logger.error("No active SAP connections found.")
            return []

        sessions = []
        for i in range(application.Children.Count):
            connection = application.Children(i)
            if connection.Children.Count > 0:
                sessions.append(connection.Children(0))  # Get the first session of each connection

        logger.info(f"Found {len(sessions)} active SAP session(s).")
        return sessions

    except Exception as e:
        logger.error(f"Error retrieving SAP sessions: {e}")
        return []

def is_session_idle(session):
    """
    Checks if a given SAP session is idle (SAP Easy Access screen or no active transaction).
    In this modified version, a session is considered idle if the transaction code is empty,
    'SESSION_MANAGER', or 'SMEN'.

    Args:
        session: SAP session object.

    Returns:
        bool: True if the session is idle, False otherwise.
    """
    try:
        transaction_code = session.Info.Transaction
        system_name = session.Info.SystemName
        user = session.Info.User

        # Consider idle if no transaction is active, or if it's on SAP Easy Access Screen
        # (indicated by "SESSION_MANAGER" or "SMEN").
        if not transaction_code or transaction_code.strip() in ("SESSION_MANAGER", "SMEN", "S000"):
            logger.info(f"Session '{user}@{system_name}' is idle (transaction: '{transaction_code}').")
            return True

        logger.info(f"Session '{user}@{system_name}' is in use (T-code: {transaction_code}).")
        return False

    except Exception as e:
        logger.warning(f"Could not check session status: {e}")
        return False

def bring_sap_to_front(session):
    """
    Maximizes the SAP window and brings it to the front.

    Args:
        session: Active SAP session.
    """
    try:
        sap_window = session.FindById("wnd[0]")  # Get the main SAP window
        sap_window.maximize()  # Maximize SAP window
        time.sleep(0.5)  # Small delay for window state to change

        # Get the window handle for SAP GUI
        hwnd = sap_window.Handle
        if hwnd:
            ctypes.windll.user32.SetForegroundWindow(hwnd)  # Bring SAP window to the front
            logger.info("\n✅ SAP window brought to the front successfully.")
        else:
            logger.warning("Could not retrieve SAP window handle.")

    except Exception as e:
        logger.error(f"Error bringing SAP to the front: {e}")

def connect_to_idle_sap():
    """
    Connects to an idle SAP session. If no idle session is available, it launches a new SAP session
    using the sap_launcher module, waits for a new session to appear, and then returns the idle session.

    Returns:
        session: An active idle SAP session or None if none is available.
    """
    sessions = get_sap_sessions()
    if sessions:
        # Check if any session is idle.
        for i, session in enumerate(sessions):
            if is_session_idle(session):
                user = session.Info.User
                system_name = session.Info.SystemName
                logger.info(f"\n✅ Connected to SAP session {i}: {user}@{system_name}")
                bring_sap_to_front(session)
                return session

    # If no idle session was found, attempt to launch a new SAP session.
    logger.error("No idle SAP sessions found. All sessions are in use.")
    logger.info("Attempting to launch a new SAP session using sap_launcher...")
    try:
        if launch_sap():
            # Wait a few seconds to allow the new session to appear.
            time.sleep(5)
            sessions = get_sap_sessions()
            for i, session in enumerate(sessions):
                if is_session_idle(session):
                    user = session.Info.User
                    system_name = session.Info.SystemName
                    logger.info(f"\n✅ Connected to newly launched idle SAP session {i}: {user}@{system_name}")
                    bring_sap_to_front(session)
                    return session
            logger.error("No idle SAP session available even after launching a new session.")
            return None
        else:
            logger.error("Failed to launch new SAP session via sap_launcher.")
            return None
    except Exception as e:
        logger.error(f"Error launching new SAP session: {e}")
        return None

# For testing purposes:
if __name__ == "__main__":
    session = connect_to_idle_sap()
    if session:
        print("Connected to an idle SAP session successfully.")
    else:
        print("No idle SAP session available.")
