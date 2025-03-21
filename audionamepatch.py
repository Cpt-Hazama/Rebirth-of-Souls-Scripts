import os
import shutil
import re
import tkinter as tk
from tkinter import filedialog

# Extract your audio files from the .BNK files using foobar2000
# Note that this is currently only for voice files (and maybe sfx, didn't test)
# I will add music support later, pretty ez to do but I want to play the game now :P

def execute():
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
        parts = line.strip().split("\t")
        if len(parts) >= 2 and parts[0].isdigit():
            wemID = parts[0]  # Memory Audio ID
            wemName = parts[1]  # Name
            mappingTbl[wemID] = wemName + ".wav"
    
    for filename in os.listdir(wavFolder):
        match = re.search(r"\((\d+)\)\.wav$", filename)
        if match:
            wemID = match.group(1)
            
            if wemID in mappingTbl:
                convName = mappingTbl[wemID]
                oldPath = os.path.join(wavFolder, filename)
                newPath = os.path.join(outputDir, convName)
                
                shutil.copy(oldPath, newPath)
                print(f"Renamed: {oldPath} -> {newPath}")
            else:
                print(f"No matching name found for Memory Audio ID: {wemID}")
    
    print("Renaming complete!")

if __name__ == "__main__":
    execute()
