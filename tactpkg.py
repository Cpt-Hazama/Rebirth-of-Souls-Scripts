import os
import struct
import re
import tkinter as tk
import zlib
from tkinter import filedialog
from pathlib import Path

def decompress(path):
    with open(path, "rb") as f:
        header = f.read(4)
        if header != b'PZZE':
            f.seek(0)
            return f.read()

        f.seek(16)
        offset = struct.unpack("<I", f.read(4))[0]
        if offset == 0:
            offset = 24

        f.seek(offset)
        try:
            data = zlib.decompress(f.read())
            return data
        except Exception as e:
            print(f"[!] Failed to decompress {path}: {e}")
            return None

def grabActionData(buffer):
    matches = re.finditer(rb'"kind"\s*:\s*"act_data"\s*,\s*"([^"]+)"\s*:\s*\{.*?"tmo_name"\s*:\s*"([^"]+)"', buffer, re.DOTALL)
    data = []
    for m in matches:
        logic_name = m.group(1).decode("utf-8", errors="ignore")
        tmo_name = m.group(2).decode("utf-8", errors="ignore")
        start = max(0, m.start() - 20)
        end = m.end() + 300
        blob = buffer[start:end].decode("utf-8", errors="ignore")
        data.append((tmo_name.strip(), logic_name.strip(), blob.strip()))
    return data

def grabNames(buffer):
    matches = re.findall(rb'"tmo_name"\s*:\s*"([^"]+)"', buffer)
    return [m.decode("utf-8", errors="ignore").strip() for m in matches]

def extractTMO(buffer, output, tact):
    if not os.path.exists(output):
        os.makedirs(output)

    tmoIndex = [m.start() for m in re.finditer(b'tmo1', buffer)]
    print(f"[+] {tact}: Found {len(tmoIndex)} .tmo1 entries")

    tmo_names = grabNames(buffer)
    actionData = grabActionData(buffer)
    actionMap = {k: blob for k, _, blob in actionData}
    usedNames = set()
    reportLines = []

    for i, start in enumerate(tmoIndex):
        end = tmoIndex[i + 1] if i + 1 < len(tmoIndex) else len(buffer)
        chunk = buffer[start:end]

        if i < len(tmo_names):
            animName = tmo_names[i]
            # animName = tmo_names[i-1]
            if not animName:
                animName = f"anim_{i:03}"
        else:
            animName = f"anim_{i:03}"

        baseName = animName
        count = 1
        while animName in usedNames:
            animName = f"{baseName}_{count}"
            count += 1

        usedNames.add(animName)
        outputPath = os.path.join(output, f"{animName}.tmo")
        with open(outputPath, "wb") as out:
            out.write(chunk)
        print(f"[+] Extracted: {animName}.tmo")

        jsonOutputData = actionMap.get(baseName, "[No JSON match found]")
        reportLines.append(f"{animName}.tmo")
        reportLines.append(jsonOutputData)
        reportLines.append("")

    with open(os.path.join(output, "__animreport.txt"), "w", encoding="utf-8") as report:
        report.write("\n".join(reportLines))

def selection():
    root = tk.Tk()
    root.withdraw()

    filePaths = filedialog.askopenfilenames(
        title="Select one or more .tactpkg files (or cancel to choose a folder)",
        filetypes=[("TACTPKG files", "*.tactpkg")]
    )

    if filePaths:
        return list(filePaths)

    folder = filedialog.askdirectory(title="Select Folder Containing .tactpkg Files")
    if folder:
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.tactpkg')]

    return []

def main():
    paths = selection()
    if not paths:
        print("[!] No valid files selected.")
        return

    for filePath in paths:
        if not os.path.isfile(filePath) or not filePath.endswith(".tactpkg"):
            print(f"[!] Skipped invalid file: {filePath}")
            continue

        tact = Path(filePath).stem
        buffer = decompress(filePath)
        if buffer:
            extractTMO(buffer, os.path.join(os.path.dirname(filePath), tact), tact)

if __name__ == "__main__":
    main()
