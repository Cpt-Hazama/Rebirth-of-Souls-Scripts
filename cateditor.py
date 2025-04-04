import os
import struct
import re
import zlib
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

class main:
    def __init__(self, base):
        self.base = base
        self.base.title(".CAT DDS Editor")
        self.data = []
        self.offsets = []
        self.sizes = []
        self.names = []
        self.catPath = None
        self.catData = None
        self.mods = {}
        self.indexes = {}
        self.buildUI()

    def buildUI(self):
        frame = tk.Frame(self.base)
        frame.pack(fill=tk.BOTH, expand=True)
        leftFrame = tk.Frame(frame)
        leftFrame.pack(side=tk.LEFT, fill=tk.Y)
        rightFrame = tk.Frame(frame)
        rightFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.list = tk.Listbox(leftFrame, width=30)
        self.list.pack(fill=tk.Y, expand=True)
        self.list.bind("<<ListboxSelect>>", self.displayPreview)
        self.loadCat = tk.Button(leftFrame, text="Load .CAT File", command=self.processCat)
        self.loadCat.pack(fill=tk.X)
        self.replaceDDS = tk.Button(leftFrame, text="Replace DDS", command=self.stageDDS)
        self.replaceDDS.pack(fill=tk.X)
        self.saveCat = tk.Button(leftFrame, text="Save .CAT File", command=self.saveFile)
        self.saveCat.pack(fill=tk.X)
        self.label = tk.Label(rightFrame, text="DDS Preview")
        self.label.pack()
        self.preview = tk.Label(rightFrame)
        self.preview.pack()
        self.logger = tk.Text(self.base, height=10, bg="black", fg="lime", insertbackground='white')
        self.logger.pack(fill=tk.X)

        self.log("[!] This tool is still a work in progress!")

    def log(self, msg):
        self.logger.insert(tk.END, msg + "\n")
        self.logger.see(tk.END)

    def decompress(self, data):
        if data[:4] != b'PZZE':
            self.log("[!] File is not PZZE compressed.")
            return data
        offset = struct.unpack("<I", data[16:20])[0]
        offset = offset if 0 < offset < len(data) else 24
        try:
            decompressed = zlib.decompress(data[offset:])
            self.log("[+] Successfully decompressed the .CAT file.")
            return decompressed
        except zlib.error:
            self.log("[!] Decompression failed, using raw data.")
            return data

    def processCat(self):
        path = filedialog.askopenfilename(filetypes=[["CAT files", "*.cat"]])
        if not path:
            return

        self.catPath = path
        with open(path, "rb") as f:
            raw = f.read()

        self.catData = bytearray(self.decompress(raw))
        self.grabEntries()
        self.unk370()
        self.unk1190()
        self.log(f"[+] Loaded .CAT file: {os.path.basename(path)}")

    def grabNames(self, data):
        matches = re.findall(rb'[ -~]{6,}', data)
        strings = [s.decode('ascii', errors='ignore').strip(",. ") for s in matches]
        tests = [s for s in strings if len(s) <= 64 and " " not in s and re.match(r"^[\w\-\.]+$", s)]
        seen = set()
        names = []
        for name in tests:
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names

    def grabEntries(self):
        self.offsets.clear()
        self.data.clear()
        self.sizes.clear()
        self.names.clear()
        self.mods.clear()
        self.list.delete(0, tk.END)

        data = self.catData
        index = 0
        while True:
            found = data.find(b'DDS ', index)
            if found == -1:
                break
            self.offsets.append(found)
            index = found + 4
        self.offsets.append(len(data))

        names = self.grabNames(data)
        for i in range(len(self.offsets) - 1):
            start = self.offsets[i]
            end = self.offsets[i + 1]
            dds = data[start:end]
            self.data.append(dds)
            self.sizes.append(end - start) # temp, gets overwritten later
            name = names[i] if i < len(names) else f"INDEX_{i:02}"
            self.names.append(name)
            self.list.insert(tk.END, name)
            if name.startswith("INDEX_"):
                self.list.itemconfig(i, {'fg': 'red'})

        self.log(f"Found {len(self.data)} DDS entries.")

    def unk370(self):
        for i in range(256):
            offset = 0x370 + i * 8
            if offset + 8 > len(self.catData):
                break
            val1, val2 = struct.unpack('<II', self.catData[offset:offset+8])

    def unk1190(self):
        self.indexes.clear()
        for i in range(256):
            offset = 0x1190 + i * 16
            if offset + 16 > len(self.catData):
                break
            val1, val2, val3, val4 = struct.unpack('<IIII', self.catData[offset:offset+16])
            matchNote = ""
            for j in range(len(self.offsets) - 1):
                curOffset = self.offsets[j]
                if abs(val2 - curOffset) <= 32:
                    self.indexes[curOffset] = i
                    matchNote += " [MATCH: offset]"
                    if val3 <= (self.offsets[j + 1] - curOffset):
                        matchNote += " [MATCH: size]"
                        self.sizes[j] = val3 # update size
                        self.data[j] = self.catData[curOffset:curOffset + val3]
                    break

    def displayPreview(self, ev):
        selection = self.list.curselection()
        if not selection:
            return
        index = selection[0]
        data = self.mods.get(index, self.data[index])
        try:
            with open("__temp.dds", "wb") as f:
                f.write(data)
            img = Image.open("__temp.dds")
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            imgPreview = ImageTk.PhotoImage(img)
            self.preview.config(image=imgPreview)
            self.preview.image = imgPreview
        except Exception as e:
            self.log(f"[!] Error loading DDS preview: {e}")

    def stageDDS(self):
        selection = self.list.curselection()
        if not selection:
            return

        index = selection[0]
        path = filedialog.askopenfilename(filetypes=[["DDS files", "*.dds"]])
        if not path:
            return

        try:
            with open(path, "rb") as f:
                stagedFile = bytes(f.read())
        except Exception as e:
            self.log(f"[!] Failed to read DDS file: {e}")
            return

        self.mods[index] = stagedFile
        self.list.itemconfig(index, {'fg': 'blue'})
        self.log(f"[+] Successfully staged DDS file: DDS #{index} ({self.names[index]}) | Size: {len(stagedFile)} | Path: {path}")
        self.displayPreview(None)

    def saveFile(self):
        if not self.mods:
            self.log("[!] No changes to save.")
            return

        HEADER_END = min(offset for offset in self.offsets)
        header = bytearray(self.catData[:HEADER_END])
        # paddingTest = bytes.fromhex(
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        #     "10 00 00 00 01 00 00 00 44 74 00 00 00 00 00 00"
        # )

        self.indexes.clear()
        newBody = bytearray()
        newOffsets = []
        newSizes = []

        for i in range(len(self.data)):
            # isModded = i in self.mods
            dds = self.mods.get(i, self.data[i])
            newOffset = HEADER_END + len(newBody)
            newSize = len(dds)
            newBody += dds
            # if isModded:
                # newBody += paddingTest

            newOffsets.append(newOffset)
            newSizes.append(newSize)
            oldOffset = self.offsets[i]
            entryIndex = self.indexes.get(oldOffset)
            if entryIndex is not None:
                entryOffset = 0x1190 + entryIndex * 16
                if entryOffset + 12 > len(header):
                    self.log(f"[!] Skipping invalid header patch for entry {entryIndex}")
                    continue
                header[entryOffset + 4:entryOffset + 8] = struct.pack('<I', newOffset)
                header[entryOffset + 8:entryOffset + 12] = struct.pack('<I', newSize)
                self.indexes[newOffset] = entryIndex
                self.log(f"[+] Patched Entry {entryIndex:03} ({self.names[i]}) | Offset: 0x{newOffset:08X} | Size: 0x{newSize:08X}")

        newCat = header + newBody
        self.offsets = newOffsets
        self.sizes = newSizes
        for i in range(len(self.data)):
            self.data[i] = self.mods.get(i, self.data[i])

        output = self.catPath.replace(".cat", "_modified.cat")
        with open(output, "wb") as f:
            f.write(newCat)

        self.catData = newCat
        self.log(f"[!] Saved modified .CAT file to: {output}")
        self.mods.clear()

        for index in range(self.list.size()):
            self.list.itemconfig(index, {'fg': 'black'})

if __name__ == "__main__":
    base = tk.Tk()
    app = main(base)
    base.mainloop()