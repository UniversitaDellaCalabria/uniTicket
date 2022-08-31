#!/bin/bash

# Copy your configuration to a separate folder
export EXPFOLDER="examples-docker"
cp -R uniticket $EXPFOLDER
cp -R uniticket/uni_ticket_project/settingslocal.py.example $EXPFOLDER/uni_ticket_project/settingslocal.py
cp -R dumps $EXPFOLDER

# remove dev db
rm -f $EXPFOLDER/uniticket/db.sqlite3 
