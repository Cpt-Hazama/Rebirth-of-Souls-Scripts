import os
import shutil
import re
import tkinter as tk
from tkinter import filedialog

def main():
    root = tk.Tk()
    root.withdraw()

    wemIDFile = filedialog.askopenfilename(title="Select Sound Bank TXT File", filetypes=[("Text Files", "*.txt")])
    if not wemIDFile:
        print("No TXT file selected. Exiting...")
        return
    wavFolder = filedialog.askdirectory(title="Select Extracted Audio Files Folder")
    if not wavFolder:
        print("No audio folder selected. Exiting...")
        return

    outputDir = os.path.join(wavFolder, "Output")
    os.makedirs(outputDir, exist_ok=True)
    print(f"Processing: {wemIDFile}")
    
    with open(wemIDFile, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    mappingTbl = {}
    for line in lines:
        line = line.strip()
        if not line or not line[0].isdigit():
            continue
        parts = re.split(r'\s+', line)
        if len(parts) >= 2 and parts[0].isdigit():
            wemID = parts[0]
            wemName = parts[1]
            mappingTbl[wemID] = wemName + ".wav"

    for filename in os.listdir(wavFolder):
        # match = re.search(r"\(?(\d+)\)?\.wav$", filename)
        match = re.search(r"\(?(\d+)\)?\.(wem|wav|ogg)$", filename)
        if match:
            wemID = match.group(1)
            if wemID in mappingTbl:
                convName = mappingTbl[wemID]
                oldPath = os.path.join(wavFolder, filename)
                newPath = os.path.join(outputDir, convName)
                shutil.copy(oldPath, newPath)
                print(f"Renamed: {filename} -> {convName}")
            else:
                print(f"No match for ID {wemID}")
    
    print("Renaming complete!")

if __name__ == "__main__":
    main()