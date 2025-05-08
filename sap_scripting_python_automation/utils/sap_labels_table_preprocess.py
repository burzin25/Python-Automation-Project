import pandas as pd
import numpy as np
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.sap_utils import logger

def preprocess_sap_label_data(
        df: pd.DataFrame,
        columns_to_keep: list = None,
        replacement_rules: dict = None,
        missing_value_fill: dict = None,
        dtype_mapping: dict = None,
        filter_conditions: dict = None,
        none_empty_df: pd.DataFrame = None,
        date_col: str = None # New parameter for date column name
) -> pd.DataFrame:
    """
    Preprocesses raw SAP ALV grid data with multiple customizable operations.

    Operations performed:
      1. Filter the DataFrame to only include specified columns.
      2. Replace specific characters in specified columns.
      3. Handle missing values:
         - Replaces empty strings with NaN.
         - Optionally fills missing values with provided fill values.
      4. Convert columns to specified data types safely:
         - Date columns: converted to datetime64[D] (date only) and then formatted as strings.
         - Numeric columns: converted to int (using Int64 for missing values) or float.
         - Others: converted to string.
      5. Filter rows based on specified column conditions.
      6. Remove duplicate rows and reset the index.
      7. If the specified date column's last cell is empty, insert "Total".

    Args:
        df (pd.DataFrame): The raw DataFrame.
        columns_to_keep (list, optional): List of column names to retain.
        replacement_rules (dict, optional): Dictionary of replacement rules.
               Format: { column_name: {target: replacement, ...} }
        missing_value_fill (dict, optional): Dictionary of fill values for missing data.
               Format: { column_name: fill_value, ... }
        dtype_mapping (dict, optional): Mapping of column names to desired data types.
               Supported types (as strings): "date", "int", "float", "str".
        filter_conditions (dict, optional): Dictionary of filter conditions.
               Format: { column_name: value or list of acceptable values, ... }
        none_empty_df (pd.DataFrame, optional): A DataFrame to use if the input DataFrame is None or empty.
        date_col (str, optional): The name of the column that holds date values.
                                    This column will be checked, and if its last cell is empty,
                                    "Total" will be inserted.
    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """

    # If the input DataFrame is None, handle it.
    if df is None:
        logger.warning("Input DataFrame is None.")
        if none_empty_df is not None:
            logger.info("Using provided none_empty_df as the output.")
            return none_empty_df
        else:
            logger.info("Creating an empty DataFrame with specified columns_to_keep.")
            if columns_to_keep:
                return pd.DataFrame(columns=columns_to_keep)
            else:
                return pd.DataFrame()

    # If the input DataFrame is empty, handle it.
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        if none_empty_df is not None:
            logger.info("Using provided none_empty_df as the output.")
            return none_empty_df
        else:
            logger.info("Returning an empty DataFrame with specified columns_to_keep.")
            if columns_to_keep:
                existing_columns = [col for col in columns_to_keep if col in df.columns]
                missing_columns = [col for col in columns_to_keep if col not in df.columns]
                if missing_columns:
                    logger.warning(f"Columns not found and will be ignored: {missing_columns}")
                return df.loc[:, existing_columns]
            else:
                return df

    # Work on a copy to avoid modifying the original DataFrame.
    processed_df = df.copy()

    # 1. Filter columns.
    if columns_to_keep:
        existing_columns = [col for col in columns_to_keep if col in processed_df.columns]
        missing_columns = [col for col in columns_to_keep if col not in processed_df.columns]
        if missing_columns:
            logger.warning(f"Columns not found and will be ignored: {missing_columns}")
        processed_df = processed_df.loc[:, existing_columns]
        logger.info(f"Retained columns: {existing_columns}")

    # 2. Replace specific characters in specific columns.
    if replacement_rules:
        for col, rules in replacement_rules.items():
            if col in processed_df.columns:
                # Convert to string before applying replacements.
                processed_df[col] = processed_df[col].astype(str)
                for target, replacement in rules.items():
                    processed_df[col] = processed_df[col].str.replace(target, replacement, regex=False)
                logger.info(f"Applied replacement rules on column: {col}")
            else:
                logger.warning(f"Replacement rule specified for missing column: {col}")

    # 3. Handle missing values.
    processed_df.replace("", np.nan, inplace=True)
    logger.info("Replaced empty strings with NaN.")

    if missing_value_fill:
        for col, fill_value in missing_value_fill.items():
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna(fill_value)
                logger.info(f"Filled missing values in column '{col}' with '{fill_value}'.")
            else:
                logger.warning(f"Missing value fill rule specified for missing column: {col}")

    # 4. Convert columns to specified data types safely.
    if dtype_mapping:
        for col, desired_type in dtype_mapping.items():
            if col not in processed_df.columns:
                logger.warning(f"Data type conversion rule specified for missing column: {col}")
                continue

            desired_type = desired_type.lower() if isinstance(desired_type, str) else str(desired_type).lower()

            # For numeric types, ensure the default is numeric (0); for date and string types, default to an empty string.
            if desired_type in ["int", "float"]:
                default_val = missing_value_fill.get(col, 0) if missing_value_fill else 0
                # If the provided default value is not numeric, force it to 0.
                try:
                    default_val = float(default_val)
                except (ValueError, TypeError):
                    default_val = 0
            else:
                default_val = missing_value_fill.get(col, "") if missing_value_fill else ""

            # Fill missing values in the column with the default.
            processed_df[col] = processed_df[col].fillna(default_val)

            if desired_type == "date":
                try:
                    # Ensure all values are strings and strip spaces
                    processed_df[col] = processed_df[col].astype(str).str.strip()
                    # Replace obvious bad values with NaN
                    processed_df[col] = processed_df[col].replace(["", "nan", "NaN", "None", "null"], pd.NA)
                    # Convert to datetime, coerce errors to NaT
                    dt_series = pd.to_datetime(processed_df[col], errors='coerce').dt.normalize()
                    # Format to MM/DD/YYYY and fill missing with empty string
                    processed_df[col] = dt_series.dt.strftime('%m/%d/%Y').fillna("")
                    logger.info(f"Converted column '{col}' to date format MM/DD/YYYY.")
                except Exception as e:
                    logger.error(f"Failed to convert column '{col}' to date: {e}")

            elif desired_type == "int":
                try:
                    # Remove commas and whitespace just in case
                    processed_df[col] = processed_df[col].astype(str).str.replace(",", "").str.strip()
                    # Convert to numeric safely
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                    # Fill and convert to nullable integer
                    processed_df[col] = processed_df[col].fillna(default_val).astype("Int64")
                    logger.info(f"Converted column '{col}' to integer (Int64).")
                except Exception as e:
                    logger.error(f"Failed to convert column '{col}' to Int64: {e}")


            elif desired_type == "float":
                try:
                    # Pre-clean: remove commas and trim spaces
                    processed_df[col] = processed_df[col].astype(str).str.replace(",", "").str.strip()
                    # Convert to numeric (floats), coerce bad values to NaN
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                    # Fill NaNs and convert to float
                    processed_df[col] = processed_df[col].fillna(default_val).astype(float)
                    logger.info(f"Converted column '{col}' to float.")
                except Exception as e:
                    logger.error(f"Failed to convert column '{col}' to float: {e}")

            elif desired_type == "str":
                try:
                    # Convert to string, strip whitespace, and replace 'nan' with empty string
                    processed_df[col] = processed_df[col].astype(str).str.strip().replace("nan", "")
                    logger.info(f"Converted column '{col}' to string.")
                except Exception as e:
                    logger.error(f"Failed to convert column '{col}' to string: {e}")

        else:
                logger.warning(f"Unsupported data type '{desired_type}' for column '{col}'. No conversion applied.")

    # 5. Filter rows based on specified column conditions.
    if filter_conditions:
        for col, condition in filter_conditions.items():
            if col not in processed_df.columns:
                logger.warning(f"Filter condition specified for missing column: {col}")
                continue
            if isinstance(condition, list):
                processed_df = processed_df[processed_df[col].isin(condition)]
                logger.info(f"Filtered rows where column '{col}' is in {condition}.")
            else:
                processed_df = processed_df[processed_df[col] == condition]
                logger.info(f"Filtered rows where column '{col}' equals {condition}.")

    # 6. Remove duplicate rows.
    processed_df.drop_duplicates(inplace=True)
    logger.info("Removed duplicate rows.")

    # 7. Reset index.
    processed_df.reset_index(drop=True, inplace=True)
    logger.info("Reset DataFrame index.")

    # 8. Insert "Total" if the last row's cell in the specified date column is empty or NaN.
    if not processed_df.empty and date_col in processed_df.columns:
        last_idx = processed_df.index[-1]
        last_val = processed_df.at[last_idx, date_col]
        # Check if it's NaN or an empty string
        if pd.isna(last_val) or last_val == "":
            processed_df.at[last_idx, date_col] = "Total"
            logger.info(f"Set the last row's '{date_col}' to 'Total'.")

    return processed_df
