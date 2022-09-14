#!/bin/bash
cd ${HOME}
python3 -m venv venv
source "${HOME}/venv/bin/activate"
pip install -r ${HOME}/requirements.txt
deactivate
