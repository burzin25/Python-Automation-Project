import win32com.client
import pythoncom


def get_sap_table_data():
    pythoncom.CoInitialize()  # Required if running from a non-main thread

    try:
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
        application = sap_gui_auto.GetScriptingEngine
        connection = application.Children(0)
        session = connection.Children(0)

        return session
    except Exception as e:

        return None

    application = SapGuiAuto.GetScriptingEngine
    connection = application.Children(0)
    session = connection.Children(0)

    # Example path to the table element — update based on your transaction
    # Use scripting recorder to find the right ID
    table_id = "usr/tblSAPLZMM_TABLE1"  # Replace with your table ID
    table = session.FindById(table_id)

    row_count = table.RowCount
    col_count = table.ColumnCount  # Or len(table.Columns)

    data = []
    for row in range(row_count):
        row_data = {}
        for col in range(col_count):
            try:
                # Access cell by column index
                cell_value = table.GetCellValue(row, col)
                column_name = table.Columns.ElementAt(col).Name
                row_data[column_name] = cell_value
            except:
                # Fallback if column access fails
                pass
        data.append(row_data)

    return data


if __name__ == "__main__":
    extracted_data = get_sap_table_data()
    for row in extracted_data:
        print(row)
