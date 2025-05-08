"""
Module: sap_alv_extractor
Description: This module extracts SAP ALV Grid data using SAP GUI scripting.
"""

import time
import pandas as pd

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sap_automate_64bit.utils.sap_utils import logger
from sap_automate_64bit.utils.sap_connection import get_sap_session

def extract_sap_alv_grid(session, grid_id="wnd[0]/usr/cntlGRID1/shellcont/shell"):
    """Extracts SAP ALV Grid data safely and returns a DataFrame."""
    try:
        if not session:
            logger.error("No active SAP session. Cannot extract ALV Grid.")
            return pd.DataFrame()

        grid = session.FindById(grid_id)

        # Check if the grid has a RowCount property
        if not hasattr(grid, "RowCount"):
            logger.error("Grid does not have RowCount property.")
            return pd.DataFrame()

        # If the grid is empty, try to extract column headers and return an empty DataFrame
        if grid.RowCount == 0:
            logger.warning("SAP ALV Grid is empty.")
            if hasattr(grid, "ColumnOrder"):
                column_titles = [grid.GetColumnTitles(col)[0] for col in grid.ColumnOrder]
                return pd.DataFrame(columns=column_titles)
            else:
                logger.error("Column order not found for empty grid. Check SAP GUI scripting settings.")
                return pd.DataFrame()

        # Proceed only if the grid has column information
        if not hasattr(grid, "ColumnOrder"):
            logger.error("Column order not found. Check SAP GUI scripting settings.")
            return pd.DataFrame()

        row_count, col_count = grid.RowCount, grid.ColumnCount
        column_titles = [grid.GetColumnTitles(col)[0] for col in grid.ColumnOrder]
        table_data = []

        visible_rows = grid.VisibleRowCount
        start_row = 0

        while start_row < row_count:
            batch_data = [
                [grid.GetCellValue(i, col) for col in grid.ColumnOrder]
                for i in range(start_row, min(start_row + visible_rows, row_count))
            ]
            table_data.extend(batch_data)
            start_row += visible_rows

            if start_row < row_count:
                grid.FirstVisibleRow = start_row
                time.sleep(1)  # Allow SAP GUI to refresh

        return pd.DataFrame(table_data, columns=column_titles)
    except Exception as e:
        logger.error(f"Error extracting SAP grid data: {e}")
        return pd.DataFrame()


def main():
    """Main function to extract SAP ALV Grid data."""
    session = get_sap_session()
    if session:
        grid_id = "wnd[0]/usr/cntlGRID1/shellcont/shell"
        sap_data = extract_sap_alv_grid(session, grid_id)

        if not sap_data.empty:
            print("\n✅ Successfully extracted SAP Table Data:")
            print(sap_data)  # Print full table (CAUTION: Can be large!)
        else:
            print("\n⚠️ No data found in the SAP ALV Grid.")
            print("Extracted columns (if any):", list(sap_data.columns))


if __name__ == "__main__":
    main()
