#!/bin/bash
SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd $SCRIPTDIR
source venv/bin/activate
python3 CloudronWatcher.py 2>&1 | tee -a CloudronWatcher.log
#python3 CloudronWatcher.py --debug 2>&1 | tee -a CloudronWatcher.log

