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
import os
import subprocess
import sys
import requests
from urllib.parse import quote
from datetime import datetime


def is_debug_mode() -> bool:
    """
    Checks if the script is running in debug mode.

    Returns:
    - bool: True if the script is running in debug mode, False otherwise.
    """
    return '--debug' in sys.argv


def get_config():
    """
    Retrieves configuration settings from the settings.ini file.

    This function reads the settings.ini file and extracts the necessary configuration settings
    for the Cloudron monitoring tool. It specifically looks for the following settings:
    - NOTIFICATION_CMD: The command used to send notifications.
    - NOTIFICATION_TEMPLATE: The template for the notification messages.
    - CLOUDRON_TOKEN: The API token(s) for accessing the Cloudron instance(s).
    - CLOUDRON_DOMAIN: The domain(s) of the Cloudron instance(s).

    Returns:
        tuple: A tuple containing the following elements:
        - cloudron_title (list): A list of titles for each Cloudron instance.
        - cloudron_domain (list): A list of domains for each Cloudron instance.
        - cloudron_api_key (list): A list of API tokens for each Cloudron instance.
        - bash_command (str): The command used to send notifications.
        - message_template (str): The template for the notification messages.
    """
    config = configparser.ConfigParser()

    if not os.path.exists("settings.ini"):
        sys.stderr.write(f"\033[mError: The configuration file 'settings.ini' does not exist.\033[0m\n")
        sys.stderr.flush()
        exit(1)

    try:
        config.read("settings.ini")
        bash_command = config["NOTIFICATION"]["NOTIFICATION_CMD"]
        message_template = config["NOTIFICATION"]["NOTIFICATION_TEMPLATE"]
    except KeyError as e:
        sys.stderr.write(
            f"\033[mConfiguration error: Check the environment variables: {e}.\033[0m\n"
        )
        sys.stderr.flush()
        exit(1)
    cloudron_api_key = []
    cloudron_domain = []
    cloudron_title = []

    for section in config.sections():
        for key in config[section]:
            if key.startswith("cloudron_domain"):
                cloudron_domain.append(config[section]["CLOUDRON_DOMAIN"])
            elif key.startswith("cloudron_token"):
                cloudron_api_key.append(config[section]["CLOUDRON_TOKEN"])
                cloudron_title.append(section)

    return (
        cloudron_title,
        cloudron_domain,
        cloudron_api_key,
        bash_command,
        message_template,
    )


