# cloudron-monitor

## Overview

Cloudron Monitor is a Python-based tool designed to enhance the monitoring capabilities of Cloudron instances. It facilitates the fetching of notifications from Cloudron, sending acknowledged notifications to a messaging service, and marking notifications as acknowledged in Cloudron. This project aims to provide a seamless way to keep track of the health and performance of Cloudron deployments, ensuring that users are informed about any important updates or issues.

## Features

- **Notification Fetching**: Automatically fetches notifications from Cloudron using the Cloudron API.
- **Message Sending**: Sends unacknowledged notifications to a messaging service via a cURL command.
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

This script does not require any command-line arguments. It will automatically fetch unacknowledged notifications from Cloudron, send them to the configured messaging service, and mark them as acknowledged in Cloudron.

You can configure the script together with cron.

All successful commands and errors are logged to the corresponding output streams: `stdout` for successful commands and `stderr` for errors. This ensures that the monitoring process is transparent and that any issues can be easily identified and addressed.

## License
This project is licensed under the Apache License. See the `LICENSE` file for details.