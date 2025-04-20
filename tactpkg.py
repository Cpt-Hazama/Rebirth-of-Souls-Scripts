
import os
import json
import re
import sys
from pzze import decompress

def readAnimNames(data):
    labels = set()
    for match in re.finditer(rb'[a-zA-Z0-9_]{8,}', data):
        s = match.group().decode(errors='ignore')
        if any(tag in s.lower() for tag in ["attack", "idle", "move", "dash", "hit", "skill", "atk", "mot", "cam", "pose"]):
            labels.add(s)
    return sorted(labels)

def run(file_path):
    print(f"Processing: {file_path}")
    data = decompress(file_path)
    if not data:
        print("Failed to decompress or invalid file format.")
        return

    labels = readAnimNames(data)
    output = os.path.splitext(file_path)[0] + ".json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)
    print(f"Exported {len(labels)} animation names to: {output}")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        for file in sys.argv[1:]:
            if os.path.isfile(file):
                run(file)
            else:
                print(f"Invalid file: {file}")
    else:
        input("Drag a file onto this script or run it from command line.\nPress Enter to exit...")