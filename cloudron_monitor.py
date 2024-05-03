"""
cloudron_monitor.py

This script is a monitoring tool for Cloudron. 
It is responsible for:
*   fetching notifications from Cloudron,
    sending unacknowledged notifications to a messaging service, 
    and marking notifications as acknowledged in Cloudron.
    
*   checking the running and error status of applications and
    sending notifications about broken apps

Features:
- Retrieves notifications from the Cloudron.
- Retrieves list of apps from the Cloudron.
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


def get_apps() -> list:
    """
    Fetches a list of applications from the Cloudron API.

    This function fetches a list of applications from the Cloudron API using the API key and domain specified in the environment variables.
    If the API call is successful, it prints a success message to stdout. In case of an error, it prints an error message to stderr.
    Returns:
        list: A list of applications in JSON format, obtained from the Cloudron API.
    """
    url = f"https://{cloudron_domain}/api/v1/apps"
    headers = {'Authorization': f'Bearer {cloudron_api_key}'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mError when receiving the application list: {e}. Time: {current_time}\n\033[0m")
        sys.stderr.flush()
        exit(1)

    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(
        f"\033[92mThe application list was successfully received. Time: {current_time}\n\033[0m\n")
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


def message_update_template(notification) -> str:
    """
    Updates a message template with the details of a notification.

    This function takes a notification object and replaces placeholders in the message template with the actual notification details.
    The placeholders in the template are replaced with the notification's ID, title, creation time, and message content.

    Parameters:
    - notification (dict): A dictionary containing the notification details. Expected keys are:
        - 'id' (str): The unique identifier of the notification.
        - 'title' (str): The title of the notification.
        - 'creationTime' (str): The creation time of the notification in ISO 8601 format.
        - 'message' (str): The message content of the notification.

    Returns:
    - str: A formatted string with the updated message template, incorporating the notification's details.
    """
    message_content = message_template.replace(
        "{id}", notification['id'])
    message_content = message_content.replace(
        "{title}", notification['title'])
    message_content = message_content.replace(
        "{creationTime}", datetime.fromisoformat(
            notification['creationTime'].replace("Z", "+00:00")).strftime("%d %B %Y, %H:%M:%S"))
    message_content = message_content.replace(
        "{MESSAGE}", notification['message'])
    return message_content


def curl_handler(process: subprocess.CompletedProcess, message_type: str = "notification") -> bool:
    """
    Handles the response from the messaging service when using cURL for sending messages.

    This function processes the output of a subprocess call that sends a message using cURL. It checks if the message was sent successfully by parsing the JSON response.
    If the message was sent successfully, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Parameters:
    - process (subprocess.CompletedProcess): The completed process object returned by the subprocess call.
    - message_type (str): The type of message being sent. Defaults to "notification".

    Returns:
    - bool: True if the message was sent successfully, False otherwise.
    """
    try:
        json_data = json.loads(process.stdout)

        if json_data['ok']:
            current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            if message_type == "notification":
                sys.stdout.write(
                    f"\033[92m\nThe notification has been sent successfully. Time: {current_time}\n\033[0m")
            elif message_type == "running status":
                sys.stdout.write(
                    f"\033[92m\nInformation about the app not running has been sent successfully. Time: {current_time}\n\033[0m")
            elif message_type == "error status":
                sys.stdout.write(
                    f"\033[92m\nInformation about the app's error has been successfully sent. Time: {current_time}\n\033[0m")

            sys.stdout.flush()

        else:
            current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            sys.stderr.write(
                f"\033[nInformation about {message_type} was not sent successfully. Time: {current_time}\n{process.stdout}\n\033[0m")
            sys.stderr.flush()
            return False

    except json.JSONDecodeError:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mInformation about {message_type} was not sent successfully. Time: {current_time}\nNOTIFICATION_CMD error: Check the curl cmd. \n\033[0m")
        sys.stderr.flush()
        return False

    return True


def not_curl_handler(process: subprocess.CompletedProcess, message_type: str = "notification") -> bool:
    """
    Handles the response from the messaging service when not using cURL for sending messages.

    This function processes the output of a subprocess call that sends a message without using cURL. It checks the return code of the subprocess call to determine if the message was sent successfully.
    If the message was sent successfully, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Parameters:
    - process (subprocess.CompletedProcess): The completed process object returned by the subprocess call.
    - message_type (str): The type of message being sent. Defaults to "notification".

    Returns:
    - bool: True if the message was sent successfully, False otherwise.
    """
    if process.returncode == 0:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        if message_type == "notification":
            sys.stdout.write(
                f"\033[92m\nThe notification has been sent successfully. Time: {current_time}\n\033[0m")
        elif message_type == "running status":
            sys.stdout.write(
                f"\033[92m\nInformation about the app not running has been sent successfully. Time: {current_time}\n\033[0m")
        elif message_type == "error status":
            sys.stdout.write(
                f"\033[92m\nInformation about the app's error has been successfully sent. Time: {current_time}\n\033[0m")

        sys.stdout.flush()
        return True

    else:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mInformation about {message_type} was not sent successfully. Time: {current_time}\n{process.stderr}\n\033[0m")
        sys.stderr.flush()
        return False


def send_notification(message: str, message_type: str = "notification") -> bool:
    """
    Sends a notification message to the configured messaging service.

    This function prepares the message for sending by replacing placeholders in the command specified in the configuration file with the actual message content.
    It then executes the command using a subprocess call. The function uses either `curl_handler` or `not_curl_handler` to process the response from the messaging service,
    depending on whether the command includes "curl".

    Parameters:
    - message (str): The message content to be sent.
    - message_type (str): The type of message being sent. Defaults to "notification".

    Returns:
    - bool: True if the message was sent successfully, False otherwise.
    """
    if "curl" in bash_command:
        bash_command_message = bash_command.replace(
            "{MESSAGE}", quote(message))
    else:
        bash_command_message = bash_command.replace(
            "{MESSAGE}", message.replace('`', '\`'))

    process = subprocess.run(
        bash_command_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return curl_handler(process, message_type) if "curl" in bash_command else not_curl_handler(process, message_type)


if __name__ == '__main__':
    if not cloudron_api_key or not cloudron_domain or not bash_command:
        current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"\033[41mConfiguration error: Check the environment variables. Time: {current_time}\033[0m\n")
        sys.stderr.flush()
        exit(1)

    list_apps = get_apps()

    for app in list_apps['apps']:
        if app['runState'] != 'running':
            message = f"""Application {app['manifest']['title']} is not running"""
            send_notification(message, "running status")

        if not app['error'] is None:
            message = f"""Application {app['manifest']['title']} has an error:\nError: {app['error']['message']}\nReason: {app['error']['reason']}"""
            send_notification(message, "error status")

    list_notifications = get_cloudron_notifications()

    for notification in list_notifications['notifications']:
        if not notification['acknowledged']:
            message = message_update_template(notification)
            send_status = send_notification(message)

            if send_status:
                sys.stdout.write(f"{notification}\n")
                sys.stdout.flush()
                mark_notification_as_acknowledged(notification['id'])
