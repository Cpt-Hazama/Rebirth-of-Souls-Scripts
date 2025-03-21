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
    path = os.path.join(fileDir, filename)
    output = decompress(path)
    
    if output:
        outputDir = os.path.join(fileDir, os.path.splitext(filename)[0] + "_decompressed.bin")
        with open(outputDir, "wb") as f:
            f.write(output)
        print(f"Decompressed data saved to {outputDir}")
    else:
        print(f"Skipping {filename}, decompression failed.")