import calendar
from datetime import datetime
from typing import Optional, Tuple
import logging
import argparse
import sys

# Constants
DATE_FORMAT = "%m-%d-%Y"
COLUMN_MULTIPLIER = 3

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class SAPDateError(Exception):
    """Custom exception for SAP date processing errors."""
    pass


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.

    Args:
        date_str (str): Date string in the format "MM-DD-YYYY".

    Returns:
        datetime: Parsed datetime object.

    Raises:
        SAPDateError: If the date string does not match the expected format.
    """
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        raise SAPDateError(f"Invalid date format: '{date_str}'. Expected format: {DATE_FORMAT}") from e


def get_sap_calendar_id(target_date: Optional[str]) -> Optional[str]:
    """
    Generate the SAP Calendar ID for a given date.

    The SAP Calendar ID is formatted as "DAYXX[week_index,column_index]", where:
      - XX: Day of week (Monday=01, Tuesday=02, etc.)
      - week_index: Zero-based index of the week in the month's calendar matrix.
      - column_index: Calculated as (day_of_week * COLUMN_MULTIPLIER).

    Args:
        target_date (Optional[str]): Date string in "MM-DD-YYYY" format.

    Returns:
        Optional[str]: The generated SAP Calendar ID, or None if target_date is None or an error occurs.
    """
    if target_date is None:
        logger.info("Target date is None. Returning None.")
        return None

    try:
        logger.info(f"Processing target date: {target_date}")
        date_obj = parse_date(target_date)
        year, month, day = date_obj.year, date_obj.month, date_obj.day

        # Validate that the day is within the valid range for the month.
        last_day = calendar.monthrange(year, month)[1]
        if not (1 <= day <= last_day):
            raise SAPDateError(f"Invalid day {day} for month {month} in year {year}.")

        # Retrieve the month's calendar as a matrix (weeks as rows).
        month_calendar = calendar.monthcalendar(year, month)

        # Find the week (row) that contains the day.
        week_index = next((idx for idx, week in enumerate(month_calendar) if day in week), None)
        if week_index is None:
            raise SAPDateError(f"Could not find the week for day {day} in month {month}.")

        day_of_week = date_obj.weekday()  # Monday=0, Sunday=6
        column_index = day_of_week * COLUMN_MULTIPLIER

        sap_id = f"DAY{day_of_week + 1:02d}[{week_index},{column_index}]"
        logger.info(f"Generated SAP Calendar ID: {sap_id}")
        return sap_id

    except SAPDateError as e:
        logger.error(f"Error generating SAP Calendar ID: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error processing {target_date}: {e}")
        return None


def get_first_day_of_month_sap_id(from_date: str) -> Optional[Tuple[str, str, str]]:
    """
    Calculate the first day of the month details based on the provided FROM DATE.

    This function returns a tuple containing:
      - The Year in "YYYY" format,
      - The Month as a single digit string (e.g., "1" for January),
      - The SAP Calendar ID for the first day of the month.

    Args:
        from_date (str): Date string in "MM-DD-YYYY" format.

    Returns:
        Optional[Tuple[str, str, str]]: A tuple (year, month, start_month_sap_id)
                                        or None if an error occurs.
    """
    try:
        logger.info(f"Calculating first day SAP Calendar ID from date: {from_date}")
        date_obj = parse_date(from_date)
        # Get the year and month; month is converted to a single-digit string if applicable.
        year_str = str(date_obj.year)
        month_str = str(date_obj.month)  # This returns "1" for January, "2" for February, etc.
        # Set the day to 1 to get the first day of the month.
        first_day_date = date_obj.replace(day=1)
        first_day_str = first_day_date.strftime(DATE_FORMAT)
        start_month_sap_id = get_sap_calendar_id(first_day_str)
        logger.info(f"Year: {year_str}, Month: {month_str}, First day SAP Calendar ID: {start_month_sap_id}")
        return year_str, month_str, start_month_sap_id
    except SAPDateError as e:
        logger.error(f"Error in get_first_day_of_month_sap_id: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in get_first_day_of_month_sap_id: {e}")
        return None


def calculate_sap_calendar_ids(from_date: str, to_date: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Calculate SAP Calendar IDs for both the FROM and TO dates.

    Args:
        from_date (str): Date string in "MM-DD-YYYY" format.
        to_date (Optional[str]): Date string in "MM-DD-YYYY" format (optional).

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing the SAP Calendar IDs for the FROM and TO dates.
    """
    try:
        logger.info(f"Calculating SAP Calendar IDs for FROM date: {from_date} and TO date: {to_date}")
        from_date_sap_id = get_sap_calendar_id(from_date)
        to_date_sap_id = get_sap_calendar_id(to_date) if to_date else None
        logger.info(f"FROM date SAP Calendar ID: {from_date_sap_id}")
        logger.info(f"TO date SAP Calendar ID: {to_date_sap_id}")
        return from_date_sap_id, to_date_sap_id
    except Exception as e:
        logger.exception(f"Unexpected error in calculate_sap_calendar_ids: {e}")
        return None, None


