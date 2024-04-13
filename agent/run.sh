#!/bin/bash 
id=$(date '+%Y%m%d.%H%M%S')
cd /aws/apps/agent/
python3.11 agent.py > "agent_$id.log"