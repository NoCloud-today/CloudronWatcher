"""
This module provides utility functions for interacting with the Cloudron API, 
specifically for fetching notifications and marking them as acknowledged.

Imports:
    - requests: Used for making HTTP requests to the Cloudron API.
    - sys: Used for system-specific parameters and functions.
    - os: Used for interacting with the operating system, including reading environment variables.
    - dotenv: Used for loading environment variables from a .env file.

Environment Variables:
    - CLOUDRON_TOKEN: The API token for accessing the Cloudron API.
    - CLOUDRON_DOMAIN: The domain of the Cloudron instance.

Functions:
    - get_cloudron_notifications(): Fetches notifications from the Cloudron API.
    - mark_notification_as_acknowledged(notification_id: str): Marks a specific notification as acknowledged in the Cloudron API.

Usage:
    - This module is intended to be imported by other scripts in the project that need to interact with the Cloudron API for notifications.
"""

import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv(".env")


def get_cloudron_notifications() -> list:
    """
    Retrieves notifications from the Cloudron API.

    This function fetches notifications from the Cloudron API using the API key and domain specified in the environment variables.
    If the API call is successful, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Returns:
        list: A list of notifications received from the Cloudron API.
    """
    cloudron_api_key = os.getenv('CLOUDRON_TOKEN')
    cloudron_domain = os.getenv('CLOUDRON_DOMAIN')

    if not cloudron_api_key or not cloudron_domain:
        sys.stderr.write(
            "\033[41mConfiguration error: Check the CLOUDFRONT_TOKEN and CLOUDFRONT_DOMAIN environment variables.\033[0m\n")
        sys.stderr.flush()
        return []

    headers = {'Authorization': f'Bearer {cloudron_api_key}'}
    url = f"https://{cloudron_domain}/api/v1/notifications"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\033[41mError receiving notifications: {e}\n\033[0m\n")
        sys.stderr.flush()
        return []

    sys.stdout.write("\033[92mNotifications were successfully received via the Cloudron API\n\033[0m\n")
    sys.stdout.flush()
    return response.json()


def mark_notification_as_acknowledged(notification_id: str) -> None:
    """
    Marks a specific notification as acknowledged in the Cloudron API.

    This function sends a POST request to the Cloudron API to mark a notification as acknowledged.
    The notification ID is passed as a parameter. If the API call is successful, it prints a success message to stdout.
    In case of an error, it prints an error message to stderr.

    Parameters:
        notification_id (str): The ID of the notification to be marked as acknowledged.
    """
    cloudron_api_key = os.getenv('CLOUDRON_TOKEN')
    cloudron_domain = os.getenv('CLOUDRON_DOMAIN')

    if not cloudron_api_key or not cloudron_domain:
        sys.stderr.write(
            "\033[90mConfiguration error: Check the CLOUDRON_TOKEN and CLOUDRON_DOMAIN environment variables.\033[0m\n")
        sys.stderr.flush()
        return []

    headers = {'Authorization': f'Bearer {cloudron_api_key}'}
    data = {"acknowledged": True}

    url = f"https://{cloudron_domain}/api/v1/notifications/{notification_id}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\033[41mError when marking a notification as read: {e}\n\033[0m")
        sys.stderr.flush()
        return
    
    sys.stdout.write(
            f"\033[92mNotifications #{notification_id} have been successfully marked as read\n\033[0m\n")
    sys.stdout.flush()
    return
