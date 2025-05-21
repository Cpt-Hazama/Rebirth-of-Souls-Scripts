import os
import struct
import re
import tkinter as tk
import zlib
from tkinter import filedialog
from pathlib import Path
from typing import Optional

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

def grabNames(buffer, count): # Nasty and unreliable bwahaha
    # raw = re.split(rb'\x00+', buffer[0x10:0x8100])
    decoded = []
    # seen = set()
    # for s in raw:
    #     try:
    #         if len(s) < 6:
    #             continue
    #         text = s.decode('ascii')
    #         if (
    #             '_' in text
    #             and text[0].isalnum()
    #             and len(text) >= 8
    #             and text not in seen
    #         ):
    #             decoded.append(text)
    #             seen.add(text)
    #     except:
    #         continue
    return decoded[:count]

def parseTMO(chunk):
    try:
        if chunk[:4] != b'tmo1':
            return None
        keyframeCount = struct.unpack_from('<I', chunk, 0x34)[0]
        frameCount = struct.unpack_from('<I', chunk, 0x3C)[0]
        boneCount = struct.unpack_from('<I', chunk, 0x40)[0]
        if frameCount > 10000 or boneCount > 500 or keyframeCount > 100000:
            return None
        return {
            "frames": frameCount,
            "bones": boneCount,
            "keyframes": keyframeCount
        }
    except Exception:
        return None

def extractTMO(buffer, output, tact):
    if not os.path.exists(output):
        os.makedirs(output)

    indexes = [m.start() for m in re.finditer(b'tmo1', buffer)]
    print(f"[+] {tact}: Found {len(indexes)} .tmo1 entries")

    tmoNames = grabNames(buffer, len(indexes))
    usedNames = set()
    reportLines = []

    for i, start in enumerate(indexes):
        end = indexes[i + 1] if i + 1 < len(indexes) else len(buffer)
        chunk = buffer[start:end]
        info = parseTMO(chunk)

        if i < len(tmoNames):
            name = tmoNames[i].strip()
            animName = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        else:
            animName = f"anim_{i:03}"

        count = 1
        while animName in usedNames:
            animName = f"{animName}_{count}"
            count += 1

        usedNames.add(animName)
        with open(os.path.join(output, f"{animName}.tmo"), "wb") as out:
            out.write(chunk)

        print(f"[+] Extracted: {animName}.tmo")

        if info:
            reportLines.append(f"{animName}.tmo, {info['frames']} frames, {info['bones']} bones, {info['keyframes']} keyframes")

    with open(os.path.join(output, "__animreport.txt"), "w") as report:
        report.write("FileName, FrameCount, BoneCount, KeyframeCount\n")
        for line in reportLines:
            report.write(line + "\n")

def selection():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select a .tactpkg File or Cancel to Select Folder", filetypes=[("TACTPKG files", "*.tactpkg")])
    if not path:
        path = filedialog.askdirectory(title="Select Folder Containing .tactpkg Files")
    return path

def main():
    path = selection()
    if not path:
        print("[!] No path selected!")
        return

    paths = []
    if os.path.isdir(path):
        paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.tactpkg')]
    elif path.endswith(".tactpkg"):
        paths = [path]
    else:
        print("[!] Invalid file or folder!")
        return

    for filePath in paths:
        tact = Path(filePath).stem
        buffer = decompress(filePath)
        if buffer:
            extractTMO(buffer, os.path.join(os.path.dirname(filePath), tact), tact)

if __name__ == "__main__":
    main()