"""
Module: sap_label_formatter
Description: Formats extracted SAP label data into structured tables based on user-defined parameters.
"""

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from typing import Optional, List, Dict
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.sap_utils import logger



def format_extracted_labels_table(
    df: pd.DataFrame,
    title_row: Optional[int] = None,
    title_col: Optional[int] = None,
    header_row: Optional[int] = None,
    header_col: Optional[int] = None,
    data_row: Optional[int] = None,
    split_instructions: Optional[List[Dict[str, Optional[str]]]] = None
) -> Optional[pd.DataFrame]:
    """
    Formats extracted label data into structured tables based on user-defined parameters.

    Optionally, a list of split instructions can be provided to split multiple columns. Each instruction should be a dict with:
        - 'split_col': original column name to split.
        - 'new_col_names': string with two new column names separated by a delimiter (e.g., "Local date,shift(72/7400)").
        - 'col_name_delimiter': delimiter for splitting the new_col_names string.
        - 'value_delimiter': delimiter for splitting the values in the specified column (if None, splits on whitespace).
    """
    try:
        if df is None or df.empty:
            logger.error("Received an empty DataFrame. Cannot format.")
            return None

        # Extract table title
        table_title = (
            df.loc[df['Row'] == title_row, title_col].values[0]
            if title_col in df.columns and not df.loc[df['Row'] == title_row, title_col].isnull().all()
            else None
        )

        # Extract column headers
        headers = df[df['Row'] >= header_row].set_index('Row').iloc[:, header_col:].dropna(how='all')
        if not headers.empty:
            headers.columns = headers.iloc[0]  # Set first row as column names
            headers = headers[1:].reset_index(drop=True)  # Remove header row from data
        else:
            logger.error("No headers found in the provided DataFrame.")
            return None

        # Extract table data
        table_data = df[df['Row'] >= data_row].set_index('Row').iloc[:, header_col:].dropna(how='all')
        table_data.columns = headers.columns  # Assign headers to data

        # Process each split instruction if provided
        if split_instructions:
            for instruction in split_instructions:
                split_col = instruction.get("split_col")
                new_col_names = instruction.get("new_col_names")
                col_name_delimiter = instruction.get("col_name_delimiter")
                value_delimiter = instruction.get("value_delimiter")

                if not split_col or not new_col_names or col_name_delimiter is None:
                    logger.error("Incomplete split instruction provided. Skipping this instruction.")
                    continue

                if split_col not in table_data.columns:
                    logger.error(f"Column '{split_col}' not found in table data. Skipping this instruction.")
                    continue

                # Split the new_col_names string to get the two new names.
                new_names = new_col_names.split(col_name_delimiter)
                if len(new_names) != 2:
                    logger.error("Please provide exactly two new column names separated by the col_name_delimiter.")
                    continue

                # Split the values in the specified column.
                # If value_delimiter is None, splitting defaults to any whitespace.
                split_values = table_data[split_col].astype(str).str.split(value_delimiter, expand=True)
                if split_values.shape[1] != 2:
                    logger.error(f"Splitting the values in '{split_col}' did not produce exactly 2 columns. Skipping this instruction.")
                    continue

                # Rename the new columns.
                split_values.columns = new_names

                # Drop the original column and join the new columns.
                table_data = table_data.drop(columns=[split_col]).join(split_values)

        logger.info("✅ Successfully formatted extracted data.")
        return table_data if not table_data.empty else None

    except Exception as e:
        logger.error(f"Error formatting extracted labels: {e}")
        return None


# # Example usage:
# if __name__ == "__main__":
#     # Sample DataFrame mimicking your extracted SAP label data.
#     # For demonstration, assume after processing headers, one column is named "Local date + shift (72/7400)".
#     data = {
#         'Row': [1, 2, 3, 4, 5],
#         0: ['Title', None, 'Local date + shift (72/7400)', 'Other Column', '20250211   1'],
#         1: [None, None, None, None, 'SomeValue']
#     }
#     df_sample = pd.DataFrame(data)
#
#     # Parameters for table extraction:
#     title_row = 1
#     title_col = 0
#     header_row = 3
#     header_col = 0
#     data_row = 5
#
#     # List of split instructions.
#     # In this example, we want to split "Local date + shift (72/7400)" into "Local date" and "shift(72/7400)".
#     split_instructions = [
#         {
#             "split_col": "Local date + shift (72/7400)",
#             "new_col_names": "Local date,shift(72/7400)",
#             "col_name_delimiter": ",",
#             "value_delimiter": None  # None indicates split on any whitespace
#         }
#         # You can add more split instructions here as needed.
#     ]
#
#     formatted_df = format_extracted_labels_table(
#         df_sample,
#         title_row=title_row,
#         title_col=title_col,
#         header_row=header_row,
#         header_col=header_col,
#         data_row=data_row,
#         split_instructions=split_instructions
#     )
#
#     print(formatted_df)
