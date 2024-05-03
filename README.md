# cloudron-monitor

## Overview

Cloudron Monitor is a Python-based tool designed to enhance the monitoring capabilities of cloud instances. It makes it easier to receive notifications from Cloudron, send confirmed notifications to the messaging service, and mark notifications as confirmed in Cloudron. The script also checks the status of applications and informs about errors. The goal of this project is to provide an easy way to track the health and performance of cloud deployments, ensuring that users are informed of any important updates or issues.

## Features

- **Notification Fetching**: Automatically fetches notifications from Cloudron using the Cloudron API.
- **Application status**: Automatically fetches a list of apps and check status from Cloudron using the Cloudron API.
- **Message Sending**: Sends unacknowledged notifications and errors to a messaging service via a bash command.
- **Notification Acknowledgement**: Marks notifications as acknowledged in Cloudron, ensuring that they are not reprocessed.

## Prerequisites

- Python 3.6+
- Access to a Cloudron instance with API access enabled.
- A messaging service that can receive messages via cURL.

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/cloudron-monitor.git
```

2. Navigate to the project directory:
```
cd cloudron-monitor
```

3. Install the required Python packages:
```
pip install -r requirements.txt
```

4. Change the settings in the `setting.ini` file using the instructions provided in the accompanying file.


## Usage

To run the Cloudron Monitor, simply execute the `cloudron_monitor.py` script:
```
python cloudron_monitor.py
```

This script does not require any command-line arguments. It will automatically fetch unacknowledged notifications and application status from Cloudron. It send notifications to the configured messaging service, and mark them as acknowledged in Cloudron.

You can configure the script together with cron.

All successful commands and errors are logged to the corresponding output streams: `stdout` for successful commands and `stderr` for errors. This ensures that the monitoring process is transparent and that any issues can be easily identified and addressed.

## Example

* Use `bin/echo` 

    `settings.ini`
    ```ini
    NOTIFICATION_CMD=/bin/echo "{MESSAGE}" >> path/to/greetings.txt
    NOTIFICATION_TEMPLATE=
        Hello!
        You have new notification No.{id}:
        {title}
        {MESSAGE}
        The notification has been created {creationTime}
        🚀
    ```
    `greetings.txt`
    
    ```
    Application GitLab is not running

    Application GitLab has an error:
    Error: ...
    Reason: FileSystem Error

    Hello!
    You have new notification No.1:
    Cloudron v7.7.2 installed
    Cloudron v7.7.2 was installed.

    Please join our community at https://forum.cloudron.io .

    Changelog:
    * OIDC avatar support via picture claim
    * backupcleaner: fix bug where preserved backups were removed incorrectly
    * directoryserver: cloudflare warning
    * oidc/ldap: fix display name parsing to send anything after first name as the last name
    * mail: Update haraka to 3.0.3
    * mongodb: Update mongodb to 6.0
    * acme: use secp256r1 curve for max compatibility
    * add port range support
    * docker: disable userland proxy
    * oidc: always re-setup oidc client record
    * mail: update solr to 8.11.3
    * mail: spam acl should allow underscore and question mark
    * Fix streaming of logs with `logPaths`
    * profile: store user language setting in the database


    The notification has been created 21 April 2024, 12:03:33
    🚀
    ```

* Use Telegram API

    `settings.ini`
    ```ini
    NOTIFICATION_CMD=curl -X POST "https://api.telegram.org/bot<your-bot-token>/sendMessage" -d  "chat_id=<your-chat-id>&text={MESSAGE}&parse_mode=HTML"
    NOTIFICATION_TEMPLATE=
        Hello!
        You have new notification No.{id}:
        <b>{title}</b>
        {MESSAGE}
        <i>The notification has been created {creationTime}</i>
        🚀
    ```


## License
This project is licensed under the Apache License. See the `LICENSE` file for details.