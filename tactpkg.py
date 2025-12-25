import os
import struct
import re
import zlib
from pathlib import Path

def decompress(path: str) -> bytes | None:
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
            return zlib.decompress(f.read())
        except Exception as e:
            print(f"[!] Failed to decompress {path}: {e}")
            return None

def grabActionData(buffer: bytes):
    matches = re.finditer(
        rb'"kind"\s*:\s*"act_data"\s*,\s*"([^"]+)"\s*:\s*\{.*?"tmo_name"\s*:\s*"([^"]+)"',
        buffer,
        re.DOTALL
    )
    out = []
    for m in matches:
        logicName = m.group(1).decode("utf-8", errors="ignore").strip()
        tmoName = m.group(2).decode("utf-8", errors="ignore").strip()
        start = max(0, m.start() - 40)
        end = min(len(buffer), m.end() + 400)
        blob = buffer[start:end].decode("utf-8", errors="ignore")
        out.append((tmoName, logicName, blob.strip()))
    return out

def getAll(hay: bytes, needle: bytes):
    start = 0
    while True:
        i = hay.find(needle, start)
        if i == -1:
            return
        yield i
        start = i + 1

def parseTable(buffer: bytes):
    """
    0x00: 'acttmo_pkg' (null padded to 0x10 bytes)
    0x10..0x1F: zeros / hash-ish
    0x20: u32 count
    0x24: count records, each 0x48:
        0x00..0x3F: name[0x40] null padded (tmo base name)
        0x40..0x43: u32 data_offset (relative to acttmo_pkg start)
        0x44..0x47: u32 dataSize
    then binary blobs live at acttmo_pkg_start + data_offset
    """
    pkgs = []
    for base in getAll(buffer, b"acttmo_pkg"):
        if base + 0x24 > len(buffer):
            continue
        count = struct.unpack_from("<I", buffer, base + 0x20)[0]
        recsStart = base + 0x24
        recsEnd = recsStart + (count * 0x48)
        if recsEnd > len(buffer):
            continue
        recs = []
        for i in range(count):
            off = recsStart + i * 0x48
            rawName = buffer[off:off + 0x40]
            name = rawName.split(b"\x00", 1)[0].decode("utf-8", errors="ignore").strip()
            dataOff, dataSize = struct.unpack_from("<II", buffer, off + 0x40)
            absOff = base + dataOff
            if absOff < 0 or absOff + dataSize > len(buffer):
                recs.append((name, dataOff, dataSize, False))
                continue
            ok = buffer[absOff:absOff + 4] == b"tmo1"
            recs.append((name, dataOff, dataSize, ok))
        pkgs.append((base, recs))
    return pkgs

def formatFileName(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_").replace(":", "_")
    name = re.sub(r"[<>\"|?*\x00-\x1f]", "_", name)
    return name

def extract(buffer: bytes, output_dir: str, tact_name: str):
    os.makedirs(output_dir, exist_ok=True)
    pkgs = parseTable(buffer)
    if not pkgs:
        print(f"[!] {tact_name}: No acttmo_pkg sections found.")
        return
    actionData = grabActionData(buffer)
    actionMap = {}
    for tmoName, logicName, blob in actionData:
        actionMap.setdefault(tmoName, []).append((logicName, blob))
    used = set()
    reportLines = []
    totalWritten = 0
    for pkgIndex, (base, recs) in enumerate(pkgs):
        print(f"[+] {tact_name}: acttmo_pkg[{pkgIndex}] @ 0x{base:X} with {len(recs)} entries")
        for i, (name, dataOff, dataSize, ok) in enumerate(recs):
            if not name:
                name = f"anim_{pkgIndex}_{i:03}"
            fileBase = formatFileName(name)
            final = fileBase
            n = 1
            while final.lower() in used:
                final = f"{fileBase}_{n}"
                n += 1
            used.add(final.lower())
            absOff = base + dataOff
            blob = buffer[absOff:absOff + dataSize]
            outFile = os.path.join(output_dir, f"{final}.tmo")
            with open(outFile, "wb") as out:
                out.write(blob)
            totalWritten += 1
            warn = "" if ok else " [!hdr?]"
            print(f"[+] Extracted: {final}.tmo  (off=0x{absOff:X} size=0x{dataSize:X}){warn}")
            snippets = actionMap.get(name) or actionMap.get(fileBase) or []
            reportLines.append(f"{final}.tmo  (source_name='{name}')")
            if snippets:
                for logicName, snippet in snippets:
                    reportLines.append(f" - logic: {logicName}")
                    reportLines.append(snippet)
            else:
                reportLines.append(" [No JSON match found]")
            reportLines.append("")

    reportFile = os.path.join(output_dir, "__animreport.txt")
    with open(reportFile, "w", encoding="utf-8") as report:
        report.write("\n".join(reportLines))
    print(f"[+] {tact_name}: Wrote {totalWritten} TMO files")
    print(f"[+] Report: {reportFile}")

def selection():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        return []
    root = tk.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="Select one or more .tactpkg files (or cancel to choose a folder)",
        filetypes=[("TACTPKG files", "*.tactpkg")]
    )
    if paths:
        return list(paths)
    folder = filedialog.askdirectory(title="Select Folder Containing .tactpkg Files")
    if folder:
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".tactpkg")]
    return []

def main(argv=None):
    import sys
    if argv is None:
        argv = sys.argv[1:]
    paths = [p for p in argv if p.lower().endswith(".tactpkg")] if argv else selection()
    if not paths:
        print("[!] No valid .tactpkg files selected/provided.")
        return
    for filePath in paths:
        if not os.path.isfile(filePath) or not filePath.lower().endswith(".tactpkg"):
            print(f"[!] Skipped invalid file: {filePath}")
            continue
        tact = Path(filePath).stem
        outDir = os.path.join(os.path.dirname(filePath), tact)
        buffer = decompress(filePath)
        if not buffer:
            continue
        extract(buffer, outDir, tact)

if __name__ == "__main__":
    main()