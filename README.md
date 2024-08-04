# ffmpeg_cli_gen

A very basic ffmpeg command line generator made solely for me.  
Purpose: create a queue of videos to downscale to either 2560x1440 or 1920x1080 and change bitrates as necessary.

i.e. take fields like Input File:, Resolution, Bitrate, Output File, and build a command line which can be used to render it in ffmpeg.  
Then take this command and add it to a queue, and when all videos you want have been added press Start Rendering to run each command line in the queue.

## Requirements:

AMD gpu (this is hardcoded for now)  
ffmpeg: installed and ffmpeg set in PATH  
ffmpeg: for py (pip install python-ffmpeg)  
PySide6: Qt for python (pip install Pyside6)

run in command line by:  
`py ffmpeg_cli_gen.py`
