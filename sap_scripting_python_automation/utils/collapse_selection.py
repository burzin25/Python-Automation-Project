import time

def navigate_left_bottom_and_execute(session, shell):
    """
    Navigates to the left-bottom cell in a SAP table (or grid) and executes its action
    by calling pressTotalRowCurrentCell() without using virtual key commands.

    Assumes:
      - 'shell' is the SAP table control (e.g., ALV grid) retrieved via session.findById.
      - The control provides a RowCount property and allows setting currentCellRow
        (and optionally currentCellColumn).

    Parameters:
      session: The active SAP session object.
      shell: The SAP table/grid control object.
    """
    try:
        # Retrieve the total number of rows in the table.
        total_rows = shell.RowCount
        if total_rows is None or total_rows < 1:
            raise Exception("Unable to determine the total number of rows.")

        # Calculate the index of the bottom row (assuming 0-indexing)
        bottom_row = total_rows - 1

        # Set focus to the bottom row.
        shell.currentCellRow = bottom_row

        # Attempt to set focus to the leftmost column (assumed to be column 0).
        try:
            shell.currentCellColumn = 0
        except Exception:
            pass

        # Adjust the first visible row so that the bottom row is in view.
        try:
            shell.firstVisibleRow = bottom_row - 5 if bottom_row >= 5 else 0
        except Exception:
            pass

        # Allow some time for the selection to be processed.
        # time.sleep(0.05)

        # Execute the cell's action.
        shell.pressTotalRowCurrentCell()
        # time.sleep(0.05)

    except Exception as e:
        raise Exception(f"Failed to navigate to the left-bottom cell and execute its action: {e}")


# Example usage:
if __name__ == "__main__":
    from utils.sap_connection import get_sap_session
    from utils.sap_utils import logger

    try:
        session = get_sap_session()
        if session is None:
            logger.error("No active SAP session found.")
        else:
            # Retrieve the control that represents your table/grid.
            shell = session.findById("wnd[0]/usr/cntlCONTAINER/shellcont/shell")
            # Allow some time for the control to be ready.
            time.sleep(1)

            # Execute the operation twice.
            for i in range(2):
                logger.info(f"Executing operation iteration {i + 1}...")
                navigate_left_bottom_and_execute(session, shell)
                # Pause between iterations if needed.
                time.sleep(2)

            logger.info("Operation executed successfully twice.")
    except Exception as e:
        logger.error(f"Error during navigation: {e}")