def get_cloudron_notifications(cloudron_domain: str, cloudron_api_key: str) -> list:
    """
    Fetches a list of notifications from the Cloudron API.

    Parameters:
    - cloudron_domain (str): The domain of the Cloudron instance from which to fetch notifications.
    - cloudron_api_key (str): The API token for accessing the Cloudron instance.

    Returns:
    - list: A list of notifications in JSON format, obtained from the Cloudron API. The list is sorted by the 'creationTime' attribute of each notification.

    Raises:
    - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API.
    """
    headers = {"Authorization": f"Bearer {cloudron_api_key}"}
    url = f"https://{cloudron_domain}/api/v1/notifications"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\033[Error receiving notifications: {e}.\033[0m\n")
        sys.stderr.flush()
        return []

    # sys.stdout.write(
    #     f"\033[92mNotifications were successfully received via the Cloudron API.\033[0m\n")
    # sys.stdout.flush()
    return sorted(response.json()["notifications"], key=lambda x: x["creationTime"])


def get_apps(cloudron_domain: str, cloudron_api_key: str) -> list:
    """
    Retrieves a list of applications from the Cloudron API.

    Parameters:
    - cloudron_domain (str): The domain of the Cloudron instance from which to fetch the list of applications.
    - cloudron_api_key (str): The API token for accessing the Cloudron instance.

    Returns:
    - list: A list of applications in JSON format, obtained from the Cloudron API.

    Raises:
    - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API.
    """
    url = f"https://{cloudron_domain}/api/v1/apps"
    headers = {"Authorization": f"Bearer {cloudron_api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(
            f"\033[mError when receiving the application list: {e}.\n\033[0m"
        )
        sys.stderr.flush()
        return []

    return response.json()


def mark_notification_as_acknowledged(
        cloudron_domain: str, cloudron_api_key: str, notification_id: str
) -> None:
    """
    Marks a specific notification as acknowledged in the Cloudron API.

    Parameters:
    - cloudron_domain (str): The domain of the Cloudron instance where the notification is located.
    - cloudron_api_key (str): The API token for accessing the Cloudron instance.
    - notification_id (str): The unique identifier of the notification to be marked as acknowledged.

    Raises:
    - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API, such as network issues or invalid credentials.
    """
    headers = {"Authorization": f"Bearer {cloudron_api_key}"}
    data = {"acknowledged": True}

    url = f"https://{cloudron_domain}/api/v1/notifications/{notification_id}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(
            f"\033[mError when marking a notification as read: {e}.\033[0m"
        )
        sys.stderr.flush()
        return

    sys.stdout.write(
        f"\033[92mNotifications #{notification_id} have been successfully marked as read.\033[0m\n"
    )
    sys.stdout.flush()
    return


def message_update_template(message_template: str, notification) -> str:
    """
    Updates a message template with specific notification details.

    Parameters:
    - message_template (str): The template string for the notification message.
    - notification: A dictionary containing the details of the notification.

    Returns:
    - str: The updated message string with all placeholders replaced by the actual notification details.
    """
    message_content = message_template.replace("{id}", notification["id"])
    message_content = message_content.replace("{title}", notification["title"])
    message_content = message_content.replace(
        "{creationTime}",
        datetime.fromisoformat(
            notification["creationTime"].replace("Z", "+00:00")
        ).strftime("%d %B %Y, %H:%M:%S"),
    )
    message_content = message_content.replace("{MESSAGE}", notification["message"])
    return message_content


def curl_handler(
        process: subprocess.CompletedProcess, id: str, message_type: str = "notification"
) -> bool:
    """
    Handles the response from the messaging service when using cURL for sending messages.

    This function processes the output of a subprocess call that sends a message using cURL. It checks if the message was sent successfully by parsing the JSON response.
    If the message was sent successfully, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Parameters:
    - process (subprocess.CompletedProcess): The completed process object returned by the subprocess call.
    - id (str): The notification number or application name
    - message_type (str): The type of message being sent. Defaults to "notification".

    Returns:
    - bool: True if the message was sent successfully, False otherwise.
    """
    try:
        json_data = json.loads(process.stdout)

        if json_data["ok"]:
            if message_type == "notification":
                sys.stdout.write(
                    f"\033[92mThe notification #{id} has been sent successfully.\033[0m\n"
                )
            elif message_type == "running status":
                sys.stdout.write(
                    f"\033[92mInformation about {id} not running has been sent successfully.\033[0m\n"
                )
            elif message_type == "error status":
                sys.stdout.write(
                    f"\033[92mInformation about {id}'s error has been successfully sent.\033[0m\n"
                )

            sys.stdout.flush()

        else:
            sys.stderr.write(
                f"\033[mInformation about {message_type} ({id}) was not sent successfully.\n{process.stdout}\033[0m\n"
            )
            sys.stderr.flush()
            return False

    except json.JSONDecodeError:
        sys.stderr.write(
            f"\033[mInformation about {message_type} ({id}) was not sent successfully: NOTIFICATION_CMD error: Check the curl cmd.\033[0m\n"
        )
        sys.stderr.flush()
        return False

    return True


def not_curl_handler(
        process: subprocess.CompletedProcess, id: str, message_type: str = "notification"
) -> bool:
    """
    Handles the response from the messaging service when not using cURL for sending messages.

    This function processes the output of a subprocess call that sends a message without using cURL. It checks the return code of the subprocess call to determine if the message was sent successfully.
    If the message was sent successfully, it prints a success message to stdout. In case of an error, it prints an error message to stderr.

    Parameters:
    - process (subprocess.CompletedProcess): The completed process object returned by the subprocess call.
    - id (str): The notification number or application name
    - message_type (str): The type of message being sent. Defaults to "notification".

    Returns:
    - bool: True if the message was sent successfully, False otherwise.
    """
    if process.returncode == 0:
        if message_type == "notification":
            sys.stdout.write(
                f"\033[92mThe notification #{id} has been sent successfully.\033[0m\n"
            )
        elif message_type == "running status":
            sys.stdout.write(
                f"\033[92mInformation about {id} not running has been sent successfully.\033[0m\n"
            )
        elif message_type == "error status":
            sys.stdout.write(
                f"\033[92mInformation about {id}'s error has been successfully sent.\033[0m\n"
            )

        sys.stdout.flush()
        return True

    else:
        sys.stderr.write(
            f"\033[mInformation about {message_type} ({id}) was not sent successfully.\n{process.stderr}\033[0m\n"
        )
        sys.stderr.flush()
        return False


def send_notification(
        bash_command: str, message: str, id: str, message_type: str = "notification"
) -> bool:
    """
    Sends a notification message using a specified command.

    This function prepares a notification message based on the provided template and details, then executes a command to send the message.
    The function supports both cURL commands and other shell commands. It checks if the command includes "curl" to determine the appropriate handler for processing the command's response.

    Parameters:
    - bash_command (str): The shell command to execute for sending the notification. It should include placeholders for the message content, such as "{MESSAGE}".
    - message (str): The notification message to be sent. It will replace the "{MESSAGE}" placeholder in the bash_command.
    - id (str): The notification number or application name, used for logging and error handling.
    - message_type (str): The type of message being sent. Defaults to "notification". It's used for logging and error handling.

    Returns:
    - bool: True if the notification was sent successfully, False otherwise. The success of the operation is determined by the response from the executed command.
    """
    if "curl" in bash_command:
        bash_command_message = bash_command.replace("{MESSAGE}", quote(message))
    else:
        bash_command_message = bash_command.replace(
            "{MESSAGE}", message.replace("`", "\`")
        )

    process = subprocess.run(
        bash_command_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return (
        curl_handler(process, id.strip("{'}"), message_type)
        if "curl" in bash_command
        else not_curl_handler(process, id.strip("{'}"), message_type)
    )


if __name__ == "__main__":

    (
        cloudron_title,
        cloudron_domain,
        cloudron_api_key,
        bash_command,
        message_template,
    ) = get_config()

    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

    if not bash_command or not message_template:
        sys.stderr.write(
            f"\033[mTime: {current_time}.\nConfiguration error: Check the NOTIFICATION variables.\033[0m\n"
        )
        sys.stderr.flush()
        exit(1)

    sys.stdout.write(f"Time: {current_time}.\n")
    sys.stdout.flush()

    for i in range(len(cloudron_api_key)):
        sys.stdout.write(f"Checking the instance - {cloudron_title[i]}\n")
        sys.stdout.flush()

        if not cloudron_api_key[i] or not cloudron_domain[i]:
            sys.stderr.write(
                f"\033[mConfiguration error: Check the environment variables.\033[0m\n"
            )
            sys.stderr.flush()
            continue

        list_apps = get_apps(cloudron_domain[i], cloudron_api_key[i])

        count_app = {"error": 0, "not_running": 0, "send": 0}

        if list_apps == []:
            continue

        for app in list_apps["apps"]:
            if app["runState"] != "running":
                message = f"{cloudron_title[i]}\nApplication {app['manifest']['title']} is not running"
                send_app = send_notification(
                    bash_command,
                    message,
                    str({app["manifest"]["title"]}),
                    "running status",
                )
                count_app["not_running"] += 1

                if send_app:
                    count_app["send"] += 1
                    if is_debug_mode():
                        sys.stdout.write(f"\"{message}\"\n")
                        sys.stdout.flush()

            if not app["error"] is None:
                message = f"{cloudron_title[i]}\nApplication {app['manifest']['title']} has an error:\nError: {app['error']['message']}\nReason: {app['error']['reason']}"
                send_app = send_notification(
                    bash_command,
                    message,
                    str({app["manifest"]["title"]}),
                    "error status",
                )
                count_app["error"] += 1

                if send_app:
                    count_app["send"] += 1
                    if is_debug_mode():
                        sys.stdout.write(f"\"{message}\"\n")
                        sys.stdout.flush()

        ending = {
            "app": "s status have" if len(list_apps["apps"]) > 1 else " status has",
            "err": "s" if count_app["error"] > 1 else "",
            "run": "s are" if count_app["not_running"] > 1 else " is",
            "send": "s were" if count_app["send"] > 1 else " was",
        }

        sys.stdout.write(
            f"{len(list_apps['apps'])} application{ending['app']} been checked: {count_app['error']} app{ending['err']} with "
            f"error, {count_app['not_running']} app{ending['run']} not working, {count_app['send']} error{ending['send']} successfully sent.\n"
        )
        sys.stdout.flush()

        list_notifications = get_cloudron_notifications(
            cloudron_domain[i], cloudron_api_key[i]
        )
        count_notif = {"unread": 0, "send": 0}

        if list_notifications == []:
            continue

        for notification in list_notifications:
            if not notification["acknowledged"]:
                count_notif["unread"] += 1
                message = f"{cloudron_title[i]}\n" + message_update_template(
                    message_template, notification
                )
                send_status = send_notification(
                    bash_command, message, notification["id"]
                )

                if send_status:
                    count_notif["send"] += 1
                    if is_debug_mode():
                        sys.stdout.write(f"{notification}\n")
                        sys.stdout.flush()
                    mark_notification_as_acknowledged(cloudron_domain[i], cloudron_api_key[i], notification['id'])

        ending_n = {
            "notif": "s have" if len(list_notifications) > 1 else " has",
            "unread": "s" if count_notif["unread"] > 1 else "",
            "send": "s were" if count_notif["send"] > 1 else " was",
        }
        sys.stdout.write(
            f"{len(list_notifications)} notification{ending_n['notif']} been checked: {count_notif['unread']} notification{ending_n['unread']} unread, {count_notif['send']} notification{ending_n['send']} successfully sent.\n"
        )
        sys.stdout.flush()
