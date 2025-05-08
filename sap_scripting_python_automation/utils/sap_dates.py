import sys
import calendar
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

# Constants for input and output date formats.
INPUT_DATE_FORMAT = "%m/%d/%Y"  # e.g., "03/15/2025"
OUTPUT_DATE_FORMAT = "%m/%d/%Y"  # e.g., "03/15/2025"

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DateError(Exception):
    """Custom exception for date processing errors."""
    pass


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object using the INPUT_DATE_FORMAT.

    Args:
        date_str (str): Date string in the expected format.

    Returns:
        datetime: Parsed datetime object.

    Raises:
        DateError: If the date string does not match the expected format.
    """
    try:
        return datetime.strptime(date_str, INPUT_DATE_FORMAT)
    except ValueError as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        raise DateError(f"Invalid date format: '{date_str}'. Expected format: {INPUT_DATE_FORMAT}") from e


def prompt_for_date(prompt_text: str, mandatory: bool = True) -> str:
    """
    Prompt the user for a date input and validate the format.

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
        sys.exit("Date input is required to run the transaction.")

    if date_input:
        try:
            parse_date(date_input)
            return date_input
        except DateError:
            sys.exit("Date entered incorrectly. Use the specified format and try again.")
    return date_input


def get_user_dates() -> Tuple[str, str, str]:
    """
    Prompt the user for FROM and TO dates and compute the start of the month from FROM DATE.

    Returns:
        Tuple[str, str, str]: (from_date, to_date, start_date_of_month) in "MM/DD/YYYY" format.
    """
    from_date_input = prompt_for_date("Enter FROM DATE (MM/DD/YYYY): ", mandatory=True)
    to_date_input = prompt_for_date("Enter TO DATE (MM/DD/YYYY, leave blank if not applicable): ", mandatory=False)

    from_date_obj = parse_date(from_date_input)
    from_date_formatted = from_date_obj.strftime(OUTPUT_DATE_FORMAT)

    if to_date_input == "":
        to_date_formatted = ""
    else:
        to_date_obj = parse_date(to_date_input)
        to_date_formatted = to_date_obj.strftime(OUTPUT_DATE_FORMAT)

    start_date_obj = from_date_obj.replace(day=1)
    start_date_formatted = start_date_obj.strftime(OUTPUT_DATE_FORMAT)

    return from_date_formatted, to_date_formatted, start_date_formatted


def get_dates() -> Tuple[str, str, str]:
    """
    Retrieve date parameters either from command-line arguments or by prompting the user.

    Expected command-line arguments (when provided by the Admin Task Window):
        sys.argv[1] = FROM DATE (in "MM/DD/YYYY" format)
        sys.argv[2] = TO DATE (in "MM/DD/YYYY" format or "None")

    Returns:
        Tuple[str, str, str]: (from_date, to_date, start_date_of_month) in "MM/DD/YYYY" format.
    """
    if len(sys.argv) >= 3:
        from_date_arg = sys.argv[1]
        to_date_arg = sys.argv[2].strip()
        if to_date_arg.lower() == "none":
            to_date_arg = ""
        try:
            from_date_obj = parse_date(from_date_arg)
            from_date_formatted = from_date_obj.strftime(OUTPUT_DATE_FORMAT)
            if to_date_arg:
                to_date_obj = parse_date(to_date_arg)
                to_date_formatted = to_date_obj.strftime(OUTPUT_DATE_FORMAT)
            else:
                to_date_formatted = ""
            start_date_formatted = from_date_obj.replace(day=1).strftime(OUTPUT_DATE_FORMAT)
            logger.info("Dates provided via command-line arguments will be used.")
            return from_date_formatted, to_date_formatted, start_date_formatted
        except DateError as e:
            logger.error(f"Invalid command-line date argument: {e}")
            sys.exit(1)
    else:
        logger.info("No command-line dates provided. Prompting user for date input.")
        return get_user_dates()


def get_end_date_of_month(date_obj: datetime) -> str:
    """
    Calculate the last date of the month for the given date.

    Args:
        date_obj (datetime): A datetime object representing any day within the month.

    Returns:
        str: The end date of the month in "MM/DD/YYYY" format.
    """
    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
    end_date_obj = date_obj.replace(day=last_day)
    return end_date_obj.strftime(OUTPUT_DATE_FORMAT)


def list_dates_in_month(date_obj: datetime) -> list:
    """
    Generate a list of all dates for the month of the given date.

    Args:
        date_obj (datetime): A datetime object for any day in the month.

    Returns:
        list: A list of date strings (in "MM/DD/YYYY" format) from the first to the last day of the month.
    """
    start_date = date_obj.replace(day=1)
    # Use the already defined get_end_date_of_month to get the end date as a string and then parse it.
    end_date = parse_date(get_end_date_of_month(date_obj))
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime(OUTPUT_DATE_FORMAT))
        current_date += timedelta(days=1)
    return date_list


def workday_flag(date_obj: datetime) -> int:
    """
    Determine whether a given date is a workday or a weekend.

    Args:
        date_obj (datetime): The date to evaluate.

    Returns:
        int: 1 if the date is a weekday (Monday-Friday), 0 if it is a weekend (Saturday or Sunday).
    """
    # In Python, weekday() returns 0 for Monday ... 6 for Sunday.
    return 1 if date_obj.weekday() < 5 else 0


if __name__ == "__main__":
    # For standalone testing: prompt for dates.
    from_date, to_date, month_start_date = get_dates()
    print(f"FROM DATE: {from_date}")
    print(f"TO DATE: {to_date}")
    print(f"START DATE OF THE MONTH: {month_start_date}")

    # Demonstrate the use of get_end_date_of_month using the FROM DATE.
    from_date_obj = parse_date(from_date)
    month_end_date = get_end_date_of_month(from_date_obj)
    print(f"END DATE OF THE MONTH: {month_end_date}")

    # List all dates for the month of from_date.
    dates_of_month = list_dates_in_month(from_date_obj)
    print("\nAll dates in the month:")
    for date_str in dates_of_month:
        print(date_str)

    # For each date, print whether it's a workday (1) or weekend (0).
    print("\nWorkday flag for each date (1 for workday, 0 for weekend):")
    for date_str in dates_of_month:
        current_date_obj = parse_date(date_str)
        flag = workday_flag(current_date_obj)
        print(f"{date_str}: {flag}")
