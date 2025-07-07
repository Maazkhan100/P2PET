#!/bin/bash

# This is a simple script used to delete junk

pkill geth # kill the previos geth process if running in the background
rm -rf node*
rm -rf *.log
rm -rf dummy-genesis.json
rm -rf dummy-static-nodes.json