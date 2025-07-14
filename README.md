# CovertComm

A Python steganography tool for hiding secret messages in images, audio, video, and text files using LSB (Least Significant Bit) and AES encryption. Features a user-friendly GUI.

---

## Features
- **Image Steganography**: Hide/extract messages in PNG images (LSB, DCT, DWT)
- **Audio Steganography**: Hide/extract messages in WAV audio (LSB)
- **Video Steganography**: Hide/extract messages in video files (LSB, lossless codec required)
- **Text Steganography**: Hide/extract messages in text files using zero-width characters
- **AES Encryption**: All messages are encrypted with a user-supplied key
- **Modern GUI**: Clean, intuitive interface with tabbed workflow
- **Sample files**: Provided for all media types

---

## Requirements
- Python 3.8+
- See `requirements.txt` for dependencies
- For video steganography: FFmpeg recommended for best codec support

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Launch the App
```bash
python -m src.covertcomm_gui
```

### 2. Using the GUI
- **Select the media type tab** (Image, Audio, Video, Text)
- **Select a cover file** (e.g., PNG, WAV, MOV/AVI, TXT)
- **Enter your secret message** and an AES key (password)
- **Click 'Hide Message'** to embed, or 'Extract Message' to reveal a hidden message
- **Output stego files** are saved in the corresponding `samples/stego_*` folders

#### Supported Formats
- **Images**: PNG (lossless)
- **Audio**: WAV (16-bit mono)
- **Video**: MOV, AVI, MKV, MP4 (must use a lossless codec, e.g., FFV1)
- **Text**: TXT (UTF-8)

#### Video Steganography Notes
- **Lossless codec required!** The app uses FFV1 by default for stego video output. Do not use XVID or other lossy codecs, as they will destroy hidden data.
- If you cannot play FFV1 videos, use VLC or convert with FFmpeg.

#### Directory Structure
```
samples/
  cover_images/   # Input images
  stego_images/   # Output stego images
  cover_audio/    # Input audio
  stego_audio/    # Output stego audio
  cover_video/    # Input videos
  stego_video/    # Output stego videos
  stego_txt/      # Output stego text files
```

---

## Samples
Sample cover and stego files are provided in the `samples/` directory for testing and demonstration.

