import importlib
import json
import os
import sys
from classes.tagger import classTagger

def main():
    
    # Start Tagging Process
    process_type = sys.argv[1]
    process_id = sys.argv[2]
    tagger = classTagger(process_id)
    
    print(sys.argv)
    if process_type == "inventory":
        tagger.start_inventory_process()
    
    if process_type == "tagging":
        tagger.start_tagging_process(tagger.process_id)
    
if __name__ == "__main__":
    main()
