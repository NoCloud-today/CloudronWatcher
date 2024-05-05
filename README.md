# cloudron-monitor

The tool reads Cloudron alerts and deliver them with the tool of choice to the system of choice.
Also checks applications status and raise an alert if any is failing. 

```bash
sudo apt install python3 python3-venv
git clone https://github.com/NoCloud-today/cloudron-monitor.git
cd cloudron-monitor
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
chmod +x cloudron-monitor.sh
vi settings.ini # specify the way message get delivered; Telegram is provided by default
./cloudron-monitor.sh
```
An example crontab entry:
```
*/5 * * * * python3 /home/user/cloudron_monitor/cloudron_monitor.sh
```
        <i>The notification has been created {creationTime}</i>
        🚀
    ```


## License
This project is licensed under the Apache License. See the `LICENSE` file for details.
