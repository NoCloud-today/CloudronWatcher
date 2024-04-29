"""
cloudron_monitor.py

This script is a monitoring tool for Cloudron. 
It is responsible for fetching notifications from Cloudron,
sending unacknowledged notifications to a messaging service, 
and marking notifications as acknowledged in Cloudron.

Features:
- Retrieves notifications from the Cloudron.
- Sends notifications using a command.
- Marks notifications as acknowledged in the Cloudron.

Environment Variables from setting.ini:
- CLOUDRON_TOKEN: The API token for Cloudron.
- CLOUDRON_DOMAIN: The domain of the Cloudron instance.
- NOTIFICATION_CMD: The bash command to send notifications.
- NOTIFICATION_TEMPLATE: The message template.

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

cloudron_api_key = config['MAIN']['CLOUDRON_TOKEN']
cloudron_domain = config['MAIN']["CLOUDRON_DOMAIN"]
bash_command = config['MAIN']['NOTIFICATION_CMD']
message_template = config['MAIN']['NOTIFICATION_TEMPLATE']


def get_cloudron_notifications() -> list:
    """
    Retrieves notifications from the Cloudron API.

    This function fetches notifications from the Cloudron API using the API key and domain specified in the environment variables.
    If the API call is successful, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Returns:
        list: A list of notifications received from the Cloudron API.
    """

    headers = {'Authorization': f'Bearer {cloudron_api_key}'}
    url = f"https://{cloudron_domain}/api/v1/notifications"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mError receiving notifications: {e}. Time: {current_time}\n\033[0m\n")
        sys.stderr.flush()
        exit(1)

    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(
        f"\033[92mNotifications were successfully received via the Cloudron API. Time: {current_time}\n\033[0m\n")
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

    headers = {'Authorization': f'Bearer {cloudron_api_key}'}
    data = {"acknowledged": True}

    url = f"https://{cloudron_domain}/api/v1/notifications/{notification_id}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mError when marking a notification as read: {e}. Time: {current_time}\n\033[0m")
        sys.stderr.flush()
        return

    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(
        f"\033[92mNotifications #{notification_id} have been successfully marked as read. Time: {current_time}\n\033[0m\n")
    sys.stdout.flush()
    return


def curl_handler(process: subprocess.CompletedProcess) -> None:
    """
    Handles the response from a cURL command.

    This method analyzes the output of the cURL command, checks the success of sending the notification, and if the notification
    was successfully sent, marks it as read.

    Parameters:
        process (subprocess.CompletedProcess): The result of the cURL command execution.
    """
    try:
        json_data = json.loads(process.stdout)

        if json_data['ok']:
            current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            sys.stdout.write(
                f"\033[92m\nThe notification #{notification['id']} has been sent successfully. Time: {current_time}\n\033[0m{notification}\n")
            sys.stdout.flush()

            mark_notification_as_acknowledged(notification['id'])

        else:
            current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            sys.stderr.write(
                f"\033[41mThe notification #{notification['id']} was not sent successfully. Time: {current_time}\n{process.stdout}\n\033[0m")
            sys.stderr.flush()

    except json.JSONDecodeError:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mThe notification #{notification['id']} was not sent successfully. Time: {current_time}\nNOTIFICATION_CMD error: Check the curl cmd. \n\033[0m")
        sys.stderr.flush()


def not_curl_handler(process: subprocess.CompletedProcess) -> None:
    """
    Handles the response from a command not using cURL.

    This method is intended for handling responses from commands that do not use cURL to send notifications. It analyzes
    the command output, assuming the successful sending of the notification, and marks it as read.

    Parameters:
        process (subprocess.CompletedProcess): The result of the command execution.
    """
    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(
        f"\033[92m\nThe notification #{notification['id']} has been sent successfully. Time: {current_time}\n\033[0m{notification}\n")
    sys.stdout.flush()

    mark_notification_as_acknowledged(notification['id'])


if __name__ == '__main__':

    if not cloudron_api_key or not cloudron_domain or not bash_command:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mConfiguration error: Check the environment variables. Time: {current_time}\033[0m\n")
        sys.stderr.flush()
        exit(1)

    responses = get_cloudron_notifications()

    for notification in responses['notifications']:
        if not notification['acknowledged']:
            message_content = message_template.replace(
                "{id}", notification['id'])
            message_content = message_content.replace(
                "{title}", notification['title'])
            message_content = message_content.replace(
                "{creationTime}", datetime.fromisoformat(
                    notification['creationTime'].replace("Z", "+00:00")).strftime("%d %B %Y, %H:%M:%S"))
            message_content = message_content.replace(
                "{MESSAGE}", notification['message'])

        if "curl" in bash_command:
            bash_command_message = bash_command.replace(
                "{MESSAGE}", quote(message_content))
        else:
            bash_command_message = bash_command.replace(
                "{MESSAGE}", message_content.replace('`', '\`'))

        process = subprocess.run(
            bash_command_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            if "curl" in bash_command:
                curl_handler(process)
            else:
                not_curl_handler(process)

        else:
            current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            sys.stderr.write(
                f"\033[41mThe notification #{notification['id']} was not sent successfully. Time: {current_time}\n{process.stderr}\n\033[0m")
            sys.stderr.flush()
