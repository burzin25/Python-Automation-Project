"""
Module: sap_ui_extractor
Description: Extracts SAP UI elements, labels, and window details using SAP GUI scripting.
"""
import os,sys
from typing import Optional
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.sap_utils import logger
from utils.sap_connection import get_sap_session


def extract_text(element) -> str:
    """
    Extract meaningful text from different UI elements safely.

    Parameters:
        element (object): A UI element from which text should be extracted.

    Returns:
        str: The first non-empty text value found among potential attributes
             (such as "Text", "Tooltip", "Value", "Caption", "Description").
             Returns "<No Text Found>" if none is found.
    """
    possible_attributes = ["Text", "Tooltip", "Value", "Caption", "Description"]
    for attr in possible_attributes:
        try:
            if hasattr(element, attr):
                value = getattr(element, attr, "").strip()
                if value:
                    return value  # Return first non-empty value found
        except:
            continue
    return "<No Text Found>"

def extract_labels(session) -> Optional[pd.DataFrame]:
    """
    Extracts raw label data from the SAP user area and returns it as a pivoted DataFrame.

    The resulting DataFrame has:
      - A column "Row" (of type int) representing the row numbers.
      - Other columns (with int column names) representing extracted label texts (of type str).

    Parameters:
        session (object): The active SAP session object.

    Returns:
        Optional[pd.DataFrame]: A pivoted DataFrame containing label data if extraction
                                is successful, otherwise None.
    """
    try:
        usr_area = session.findById("wnd[0]/usr")
        label_data = []

        for child in usr_area.Children:
            if "lbl" in child.Id:
                text = extract_text(child)
                if text and text != "<No Text Found>":
                    label_id = child.Id
                    parts = label_id.split("[")[-1].split(",")
                    if len(parts) == 2:
                        col_number = int(parts[0])
                        row_number = int(parts[1].strip("]"))
                    else:
                        row_number = -1
                        col_number = -1
                    label_data.append({'Row': row_number, 'Column': col_number, 'Text': text})

        df = pd.DataFrame(label_data)
        if df.empty:
            logger.warning("No labels found.")
            return None

        # Pivot the DataFrame to organize labels based on rows and columns
        df_pivoted = df.pivot(index='Row', columns='Column', values='Text').sort_index().reset_index()
        logger.info("✅ Successfully extracted labels.")
        return df_pivoted
    except Exception as e:
        logger.error(f"Error extracting labels: {e}")
        return None

def get_sap_window_label_list(session: object) -> Optional[pd.DataFrame]:
    """
    Retrieve SAP window details and extract UI elements and labels if they exist.

    Logs details such as:
      - Title (str)
      - Transaction Code (str)
      - Screen Number (str)
      - Program Name (str)

    Then, if label elements exist in the user area, it extracts the labels into a DataFrame.

    Parameters:
        session (object): The active SAP session object.

    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the extracted labels (with data types as follows):
                                - "Row": int
                                - Other columns: str (extracted label texts)
                                Returns None if extraction fails or no labels are found.
    """
    try:
        window = session.findById("wnd[0]")
        details = {
            "Title": window.findById("titl").Text,
            "Transaction Code": session.Info.Transaction,
            "Screen Number": session.Info.ScreenNumber,
            "Program Name": session.Info.Program
        }

        logger.info("📌 SAP Window Details:")
        for key, value in details.items():
            logger.info(f"   ▶ {key}: {value}")

        # Check if window contains label elements before extracting labels
        usr_area = session.findById("wnd[0]/usr")
        if any("lbl" in child.Id for child in usr_area.Children):
            df_labels = extract_labels(session)
        else:
            df_labels = None
            logger.warning("No label elements found in the window.")

        return df_labels
    except Exception as e:
        logger.error(f"Error retrieving SAP window details: {e}")
        return None, None

def main() -> Optional[pd.DataFrame]:
    """Main function to retrieve and display SAP window details and labels."""
    session = get_sap_session()
    if session:
        df_labels = get_sap_window_label_list(session)
        if df_labels is not None:
            print("\n✅ Final Extracted DataFrame:")
            print(df_labels)
            print(df_labels.columns)
            print(df_labels.info)
        return df_labels

if __name__ == "__main__":
    main()
