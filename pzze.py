import os
import struct
import zlib
import re

def decompress(path):
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
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

def findStrings(chunk, minLength=6):
    return re.findall(rb'[ -~]{%d,}' % minLength, chunk)

def extractDDS(chunk, outputDir, baseName):
    os.makedirs(outputDir, exist_ok=True)
    offsets = getOffsets(chunk)
    count = len(offsets) - 1
    stringData = findStrings(chunk, minLength=8)
    entries = [s.decode('ascii', errors='ignore') for s in stringData if b"char" in s or b"2p" in s]
    outputNames = [name.strip(",.") for name in entries if "char_" in name and len(name) <= 32]

    for i in range(count):
        start = offsets[i]
        end = offsets[i + 1]
        imgData = chunk[start:end]
        name = outputNames[i] if i < len(outputNames) else f"{baseName}_{i:02}"
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
        if filename.endswith((".py", ".md", ".txt")) or filename == "output":
            continue

        path = os.path.join(fileDir, filename)
        if os.path.isdir(path):
            continue

        print(f"Processing {filename}...")
        output = decompress(path)
        if output:
            baseName = os.path.splitext(filename)[0]
            outputDir = os.path.join(outputDir, filename)
            os.makedirs(outputDir, exist_ok=True)
            isDDS = extractDDS(output, outputDir, baseName)

            if not isDDS:
                outputPath = os.path.join(fileDir, baseName + "_decompressed" + os.path.splitext(filename)[1])
                with open(outputPath, "wb") as f:
                    f.write(output)
                print(f"Saved decompressed file: {outputPath}")
        else:
            print(f"Skipping {filename}, decompression failed.")