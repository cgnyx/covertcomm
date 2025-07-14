from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

ZERO_WIDTH_SPACE = '\u200b'
ZERO_WIDTH_NON_JOINER = '\u200c'

# AES utility functions
def aes_encrypt(data: bytes, key: bytes) -> bytes:
    try:
        key = key[:32].ljust(32, b'0')  # Pad/truncate to 32 bytes
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        return cipher.iv + ct_bytes
    except Exception as e:
        raise RuntimeError(f'Error in AES encryption: {e}')

def aes_decrypt(enc_data: bytes, key: bytes) -> bytes:
    try:
        key = key[:32].ljust(32, b'0')  # Pad/truncate to 32 bytes
        iv = enc_data[:AES.block_size]
        ct = enc_data[AES.block_size:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)
    except Exception as e:
        raise RuntimeError(f'Error in AES decryption: {e}')

def bits_to_zwc(bits):
    return ''.join(ZERO_WIDTH_SPACE if b == '0' else ZERO_WIDTH_NON_JOINER for b in bits)

def zwc_to_bits(zwc):
    return ''.join('0' if c == ZERO_WIDTH_SPACE else '1' for c in zwc if c in (ZERO_WIDTH_SPACE, ZERO_WIDTH_NON_JOINER))

def encode_text(cover_text, secret_message, key, output_path=None, cover_path=None):
    try:
        enc_bytes = aes_encrypt(secret_message.encode(), key)
        length_bytes = len(enc_bytes).to_bytes(4, 'big')
        payload = length_bytes + enc_bytes
        bits = ''.join(f'{byte:08b}' for byte in payload)
        zwc = bits_to_zwc(bits)
        stego_text = cover_text + zwc
        if output_path is None and cover_path is not None:
            base = os.path.basename(cover_path)
            output_path = os.path.join('samples', 'stego_txt', f'stego_{base}')
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(stego_text)
        return output_path
    except Exception as e:
        raise RuntimeError(f'Error in encode_text: {e}')

def decode_text(stego_text, key):
    try:
        zwc = ''.join(c for c in stego_text if c in (ZERO_WIDTH_SPACE, ZERO_WIDTH_NON_JOINER))
        bits = zwc_to_bits(zwc)
        if len(bits) < 32:
            return ''
        length = int(bits[:32], 2)
        enc_bits = bits[32:32+length*8]
        if len(enc_bits) < length*8:
            return ''
        byte_list = [int(enc_bits[i:i+8], 2) for i in range(0, len(enc_bits), 8)]
        enc_bytes = bytes(byte_list)
        msg = aes_decrypt(enc_bytes, key)
        return msg.decode(errors='ignore')
    except Exception as e:
        raise RuntimeError(f'Error in decode_text: {e}') 