#!/usr/bin/env bash

sudo mkdir /usr/bin/dsklite
sudo cp main.py /usr/bin/dsklite
sudo chown root /usr/bin/dsklite/main.py
sudo cp dsklite.sh /usr/bin
sudo chown root /usr/bin/dsklite.sh
sudo chmod u+s /usr/bin/dsklite.sh
sudo chmod u+s /usr/bin/dsklite/main.py
