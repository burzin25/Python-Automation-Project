# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def get_sap_status_bar_message(session):
    try:
        # Use the provided session directly without reconnecting
        status_bar = session.findById("wnd[0]/sbar")
        if not status_bar:
            print("Status bar not found.")
            return None
        # Extract the status bar message
        status_message = status_bar.Text
        print(f"Status Bar Message: {status_message}")
        return status_message
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_sap_status(session):
    status_message = get_sap_status_bar_message(session)
    if status_message is None:
        return False  # If there was an error or no message, assume False
    elif "No data was selected" in status_message:
        return False
    else:
        return True

# # Run the function
# session = get_sap_session()
# status_result = check_sap_status(session)
# print(status_result)  # This will print True or False based on the status message