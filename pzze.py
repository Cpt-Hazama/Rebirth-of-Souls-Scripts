import os
import struct
import zlib

fileDir = os.path.dirname(os.path.abspath(__file__))

def decompress(path):
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != b'PZZE':
                print(f"{path} is not a valid PZZE file.")
                return None

            _ = f.read(12)
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

for filename in os.listdir(fileDir):
    if filename.endswith(".py") or filename.endswith(".md") or filename.endswith(".txt") or filename.endswith(".md"):
        continue
    path = os.path.join(fileDir, filename)
    output = decompress(path)

    if output:
        ddsIndex = output.find(b'DDS ')
        if ddsIndex != -1:
            output = output[ddsIndex:]
            outputDir = os.path.join(fileDir, os.path.splitext(filename)[0] + ".dds")
        else:
            outputDir = os.path.join(fileDir, filename + "_decompressed" + os.path.splitext(filename)[1])

        with open(outputDir, "wb") as f:
            f.write(output)
        print(f"Output saved to {outputDir}")
    else:
        print(f"Skipping {filename}, decompression failed.")
