"""
This script is the main entry point for the Cloudron monitoring tool. It is responsible for fetching notifications from Cloudron,
sending acknowledged notifications to a messaging service, and marking notifications as acknowledged in Cloudron.

Imports:
    - json: Used for parsing and manipulating JSON data.
    - subprocess: Used for executing shell commands.
    - sys: Used for system-specific parameters and functions.
    - cloudron_utils.cloudron_notifications: Custom utility for handling Cloudron notifications.
    - urllib.parse.quote: Used for percent-encoding special characters in URLs.

Global Variables:
    - send_message_script: Path to the script used for sending messages via cURL.

Main Functionality:
    - The script starts by fetching unacknowledged notifications from Cloudron using the `get_cloudron_notifications` function.
    - If no notifications are found, the script exits with a status code of 1.
    - For each unacknowledged notification, the script executes the `send_message_script` with the notification message as an argument.
    - The script then checks the response from the messaging service. If the message was sent successfully, it prints a success message and marks the notification as acknowledged in Cloudron.
    - If the message was not sent successfully, it prints an error message.

Usage:
    - This script is intended to be run as a standalone application. It does not require any command-line arguments.
"""

import json
import subprocess
import sys
import cloudron_utils.cloudron_notifications as cn
from urllib.parse import quote


send_message_script = "messanger_exec/curl_api_post"


if __name__ == '__main__':
    responses = cn.get_cloudron_notifications()
    
    if responses == []:
        exit(1)

    for notification in responses['notifications']:
        if not notification['acknowledged']:
            process = subprocess.Popen(["bash", send_message_script, quote(
                notification['message'].replace('`', ''))], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = process.communicate()

            if json.loads(stdout)['ok']:
                sys.stdout.write(stdout.decode('utf-8') + '\n')
                sys.stdout.write(
                    f"\033[92mThe notification #{notification['id']} has been sent successfully.\n\033[0m{notification}\n")

                cn.mark_notification_as_acknowledged(notification['id'])
                
            else:
                sys.stderr.write(f"\033[41mThe notification #{notification['id']} was not sent successfully.\n\033[0m")
                sys.stderr.write(stdout.decode('utf-8') + '\n\n')
                
