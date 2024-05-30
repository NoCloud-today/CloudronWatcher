#!/bin/bash

if [ -f "running.txt" ]; then
  echo "This script has already been run before" >&2
  exit 1
fi

touch "running.txt"

SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd $SCRIPTDIR
source venv/bin/activate
python3 CloudronWatcher.py 2>&1 | tee -a CloudronWatcher.log
#python3 CloudronWatcher.py --debug 2>&1 | tee -a CloudronWatcher.log
rm "running.txt"
