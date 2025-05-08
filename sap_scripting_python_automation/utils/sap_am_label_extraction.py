import re
from collections import deque
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sap_automate_64bit.utils import sap_connection

from sap_automate_64bit.utils.sap_utils import logger
from sap_automate_64bit.utils.sap_connection import get_sap_session

def find_label_by_text(session, text, max_depth=10):
    """
    Find a label with specific text inside the SAP window.

    Args:
        session: Active SAP session.
        text (str): The label text to search for.
        max_depth (int): Maximum search depth.

    Returns:
        str: The full SAP element ID of the label, or None if not found.
    """
    if not session:
        logger.error("SAP session not established")
        return None

    try:
        window = session.FindById("wnd[0]")
        elements_to_explore = deque([(window, 0)])

        while elements_to_explore:
            current_element, depth = elements_to_explore.popleft()

            if getattr(current_element, 'Text', '').strip() == text:
                logger.info(f"Label found: {current_element.Id}")
                return current_element.Id

            if depth < max_depth and hasattr(current_element, 'Children'):
                elements_to_explore.extend((child, depth + 1) for child in current_element.Children)

        logger.warning(f"No label found with text: {text}")
        return None

    except Exception as e:
        logger.error(f"Error searching for label: {e}")
        return None


def extract_label_path(full_id):
    """
    Extract the label path from a full SAP element ID.

    Args:
        full_id (str): The full SAP element ID.

    Returns:
        str: The extracted label path or None if extraction fails.
    """
    if not full_id or not isinstance(full_id, str):
        logger.warning("Invalid input for label path extraction")
        return None

    try:
        match = re.search(r'(wnd\[0\]/usr/lbl\[\d+,\d+\])', full_id)
        return match.group(1) if match else None

    except Exception as e:
        logger.error(f"Error extracting label path: {e}")
        return None

def main():
    """Main function to execute the label search and extraction."""
    # Connect to SAP
    session = get_sap_session()
    if not session:
        logger.error("Failed to establish SAP session.")
        return

    # Search for a label by text
    label_text = "OTD per prod. order"  # Replace with the actual label text
    full_id = find_label_by_text(session, label_text)

    if full_id:
        logger.info(f"Full ID of the label: {full_id}")

        # Extract the label path
        label_path = extract_label_path(full_id)
        if label_path:
            logger.info(f"Extracted label path: {label_path}")
        else:
            logger.warning("Failed to extract label path.")
    else:
        logger.warning("Label not found.")


if __name__ == "__main__":
    main()