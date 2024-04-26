# cloudron-monitor

## Overview

Cloudron Monitor is a Python-based tool designed to enhance the monitoring capabilities of Cloudron instances. It facilitates the fetching of notifications from Cloudron, sending acknowledged notifications to a messaging service, and marking notifications as acknowledged in Cloudron. This project aims to provide a seamless way to keep track of the health and performance of Cloudron deployments, ensuring that users are informed about any important updates or issues.

## Features

- **Notification Fetching**: Automatically fetches notifications from Cloudron using the Cloudron API.
- **Message Sending**: Sends unacknowledged notifications to a messaging service via a bash script.
- **Notification Acknowledgement**: Marks notifications as acknowledged in Cloudron, ensuring that they are not reprocessed.

## Prerequisites

- Python 3.x
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

4. Create file `.env`
```
touch .env
```

5. Ensure that the `.env` file contains the necessary environment variables (`CLOUDRON_TOKEN` and `CLOUDRON_DOMAIN`).

6. Add part of the curl command `URL_API_MESSANGER` to the `.env` file using the instructions in the file `.env_example`

## Usage

To run the Cloudron Monitor, simply execute the `main.py` script:
```
python main.py
```

This script does not require any command-line arguments. It will automatically fetch unacknowledged notifications from Cloudron, send them to the configured messaging service, and mark them as acknowledged in Cloudron.

You can configure the script together with cron.

All successful commands and errors are logged to the corresponding output streams: `stdout` for successful commands and `stderr` for errors. This ensures that the monitoring process is transparent and that any issues can be easily identified and addressed.

## License
This project is licensed under the Apache License. See the `LICENSE` file for details.