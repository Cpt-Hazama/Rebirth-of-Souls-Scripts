import os
import struct
import zlib

fileDir = os.path.dirname(os.path.abspath(__file__))

def decompress(path):
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

for filename in os.listdir(fileDir):
    if filename.endswith(".tactpkg"):
        path = os.path.join(fileDir, filename)
        output = decompress(path)
        
        if output:
            output_path = os.path.join(fileDir, os.path.splitext(filename)[0] + "_decompressed.bin")
            with open(output_path, "wb") as f:
                f.write(output)
            print(f"Decompressed data saved to {output_path}")
        else:
            print(f"Skipping {filename}, decompression failed.")