# CovertComm

A modern Python steganography tool for hiding secret messages in images and audio files using LSB (Least Significant Bit) with password-based encryption and pseudo-random placement.

## Features
- Hide and extract messages in PNG images and WAV audio files
- AES encryption for messages (password required)
- Pseudo-random LSB placement (password-protected)
- Simple, user-friendly GUI

## Requirements
- Python 3.8+
- See `requirements.txt` for dependencies

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python -m src.covertcomm_gui
   ```
3. Use the GUI to select a cover file, enter your message and password, and hide or extract messages securely.

## Samples
Sample cover and stego files are provided in the `samples/` directory.

---
For more details, see code comments or contact the author. 