def prompt_for_date(prompt_text: str, mandatory: bool = True) -> str:
    """
    Prompt the user for a date input and validate the format.
    If the input is invalid, cancel execution and instruct the user to use the specified format.

    Args:
        prompt_text (str): The text to display to the user.
        mandatory (bool): Whether the input is mandatory.

    Returns:
        str: A valid date string in the expected format.
    """
    try:
        date_input = input(prompt_text).strip()
    except KeyboardInterrupt:
        print("\nUser aborted input.")
        sys.exit(1)

    if mandatory and not date_input:
        sys.exit("Failed to run the transaction, Enter the From Date to run the transaction")

    if date_input:
        try:
            parse_date(date_input)
            return date_input
        except SAPDateError:
            sys.exit("Date entered incorrect, use the specified format and run the program again")
    return date_input


def main(args=None):
    """
    Interactive main function to execute SAP Calendar ID calculations.

    It prints exactly three output lines showing:
      - The ID for From Date
      - The ID for To Date
      - The Year, Month, and Start Date SAP ID for the month (from the FROM DATE)
    """
    parser = argparse.ArgumentParser(description="Generate SAP Calendar IDs based on input dates.")
    parser.add_argument("--from_date", type=str, help="FROM DATE in MM-DD-YYYY format", required=False)
    parser.add_argument("--to_date", type=str, help="TO DATE in MM-DD-YYYY format (optional)", required=False)
    parsed_args = parser.parse_args(args)

    from_date = parsed_args.from_date.strip() if parsed_args.from_date else ""
    to_date = parsed_args.to_date.strip() if parsed_args.to_date else ""

    # Validate FROM DATE (mandatory).
    if from_date:
        try:
            parse_date(from_date)
        except SAPDateError as e:
            logger.error(f"Invalid FROM DATE provided via command-line: {e}")
            sys.exit("Date entered incorrect, use the specified format and run the program again")
    else:
        from_date = prompt_for_date("Enter FROM DATE (MM-DD-YYYY): ", mandatory=True)

    # Validate TO DATE (if provided).
    if to_date:
        try:
            parse_date(to_date)
        except SAPDateError as e:
            logger.error(f"Invalid TO DATE provided via command-line: {e}")
            sys.exit("Date entered incorrect, use the specified format and run the program again")
    else:
        to_date = prompt_for_date("Enter TO DATE (MM-DD-YYYY, leave blank if not applicable): ", mandatory=False)
        if to_date == "":
            to_date = None

    from_date_sap_id, to_date_sap_id = calculate_sap_calendar_ids(from_date, to_date)
    first_day_info = get_first_day_of_month_sap_id(from_date)

    # Print exactly three output lines.
    print(f"The ID for From Date : {from_date_sap_id}")
    print(f"The ID for To Date : {to_date_sap_id}")
    if first_day_info:
        year_str, month_str, start_month_sap_id = first_day_info
        print(f"Year: {year_str}, Month: {month_str}, The ID for Start Date of the month : {start_month_sap_id}")
    else:
        print("Failed to calculate first day information for the month.")


# When imported as a module, the interactive main() will not execute.
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
