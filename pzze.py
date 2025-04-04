import os
import struct
import zlib
import re

def decompress(path):
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != b'PZZE':
                print(f"{path} is not compressed, attempting raw extraction.")
                f.seek(0)
                return f.read()
            if magic != b'PZZE':
                print(f"{path} is not a valid PZZE file.")
                return None

            f.seek(16)
            offset = struct.unpack("<I", f.read(4))[0]
            if offset == 0 or offset > os.path.getsize(path):
                offset = 24

            f.seek(offset)
            try:
                return zlib.decompress(f.read())
            except zlib.error:
                print(f"Decompression failed for {path}.")
                return None
    except PermissionError:
        return None

def getOffsets(chunk):
    offsets = []
    index = 0
    while True:
        found = chunk.find(b'DDS ', index)
        if found == -1:
            break
        offsets.append(found)
        index = found + 4
    offsets.append(len(chunk))
    return offsets

def extractDDS(chunk, outputDir, baseName):
    os.makedirs(outputDir, exist_ok=True)
    offsets = getOffsets(chunk)
    count = len(offsets) - 1
    stringData = re.findall(rb'[ -~]{6,}', chunk)
    entries = [s.decode('ascii', errors='ignore').strip(",. ") for s in stringData]
    testNames = [s for s in entries if len(s) <= 64 and " " not in s and re.match(r"^[\w\-\.]+$", s)]
    seen = set()
    outputNames = []
    for name in testNames:
        if name not in seen:
            seen.add(name)
            outputNames.append(name)

    for i in range(count):
        start = offsets[i]
        end = offsets[i + 1]
        imgData = chunk[start:end]
        name = re.sub(r'[<>:"/\\|?*]', '_', outputNames[i] if i < len(outputNames) else f"{baseName}_{i:02}")
        path = os.path.join(outputDir, f"{name}.dds")
        with open(path, "wb") as f:
            f.write(imgData)
        print(f"Saved DDS image: {path}")

    return count > 0

if __name__ == "__main__":
    fileDir = os.path.dirname(os.path.abspath(__file__))
    outputDir = os.path.join(fileDir, "output")
    os.makedirs(outputDir, exist_ok=True)

    for filename in os.listdir(fileDir):
        if filename.endswith((".py", ".md", ".txt", ".gitattributes", ".git")) or filename == "output":
            continue

        path = os.path.join(fileDir, filename)
        if os.path.isdir(path):
            continue

        print(f"Processing {filename}...")
        output = decompress(path)
        if output:
            baseName = os.path.splitext(filename)[0]
            fileOutputDir = os.path.join(outputDir, baseName)
            os.makedirs(fileOutputDir, exist_ok=True)
            isDDS = extractDDS(output, fileOutputDir, baseName)

            if not isDDS:
                outputPath = os.path.join(fileDir, baseName + "_decompressed" + os.path.splitext(filename)[1])
                with open(outputPath, "wb") as f:
                    f.write(output)
                print(f"Saved decompressed file: {outputPath}")
        else:
            print(f"Skipping {filename}, decompression failed.")