# Contents

## .CAT DDS Editor [WIP]
Used to inject DDS files into .CAT containers (example: replacing character icons or HUD assets)

## PZZE Decompression
Used to decompress files with PZZE compression (can verify with a hex editor by looking for 'PZZE' in the header) and also automatically extracts DDS textures

## Audio Name Patch
Used to repair the names of extracted WAV files to the original names prior to being compiled in Wwise. You can extract the sounds from the .WEM and .BNK files using foobar2000 with the vgmstream plugin

## TACTPKG Label Export
Simple export tool that extracts animation names from TACTPKG files. Mostly personal use on my end to see what all is in the animation files, there's some interesting unused things in here (for example, running animations that every character has but got removed pre-release, which can only be seen in early game trailers)
