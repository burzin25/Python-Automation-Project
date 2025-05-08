#!/usr/bin/env python
"""
user_management_light.py

A lightweight command-line tool for managing user IDs and passwords.
User credentials are stored in a JSON file (users.json) with passwords securely hashed using bcrypt.
This tool is intended for use by an administrator.
"""

import os
import sys
import json
import bcrypt

# File to store user credentials
CREDENTIALS_FILE = "users.json"


def load_credentials():
    """Load credentials from the JSON file; return an empty dict if file doesn't exist."""
    if not os.path.exists(CREDENTIALS_FILE):
        return {}
    with open(CREDENTIALS_FILE, "r") as f:
        try:
            data = json.load(f)
            # Ensure data is a dictionary
            if isinstance(data, dict):
                return data
            else:
                return {}
        except json.JSONDecodeError:
            return {}


def save_credentials(creds):
    """Save the credentials dictionary to the JSON file."""
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=4)


def add_user(username, password):
    """Add a new user with the given plaintext password."""
    creds = load_credentials()
    if username in creds:
        print(f"Error: User '{username}' already exists.")
        return
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # Store the hash as a UTF-8 string.
    creds[username] = hashed.decode("utf-8")
    save_credentials(creds)
    print(f"User '{username}' added successfully.")


def remove_user(username):
    """Remove the user with the given username."""
    creds = load_credentials()
    if username not in creds:
        print(f"User '{username}' does not exist.")
        return
    del creds[username]
    save_credentials(creds)
    print(f"User '{username}' removed successfully.")


def update_user(username, new_password):
    """Update the password for the given user."""
    creds = load_credentials()
    if username not in creds:
        print(f"User '{username}' does not exist.")
        return
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), salt)
    creds[username] = hashed.decode("utf-8")
    save_credentials(creds)
    print(f"Password for '{username}' updated successfully.")


def list_users():
    """List all usernames."""
    creds = load_credentials()
    if not creds:
        print("No users found.")
    else:
        print("Existing users:")
        for username in creds:
            print(f" - {username}")


def get_password(prompt="Enter password: "):
    """Securely read a password from the terminal without echoing."""
    try:
        # Use getpass if available
        import getpass
        return getpass.getpass(prompt).strip()
    except Exception:
        # Fallback to plain input if getpass fails
        print("Warning: Password input will be visible.")
        return input(prompt).strip()


def main():
    # Check if the credentials file exists and print a status message.
    if os.path.exists(CREDENTIALS_FILE):
        creds = load_credentials()
        if creds:
            print("users.json found and loaded successfully.")
        else:
            print("users.json found but is empty or invalid. Starting with an empty credential set.")
    else:
        print("users.json not found. Starting with an empty credential set.")

    while True:
        print("\nUser Management Menu")
        print("====================")
        print("1. Add user")
        print("2. Remove user")
        print("3. Update user password")
        print("4. List users")
        print("5. Exit")
        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            username = input("Enter new username: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            password = get_password("Enter password: ")
            if not password:
                print("Password cannot be empty.")
                continue
            add_user(username, password)
        elif choice == "2":
            username = input("Enter username to remove: ").strip()
            if username:
                remove_user(username)
            else:
                print("Username cannot be empty.")
        elif choice == "3":
            username = input("Enter username to update: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            new_password = get_password("Enter new password: ")
            if not new_password:
                print("Password cannot be empty.")
                continue
            update_user(username, new_password)
        elif choice == "4":
            list_users()
        elif choice == "5":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main()