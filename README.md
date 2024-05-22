# CloudronWatcher

The tool reads Cloudron alerts and deliver them with the tool of choice to the system of choice.
Also checks applications status and raise an alert if any is failing. 

```bash
sudo apt install python3 python3-venv
git clone https://github.com/NoCloud-today/CloudronWatcher.git
cd CloudronWatcher
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
chmod +x run.sh
vi settings.ini
./run.sh
```

An example crontab entry:
```crontab
*/5 * * * * python3 /.../CloudronWatcher/run.sh
```
