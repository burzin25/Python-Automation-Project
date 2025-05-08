import pandas as pd
import numpy as np
import logging

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set up logging (adjust logging configuration as needed)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def preprocess_sap_alv_data(
        df: pd.DataFrame,
        columns_to_keep: list = None,
        replacement_rules: dict = None,
        missing_value_fill: dict = None,
        dtype_mapping: dict = None,
        filter_conditions: dict = None,
        none_empty_df: pd.DataFrame = None,
        date_col: str = None  # New parameter for the date column name; default is "Date"
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
         - Date columns: converted to datetime64[D] (date only).
         - Numeric columns: converted to int (using Int64 for missing values) or float.
         - Others: converted to string.
      5. Filter rows based on specified column conditions.
      6. Remove duplicate rows and reset the index.
      7. Insert "Total" in the specified date column if the last cell is empty.

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
                                  If the last cell in this column is empty or NaN, "Total" will be inserted.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """

    # If the input DataFrame is None, handle it
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

    # If the input DataFrame is empty, handle it
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

    # 1. Filter columns
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
            if desired_type == "date":
                # Convert the column to datetime and normalize (remove time component)
                dt_series = pd.to_datetime(processed_df[col], errors='coerce').dt.normalize()
                # Convert the normalized datetime series to string format "MM/DD/YYYY"
                processed_df[col] = dt_series.dt.strftime('%m/%d/%Y')
                logger.info(f"Converted column '{col}' to date format MM/DD/YYYY.")
            elif desired_type == "int":
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                processed_df[col] = processed_df[col].astype("Int64")
                logger.info(f"Converted column '{col}' to integer (Int64).")
            elif desired_type == "float":
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                processed_df[col] = processed_df[col].astype(float)
                logger.info(f"Converted column '{col}' to float.")
            elif desired_type == "str":
                processed_df[col] = processed_df[col].astype(str)
                logger.info(f"Converted column '{col}' to string.")
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

    # # 6. Remove duplicate rows.
    # processed_df.drop_duplicates(inplace=True)
    # logger.info("Removed duplicate rows.")

    # 7. Reset index.
    processed_df.reset_index(drop=True, inplace=True)
    logger.info("Reset DataFrame index.")

    # 8. Insert "Total" if the last row's cell in the specified date column is empty or NaN.
    if not processed_df.empty and date_col in processed_df.columns:
        last_idx = processed_df.index[-1]
        last_val = processed_df.at[last_idx, date_col]
        if pd.isna(last_val) or last_val == "":
            processed_df.at[last_idx, date_col] = "Total"
            logger.info(f"Set the last row's '{date_col}' to 'Total'.")

    return processed_df

# # Example usage:
# if __name__ == "__main__":
#     # Example data simulating an SAP ALV grid table.
#     data = {
#         "Product": ["  apple", "banana  ", "apple", None, "orange", "apple", "grape"],
#         "Quantity": ["10", "20", "10", "30", "", "10", "15"],
#         "Price": ["100", "200", "100", "300", "400", "100", "250"],
#         "Date": ["2022-01-01", "2022-02-15", "2022-01-01", "2022-03-10", "2022-04-20", "2022-01-01", ""],
#         "Unused Column": ["x", "y", "z", "w", "v", "z", "q"]
#     }
#     df = pd.DataFrame(data)
#
#     # Specify which columns to keep.
#     columns_to_keep = ["Product", "Quantity", "Price", "Date"]
#
#     # Specify replacement rules (e.g., remove extra spaces in the Product column).
#     replacement_rules = {
#         "Product": {"  ": " "}
#     }
#
#     # Specify missing value fill: for Quantity and Price, fill missing values with "0".
#     missing_value_fill = {
#         "Quantity": "0",
#         "Price": "0"
#     }
#
#     # Specify the desired data types for each column.
#     dtype_mapping = {
#         "Product": "str",
#         "Quantity": "int",
#         "Price": "float",
#         "Date": "date"
#     }
#
#     # Specify filter conditions: keep rows where Product is either "apple" or "banana".
#     filter_conditions = {
#         "Product": ["apple", "banana"]
#     }
#
#     cleaned_df = preprocess_sap_alv_data(
#         df,
#         columns_to_keep=columns_to_keep,
#         replacement_rules=replacement_rules,
#         missing_value_fill=missing_value_fill,
#         dtype_mapping=dtype_mapping,
#         filter_conditions=filter_conditions,
#         date_col="Date"  # You can change this if your date column is named differently
#     )
#
#     print("Preprocessed DataFrame:")
#     print(cleaned_df)
