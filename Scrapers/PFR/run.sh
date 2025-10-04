#!/bin/bash

rm -f log.txt
python -u games-pfr.py 2>&1 | tee -a log.txt
python -u player-stats-pfr.py 2>&1 | tee -a log.txt
python -u defense-pfr.py 2>&1 | tee -a log.txt