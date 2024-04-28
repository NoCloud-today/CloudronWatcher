"""
cloudron_monitor.py

This script is a monitoring tool for Cloudron. 
It is responsible for fetching notifications from Cloudron,
sending unacknowledged notifications to a messaging service, 
and marking notifications as acknowledged in Cloudron.

Features:
- Retrieves notifications from the Cloudron.
- Sends notifications using a specified cURL command.
- Marks notifications as acknowledged in the Cloudron.

Environment Variables from setting.ini:
- CLOUDRON_TOKEN: The API token for Cloudron.
- CLOUDRON_DOMAIN: The domain of the Cloudron instance.
- COMMAND_CURL: The bash command to send notifications.

Usage:
- Ensure the environment variables are set correctly.
- Run the script to fetch and process notifications.
"""
import configparser
import json
import subprocess
import sys
import requests
from urllib.parse import quote
from datetime import datetime

config = configparser.ConfigParser()
config.read("settings.ini")

cloudron_api_key = config['CloudronAPI']['CLOUDRON_TOKEN']
cloudron_domain = config["CloudronAPI"]["CLOUDRON_DOMAIN"]
bash_command = config['Messanger']['COMMAND_CURL']
message_template = config['Messanger']['MESSAGE_TEMPLATE']


def get_cloudron_notifications() -> list:
    """
    Retrieves notifications from the Cloudron API.

    This function fetches notifications from the Cloudron API using the API key and domain specified in the environment variables.
    If the API call is successful, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Returns:
        list: A list of notifications received from the Cloudron API.
    """

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
        sys.stderr.write(
            f"\033[41mError receiving notifications: {e}\n\033[0m\n")
        sys.stderr.flush()
        return []

    sys.stdout.write(
        "\033[92mNotifications were successfully received via the Cloudron API\n\033[0m\n")
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

    if not cloudron_api_key or not cloudron_domain:
        sys.stderr.write(
            "\033[90mConfiguration error: Check the CLOUDRON_TOKEN and CLOUDRON_DOMAIN environment variables.\033[0m\n")
        sys.stderr.flush()
        return

    headers = {'Authorization': f'Bearer {cloudron_api_key}'}
    data = {"acknowledged": True}

    url = f"https://{cloudron_domain}/api/v1/notifications/{notification_id}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(
            f"\033[41mError when marking a notification as read: {e}\n\033[0m")
        sys.stderr.flush()
        return

    sys.stdout.write(
        f"\033[92mNotifications #{notification_id} have been successfully marked as read\n\033[0m\n")
    sys.stdout.flush()
    return


if __name__ == '__main__':
    responses = get_cloudron_notifications()

    if responses == []:
        exit(1)

    for notification in responses['notifications']:
        if not notification['acknowledged']:
            message_content = message_template.replace(
                "{id}", notification['id'].replace('`', ''))
            message_content = message_content.replace(
                "{title}", notification['title'].replace('`', ''))
            message_content = message_content.replace(
                "{creationTime}", datetime.fromisoformat(
                    notification['creationTime'].replace("Z", "+00:00")).strftime("%d %B %Y, %H:%M:%S"))
            message_content = message_content.replace(
                "{MESSAGE}", notification['message'].replace('`', ''))

            bash_command_message = bash_command.replace(
                "{MESSAGE}", quote(message_content))

            process = subprocess.run(
                bash_command_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if json.loads(process.stdout)['ok']:
                sys.stdout.write(
                    f"\033[92m\nThe notification #{notification['id']} has been sent successfully.\n\033[0m{notification}\n")

                mark_notification_as_acknowledged(notification['id'])

            else:
                sys.stderr.write(
                    f"\033[41mThe notification #{notification['id']} was not sent successfully.\n\033[0m")
                sys.stderr.write(f"\033[41m{process.stdout}\n\033[0m\n")