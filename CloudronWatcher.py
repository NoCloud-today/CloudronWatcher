"""
CloudronWatcher.py

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


def get_config() -> tuple:
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
        - cloudron_instances
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
        bash_command_conf = config["NOTIFICATION"]["NOTIFICATION_CMD"]
        message_template_conf = config["NOTIFICATION"]["NOTIFICATION_TEMPLATE"]

        if bash_command_conf == '':
            sys.stderr.write(
                f"\033[mConfiguration error: Check the environment variables: NOTIFICATION_CMD.\033[0m\n"
            )
            sys.stderr.flush()
            exit(1)

        if message_template_conf == '':
            sys.stderr.write(
                f"\033[mConfiguration error: Check the environment variables: NOTIFICATION_TEMPLATE.\033[0m\n"
            )
            sys.stderr.flush()
            exit(1)

    except KeyError as e:
        sys.stderr.write(
            f"\033[mConfiguration error: Check the environment variables: {e}.\033[0m\n"
        )
        sys.stderr.flush()
        exit(1)

    cloudron_instances_conf = {}

    for section in config.sections():
        if section != 'NOTIFICATION':
            try:
                if config[section]["CLOUDRON_DOMAIN"] == '' or config[section]["CLOUDRON_TOKEN"] == '':
                    sys.stderr.write(
                        f"\033[33mWarning: The environment variable of {section} is empty. It will be "
                        f"skipped.\033[0m\n"
                    )
                    sys.stderr.flush()
                else:
                    cloudron_instances_conf[section] = [config[section]["CLOUDRON_DOMAIN"],
                                                        config[section]["CLOUDRON_TOKEN"]]
            except KeyError as e:
                sys.stderr.write(
                    f"\033[33mWarning: The environment variable of {section}: No {e} It will be skipped.\033[0m\n"
                )
                sys.stderr.flush()

    return (
        cloudron_instances_conf,
        bash_command_conf,
        message_template_conf,
    )


def get_cloudron_notifications(cloudron_instance_get: list) -> list:
    """
    Fetches a list of notifications from the Cloudron API.

    Parameters:
    - cloudron_instance_get: Pair (domain, api-key).

    Returns:
    - list: A list of notifications in JSON format, obtained from the Cloudron API. The list is sorted by the 'creationTime' attribute of each notification.

    Raises:
    - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API.
    """
    headers = {"Authorization": f"Bearer {cloudron_instance_get[1]}"}
    url = f"https://{cloudron_instance_get[0]}/api/v1/notifications"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"\033[mError receiving notifications: {e}.\033[0m\n")
        sys.stderr.flush()
        return []

    return sorted(response.json()["notifications"], key=lambda x: x["creationTime"])


def get_apps(cloudron_instance_get: list) -> list:
    """
    Retrieves a list of applications from the Cloudron API.

    Parameters:
    - cloudron_instance: Pair (domain, api-key).

    Returns:
    - list: A list of applications in JSON format, obtained from the Cloudron API.

    Raises:
    - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API.
    """
    url = f"https://{cloudron_instance_get[0]}/api/v1/apps"
    headers = {"Authorization": f"Bearer {cloudron_instance_get[1]}"}

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


def message_update_template(message_template_up: str, notification) -> str:
    """
    Updates a message template with specific notification details.

    Parameters:
    - message_template (str): The template string for the notification message.
    - notification: A dictionary containing the details of the notification.

    Returns:
    - str: The updated message string with all placeholders replaced by the actual notification details.
    """
    message_content = message_template_up.replace("{id}", notification["id"])
    message_content = message_content.replace("{title}", notification["title"])
    message_content = message_content.replace(
        "{creationTime}",
        datetime.fromisoformat(
            notification["creationTime"].replace("Z", "+00:00")
        ).strftime("%d %B %Y, %H:%M:%S"),
    )
    message_content = message_content.replace("{MESSAGE}", notification["message"])
    return message_content


def send_notification(bash_command_send: str, message_send: str, id_notif: str,
                      message_type: str = "notification") -> bool:
    """
    Sends a notification message using a specified command.

    Parameters:
    - bash_command_send (str): The shell command to execute for sending the notification. It should include
    placeholders for the message content, such as "{MESSAGE}".
    - message_send (str): The notification message to be sent.
    It will replace the "{MESSAGE}" placeholder in the bash_command.
    - id_notif (str): The notification number or
    application name, used for logging and error handling.
    - message_type (str): The type of message being sent.
    Defaults to "notification". It's used for logging and error handling.

    Returns: - bool: True if the notification was sent successfully, False otherwise. The success of the operation is
    determined by the return code from the executed command.
    """
    bash_command_message = bash_command_send.replace(
        "{MESSAGE}", message_send.replace("`", "\`")
    )

    process = subprocess.run(
        bash_command_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode != 0:
        sys.stderr.write(
            f"\033[mInformation about {message_type} {id_notif} was not sent successfully.\n{process.stderr}"
            f"\033[0m\n"
        )
        sys.stderr.flush()
        return False

    if message_type == "notification":
        sys.stdout.write(
            f"\033[92mThe notification #{id_notif} has been sent successfully.\033[0m\n"
        )
    elif message_type == "running status":
        sys.stdout.write(
            f"\033[92mInformation about {id_notif} (not running) has been sent successfully.\033[0m\n"
        )
    elif message_type == "error status":
        sys.stdout.write(
            f"\033[92mInformation about {id_notif} error has been successfully sent.\033[0m\n"
        )

    sys.stdout.flush()


def mark_notification_as_acknowledged(cloudron_instance_mark: list, id_notif: str) -> None:
    """
    Marks a specific notification as acknowledged in the Cloudron API.

    Parameters:
    - cloudron_instance_mark: Pair (domain, api-key).
    - notification_id (str): The unique identifier of the notification to be marked as acknowledged.

    Raises: - requests.exceptions.RequestException: If there is an error with the request to the Cloudron API,
    such as network issues or invalid credentials.
    """
    headers = {"Authorization": f"Bearer {cloudron_instance_mark[1]}"}
    data = {"acknowledged": True}

    url = f"https://{cloudron_instance_mark[0]}/api/v1/notifications/{id_notif}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sys.stderr.write(
            f"\033[mError: marking a notification as read: {e}.\033[0m"
        )
        sys.stderr.flush()
        return

    sys.stdout.write(
        f"\033[92mNotifications #{id_notif} have been successfully marked as read.\033[0m\n"
    )
    sys.stdout.flush()
    return


if __name__ == '__main__':
    cloudron_instances, bash_command, message_template = get_config()

    current_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

    sys.stdout.write(f"Time: {current_time}.\n")
    sys.stdout.flush()

    for title, cloudron_instance in cloudron_instances.items():

        sys.stdout.write(f"Checking the instance - {title}\n")
        sys.stdout.flush()

        list_apps = get_apps(cloudron_instance)

        count_app = {"error": 0, "not_running": 0, "send": 0}

        if list_apps:
            for app in list_apps['apps']:
                if app["runState"] != "running":
                    message = f"{title}\nApplication {app['manifest']['title']} is not running"
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
                    message = f"{title}\nApplication {app['manifest']['title']} has an error.\n{app['error']['message']}\nReason: {app['error']['reason']}"
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

        sys.stdout.write(
            f"Applications:\n\tChecked: {len(list_apps['apps'])}\n\tError: {count_app['error']}\n\tNot working: "
            f"{count_app['not_running']}\n\tSent successfully: {count_app['send']}\n"
        )
        sys.stdout.flush()

        list_notifications = get_cloudron_notifications(cloudron_instance)
        count_notif = {"unread": 0, "send": 0}

        if list_notifications:
            for notification in list_notifications:
                if not notification["acknowledged"]:
                    count_notif["unread"] += 1
                    message = f"{title}\n" + message_update_template(
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
                        mark_notification_as_acknowledged(cloudron_instance, notification["id"])

        sys.stdout.write(
            f"Notifications:\n\tChecked: {len(list_notifications)}\n\tUnread: {count_notif['unread']}\n\t"
            f"Sent successfully: {count_notif['send']}\n")
        sys.stdout.flush()
