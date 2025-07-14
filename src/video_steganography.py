import cv2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import numpy as np
import os
import random

# AES utility functions
def aes_encrypt(data: bytes, key: bytes) -> bytes:
    key = key[:32].ljust(32, b'0')  # Pad/truncate to 32 bytes
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes

def aes_decrypt(enc_data: bytes, key: bytes) -> bytes:
    key = key[:32].ljust(32, b'0')  # Pad/truncate to 32 bytes
    iv = enc_data[:AES.block_size]
    ct = enc_data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

def get_prng_positions(num_bits, frame_shape, num_frames, key):
    h, w, c = frame_shape
    total_pixels = h * w * num_frames
    if num_bits > total_pixels:
        raise ValueError('Message too large to fit in video.')
    seed = int.from_bytes(key, 'big') % (2**32 - 1)
    rng = np.random.default_rng(seed)
    positions = rng.choice(total_pixels, size=num_bits, replace=False)
    return positions.tolist()

def encode_video(input_video_path, secret_message, key, output_video_path=None):
    try:
        enc_bytes = aes_encrypt(secret_message.encode(), key)
        length_bytes = len(enc_bytes).to_bytes(4, 'big')
        payload = length_bytes + enc_bytes
        bits = ''.join(f'{byte:08b}' for byte in payload)
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise IOError(f'Cannot open video file: {input_video_path}')
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        c = 3
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_pixels = h * w * num_frames
        if len(bits) > total_pixels:
            cap.release()
            raise ValueError('Message too large to fit in video.')
        if output_video_path is None:
            base = os.path.basename(input_video_path)
            output_video_path = os.path.join('samples', 'stego_video', f'stego_{base}')
        # Use FFV1 lossless codec for output
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter(output_video_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (w, h))
        bit_idx = 0
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = frame.astype(np.uint8)
            for i in range(h):
                for j in range(w):
                    if bit_idx >= len(bits):
                        break
                    frame[i, j, 0] = (frame[i, j, 0] & 0xFE) | int(bits[bit_idx])
                    bit_idx += 1
                if bit_idx >= len(bits):
                    break
            out.write(frame)
            frame_idx += 1
        cap.release()
        out.release()
        return output_video_path
    except Exception as e:
        raise RuntimeError(f'Error in encode_video: {e}')


def decode_video(stego_video_path, key):
    try:
        cap = cv2.VideoCapture(stego_video_path)
        if not cap.isOpened():
            raise IOError(f'Cannot open video file: {stego_video_path}')
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        c = 3
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_pixels = h * w * num_frames
        # First, extract 32 bits (4 bytes) for the length
        bits = []
        bit_idx = 0
        frame_idx = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        while bit_idx < 32:
            ret, frame = cap.read()
            if not ret:
                break
            frame = frame.astype(np.uint8)
            for i in range(h):
                for j in range(w):
                    if bit_idx < 32:
                        bits.append(str(frame[i, j, 0] & 1))
                        bit_idx += 1
                    else:
                        break
                if bit_idx >= 32:
                    break
        length_bytes = bytes([int(''.join(bits[i:i+8]), 2) for i in range(0, 32, 8)])
        msg_len = int.from_bytes(length_bytes, 'big')
        if msg_len <= 0 or msg_len > (total_pixels - 32) // 8:
            cap.release()
            return ''
        # Now extract the message
        msg_bits = msg_len * 8
        bits = []
        bit_idx = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        skip_bits = 32
        curr_bit = 0
        while curr_bit < (msg_bits + skip_bits):
            ret, frame = cap.read()
            if not ret:
                break
            frame = frame.astype(np.uint8)
            for i in range(h):
                for j in range(w):
                    if curr_bit < skip_bits:
                        curr_bit += 1
                        continue
                    if len(bits) < msg_bits:
                        bits.append(str(frame[i, j, 0] & 1))
                        curr_bit += 1
                    else:
                        break
                if len(bits) >= msg_bits:
                    break
            if len(bits) >= msg_bits:
                break
        byte_list = [int(''.join(bits[i:i+8]), 2) for i in range(0, len(bits), 8)]
        try:
            enc_bytes = bytes(byte_list)
            msg = aes_decrypt(enc_bytes, key)
            cap.release()
            return msg.decode(errors='ignore')
        except Exception:
            cap.release()
            return ''
    except Exception as e:
        raise RuntimeError(f'Error in decode_video: {e}') 