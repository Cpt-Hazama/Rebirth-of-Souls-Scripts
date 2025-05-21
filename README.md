# Contents

## .CAT DDS Editor [WIP]
Used to inject DDS files into .CAT containers (example: replacing character icons or HUD assets)

## PZZE Decompression
Used to decompress files with PZZE compression (can verify with a hex editor by looking for 'PZZE' in the header) and also automatically extracts DDS textures

## Audio Name Patch
Used to repair the names of extracted WAV files to the original names prior to being compiled in Wwise. You can extract the sounds from the .WEM and .BNK files using foobar2000 with the vgmstream plugin

## TACTPKG Animation Extractor
Used to select individual or whole folders of TACTPKG files to extract TMO1 animations. Currently DOESN'T get the names, just names them in order of extraction. It will also automatically decompress the file (in the memory) if it wasn't already. (Thank you Hydra for your research ^^)
