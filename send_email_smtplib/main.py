# Birthday Email Automation App

"""
Logic of the Code:
This application automatically sends birthday emails to people on their birthdays.
- It reads a list of birthdays from a CSV file.
- It checks if today's date matches any person's birthday.
- If a match is found, it picks a random letter template, personalizes it, and sends an email via SMTP.
"""

import pandas as pd
import smtplib
import datetime as dt
import random

# Your email credentials
MY_EMAIL = "your_email_id@gmail.com"    # <-- Change this to your email ID
PASSWORD = "your_password"               # <-- Change this to your email password

# 1. Read the birthday CSV
def load_birthdays(csv_path="birthdays.csv"):
    """
    Loads the birthday data from a CSV file into a pandas DataFrame.

    Args:
        csv_path (str): Path to the CSV file containing birthday information.

    Returns:
        pd.DataFrame: DataFrame containing all birthdays.
    """
    return pd.read_csv(csv_path)

# 2. Check if today matches any birthday
def find_birthday_matches(birthdays_df):
    """
    Checks if today's month and day match any entry in the birthdays DataFrame.

    Args:
        birthdays_df (pd.DataFrame): DataFrame with 'month' and 'day' columns.

    Returns:
        pd.DataFrame: Rows where today matches the birthday.
    """
    today = (dt.datetime.now().month, dt.datetime.now().day)
    matches = birthdays_df[(birthdays_df['month'] == today[0]) & (birthdays_df['day'] == today[1])]
    return matches

# 3. Send Email
def send_birthday_email(to_email, name):
    """
    Sends a personalized birthday email to the specified recipient.

    Args:
        to_email (str): Recipient's email address.
        name (str): Recipient's name.
    """
    letter_templates = ["letter_1.txt", "letter_2.txt", "letter_3.txt"]
    letter_file = random.choice(letter_templates)

    # Read the letter template and personalize it
    with open(f"templates/{letter_file}") as letter:
        content = letter.read()
        personalized_content = content.replace("[NAME]", name)

    # Send the email
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()  # Secure the connection
        connection.login(user=MY_EMAIL, password=PASSWORD)  # Login to the email server
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=to_email,
            msg=f"Subject:Happy Birthday {name}!\n\n{personalized_content}"
        )

# 4. Main app logic
def main():
    """
    Main function that loads the birthday list, finds matches, and sends emails.
    """
    birthdays = load_birthdays()               # Load the list of birthdays
    matches = find_birthday_matches(birthdays) # Find if anyone's birthday is today

    for _, row in matches.iterrows():
        send_birthday_email(row['email'], row['name'])  # Send email to each match

if __name__ == "__main__":
    main()  # Run the app