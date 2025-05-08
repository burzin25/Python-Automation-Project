import os
import json
import sys
import time
import pandas as pd

# Show all DataFrame columns when printing
pd.set_option('display.max_columns', None)

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.sap_connection import connect_to_idle_sap
from utils.sap_utils import logger
from utils.sap_dates import get_dates
from utils.exceptions import SAPExecutionError, SAPDataNotAvailableError
from utils.sap_labels_table_extractor import get_sap_window_label_list
from utils.sap_labels_table_format import format_extracted_labels_table
from utils.sap_labels_table_preprocess import preprocess_sap_label_data
from utils.update_excel_sheet import update_excel_with_sap_data
from utils.sap_status_bar_check import check_sap_status
from sap_automate_64bit.config_loader import load_config, resource_path


def dynamic_wait(session, condition, timeout=30, interval=1):
    """
    Wait until `condition(session)` returns True, checking every `interval` seconds
    for up to `timeout` seconds.
    """
    start = time.time()
    while time.time() - start < timeout:
        if condition(session):
            return True
        time.sleep(interval)
    return False


def run_sap_transaction(
    session,
    transaction_code: str,
    input_fields: dict,
    table_selection: dict = None,
    post_actions: list = None,
    none_empty_df=None,
    excel_file_path: str = None,
    sheet_name: str = None
):
    """
    Generic SAP transaction template.

    Args:
      session:           Active SAP GUI session.
      transaction_code:  T-code to execute (e.g. "XXXXX").
      input_fields:      Dict { field_id: (value, focus, caret, clear_ctx) }.
      table_selection:   Optional { "path": id, "row": int, "select": bool }.
      post_actions:      Optional list of { "id": id, "action": "press"|"selectContextMenuItem", "arg": arg }.
      none_empty_df:     Fallback DataFrame if no data.
      excel_file_path:   Path for Excel export on no data.
      sheet_name:        Sheet name for Excel export.
    """
    try:
        # 1) start transaction
        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").text = transaction_code
        session.findById("wnd[0]").sendVKey(0)

        # 2) populate fields
        for fid, (value, focus, caret, clear_ctx) in input_fields.items():
            fld = session.findById(fid)
            if focus: fld.setFocus()
            if caret is not None: fld.caretPosition = caret
            if clear_ctx:
                fld.showContextMenu()
                session.findById("wnd[0]/usr").selectContextMenuItem("DELSCTX")
            if value is not None: fld.text = value

        # 3) optional table selection
        if table_selection:
            tbl = session.findById(table_selection["path"])
            tbl.currentCellRow = table_selection["row"]
            if table_selection.get("select", False):
                tbl.selectedRows = str(table_selection["row"])
            tbl.clickCurrentCell()

        # 4) execute and wait
        try:
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            if not dynamic_wait(session, lambda s: s.findById("wnd[0]/sbar").text != "Busy"):
                raise SAPExecutionError("Transaction did not complete in time.")
            if not check_sap_status(session):
                logger.warning("No data returned; exporting empty DataFrame.")
                update_excel_with_sap_data(none_empty_df, excel_file_path, sheet_name)
                return
        except Exception:
            logger.error("Error during transaction execution", exc_info=True)
            raise

        # 5) post-execution actions
        if post_actions:
            for act in post_actions:
                ctrl = session.findById(act["id"])
                if act["action"] == "press":
                    ctrl.press()
                elif act["action"] == "selectContextMenuItem":
                    ctrl.selectContextMenuItem(act["arg"])
                else:
                    logger.warning(f"Unknown post action: {act}")

    except Exception:
        logger.error("Error in run_sap_transaction template", exc_info=True)
        raise


def main():
    """
    Template main():
      1) connect to SAP
      2) run transaction
      3) extract, format, preprocess data
      4) update Excel
    """
    try:
        # connect to idle SAP
        session = connect_to_idle_sap()
        if not session or not hasattr(session, "findById"):
            logger.error("Could not obtain SAP session.")
            return

        # load config
        cfg = load_config()
        excel_path = resource_path(cfg["excel_file_path"])
        sheet_name = cfg["sheets"].get(cfg.get("sheet_alias"), cfg.get("default_sheet"))

        # get dates
        from_date, to_date, _ = get_dates()

        # placeholder DF
        placeholder_df = pd.DataFrame({})

        # run transaction
        run_sap_transaction(
            session=session,
            transaction_code=cfg["transaction_code"],
            input_fields=cfg["input_fields"],
            table_selection=cfg.get("table_selection"),
            post_actions=cfg.get("post_actions"),
            none_empty_df=placeholder_df,
            excel_file_path=excel_path,
            sheet_name=sheet_name
        )

        # extract labels table
        raw = get_sap_window_label_list(session)
        if raw is None:
            logger.error("Data extraction returned None.")
            return

        # format table
        formatted = format_extracted_labels_table(raw, **cfg["formatting_params"])
        if formatted is None:
            logger.error("Formatting failed.")
            return

        # preprocess
        cleaned = preprocess_sap_label_data(formatted, **cfg["preprocess_params"])
        if cleaned is None or cleaned.empty:
            logger.info("No data after preprocessing; nothing to export.")
            return

        # update Excel
        logger.info(f"Writing {len(cleaned)} rows to '{sheet_name}' in '{excel_path}'")
        update_excel_with_sap_data(cleaned, excel_path, sheet_name)

        logger.info("Process completed successfully.")

    except SAPDataNotAvailableError as e:
        logger.warning(f"No data available: {e}")
    except SAPExecutionError as e:
        logger.error(f"SAP execution error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}", exc_info=True)


if __name__ == "__main__":
    main()
