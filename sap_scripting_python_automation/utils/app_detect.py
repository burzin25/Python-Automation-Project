import win32com.client
import sys
import time

def connect_to_sap_gui():
    try:
        # Get the SAP GUI Scripting object
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
        if not sap_gui_auto:
            print("SAP GUI Scripting object not found. Ensure SAP GUI is running.")
            return None

        # Get the scripting engine
        application = sap_gui_auto.GetScriptingEngine
        if not application:
            print("Could not access SAP GUI Scripting Engine.")
            return None

        # Check if there’s an active connection
        if application.Children.Count == 0:
            print("No active SAP connection found. Please log in to SAP GUI first.")
            return None

        # Get the first connection
        connection = application.Children(0)
        if not connection:
            print("Could not access SAP connection.")
            return None

        # Get the first session
        session = connection.Children(0)
        if not session:
            print("Could not access SAP session.")
            return None

        return session

    except Exception as e:
        print(f"Error connecting to SAP GUI: {e}")
        return None

def get_transaction_code(session):
    try:
        # Ensure the session is active and get the transaction code
        if session.Info.Transaction:
            transaction_code = session.Info.Transaction
            return transaction_code
        else:
            return "No transaction code found on the current screen."
    except Exception as e:
        print(f"Error retrieving transaction code: {e}")
        return None

def main():
    # Connect to SAP GUI
    session = connect_to_sap_gui()
    if not session:
        print("Failed to connect to SAP GUI.")
        sys.exit(1)

    # Wait briefly to ensure the screen is fully loaded
    time.sleep(1)

    # Get the current transaction code
    tcode = get_transaction_code(session)
    if tcode:
        print(f"Current Transaction Code: {tcode}")
    else:
        print("Could not retrieve transaction code.")

if __name__ == "__main__":
    main()