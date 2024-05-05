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
chmod +x cloudron_monitor.sh
vi settings.ini
./cloudron_monitor.sh
```

An example crontab entry:
```crontab
*/5 * * * * python3 /.../cloudron_monitor/cloudron_monitor.sh
```
