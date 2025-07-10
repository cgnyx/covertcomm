"""
CovertComm Core Module
Handles the core steganography functionality using DCT and DWT algorithms.
"""

import os
import wave
import numpy as np
from PIL import Image
import cv2
import pywt
from scipy.fft import dct, idct
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# Helper functions for PKCS7 padding

def pad(data):
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len] * pad_len)

def unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]

def aes_encrypt(plaintext, key):
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')
    if isinstance(key, str):
        key = key.encode('utf-8')
    key = key[:32].ljust(32, b'0')  # Ensure 32 bytes for AES-256
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext)
    ciphertext = cipher.encrypt(padded)
    return base64.b64encode(iv + ciphertext).decode('utf-8')

def aes_decrypt(ciphertext, key):
    if isinstance(ciphertext, str):
        ciphertext = base64.b64decode(ciphertext)
    if isinstance(key, str):
        key = key.encode('utf-8')
    key = key[:32].ljust(32, b'0')  # Ensure 32 bytes for AES-256
    iv = ciphertext[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext[16:])
    return unpad(padded).decode('utf-8')


class ImageSteganography:
    """Handles image steganography using DCT and DWT techniques."""
    
    def __init__(self):
        self.stop_sequence = "1111111111111110"  # 16-bit stop sequence
        self.block_size = 8  # For DCT blocks
        self.quantization_factor = 10  # Controls embedding strength
    
    def text_to_binary(self, text):
        """Convert text to binary string."""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary
    
    def binary_to_text(self, binary_string):
        """Convert binary string to text."""
        text = ''
        for i in range(0, len(binary_string), 8):
            byte = binary_string[i:i+8]
            if len(byte) == 8:
                try:
                    text += chr(int(byte, 2))
                except ValueError:
                    continue
        return text
    
    def calculate_capacity_dct(self, image_path):
        """Calculate maximum message capacity for DCT method."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img)
                height, width = img_array.shape[:2]
                
                # Calculate number of 8x8 blocks
                blocks_h = height // self.block_size
                blocks_w = width // self.block_size
                
                # Each block can hide 1 bit in each color channel
                max_bits = blocks_h * blocks_w * 3
                # Account for stop sequence
                max_bits -= len(self.stop_sequence)
                # Convert to characters
                max_chars = max_bits // 8
                return max_chars
        except Exception as e:
            raise Exception(f"Error calculating DCT capacity: {str(e)}")
    
    def calculate_capacity_dwt(self, image_path):
        """Calculate maximum message capacity for DWT method."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img)
                height, width = img_array.shape[:2]
                
                # DWT decomposes into 4 subbands, we'll use HL and LH
                # Each pixel in these subbands can potentially hide 1 bit
                max_bits = (height * width * 3) // 4  # Approximate capacity
                # Account for stop sequence
                max_bits -= len(self.stop_sequence)
                # Convert to characters
                max_chars = max_bits // 8
                return max_chars
        except Exception as e:
            raise Exception(f"Error calculating DWT capacity: {str(e)}")
    
    def calculate_capacity_lsb(self, image_path):
        """Calculate maximum message capacity for LSB method (in characters)."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_array = np.array(img)
                height, width = img_array.shape[:2]
                # Each color channel in each pixel can hide 1 bit
                max_bits = height * width * 3
                max_bits -= len(self.stop_sequence)
                max_chars = max_bits // 8
                return max_chars
        except Exception as e:
            raise Exception(f"Error calculating LSB capacity: {str(e)}")
    
    def calculate_capacity(self, image_path, method='lsb'):
        """Calculate maximum message capacity."""
        if method == 'lsb':
            return self.calculate_capacity_lsb(image_path)
        elif method == 'dct':
            return self.calculate_capacity_dct(image_path)
        elif method == 'dwt':
            return self.calculate_capacity_dwt(image_path)
        else:
            raise ValueError("Method must be 'lsb', 'dct' or 'dwt'")
    
    def dct_2d(self, block):
        """Apply 2D DCT to a block."""
        return dct(dct(block.T, norm='ortho').T, norm='ortho')
    
    def idct_2d(self, block):
        """Apply 2D inverse DCT to a block."""
        return idct(idct(block.T, norm='ortho').T, norm='ortho')
    
    def hide_message_dct(self, image_path, message, output_path):
        """Hide message using DCT method."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img, dtype=np.float32)
                height, width = img_array.shape[:2]
                
                # Check capacity
                max_chars = self.calculate_capacity_dct(image_path)
                if len(message) > max_chars:
                    raise Exception(f"Message too long! Maximum capacity: {max_chars} characters")
                
                # Convert message to binary
                binary_message = self.text_to_binary(message) + self.stop_sequence
                
                # Process each color channel
                bit_index = 0
                for channel in range(3):
                    if bit_index >= len(binary_message):
                        break
                    
                    # Process 8x8 blocks
                    for i in range(0, height - self.block_size + 1, self.block_size):
                        for j in range(0, width - self.block_size + 1, self.block_size):
                            if bit_index >= len(binary_message):
                                break
                            
                            # Extract 8x8 block
                            block = img_array[i:i+self.block_size, j:j+self.block_size, channel]
                            
                            # Apply DCT
                            dct_block = self.dct_2d(block)
                            
                            # Embed bit in mid-frequency coefficient (position [4,4])
                            bit_to_embed = int(binary_message[bit_index])
                            
                            # Modify DCT coefficient
                            if bit_to_embed == 1:
                                dct_block[4, 4] = abs(dct_block[4, 4]) + self.quantization_factor
                            else:
                                dct_block[4, 4] = abs(dct_block[4, 4]) - self.quantization_factor
                            
                            # Apply inverse DCT
                            modified_block = self.idct_2d(dct_block)
                            
                            # Update image
                            img_array[i:i+self.block_size, j:j+self.block_size, channel] = modified_block
                            
                            bit_index += 1
                
                # Convert back to image
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)
                stego_img = Image.fromarray(img_array)
                stego_img.save(output_path, 'PNG')
                
                return True
                
        except Exception as e:
            raise Exception(f"Error hiding message with DCT: {str(e)}")
    
    def extract_message_dct(self, stego_image_path):
        """Extract message using DCT method."""
        try:
            with Image.open(stego_image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img, dtype=np.float32)
                height, width = img_array.shape[:2]
                
                # Extract bits
                binary_message = ''
                
                # Process each color channel
                for channel in range(3):
                    # Process 8x8 blocks
                    for i in range(0, height - self.block_size + 1, self.block_size):
                        for j in range(0, width - self.block_size + 1, self.block_size):
                            # Extract 8x8 block
                            block = img_array[i:i+self.block_size, j:j+self.block_size, channel]
                            
                            # Apply DCT
                            dct_block = self.dct_2d(block)
                            
                            # Extract bit from mid-frequency coefficient
                            coeff = dct_block[4, 4]
                            
                            # Determine bit based on coefficient sign/magnitude
                            if coeff > 0:
                                binary_message += '1'
                            else:
                                binary_message += '0'
                            
                            # Check for stop sequence
                            if len(binary_message) >= len(self.stop_sequence):
                                if binary_message[-len(self.stop_sequence):] == self.stop_sequence:
                                    # Remove stop sequence and convert to text
                                    binary_message = binary_message[:-len(self.stop_sequence)]
                                    return self.binary_to_text(binary_message)
                
                # If no stop sequence found, return what we have
                return self.binary_to_text(binary_message)
                
        except Exception as e:
            raise Exception(f"Error extracting message with DCT: {str(e)}")
    
    def hide_message_dwt(self, image_path, message, output_path):
        """Hide message using DWT method."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img, dtype=np.float32)
                
                # Check capacity
                max_chars = self.calculate_capacity_dwt(image_path)
                if len(message) > max_chars:
                    raise Exception(f"Message too long! Maximum capacity: {max_chars} characters")
                
                # Convert message to binary
                binary_message = self.text_to_binary(message) + self.stop_sequence
                
                # Process each color channel
                bit_index = 0
                for channel in range(3):
                    if bit_index >= len(binary_message):
                        break
                    
                    # Apply DWT
                    coeffs = pywt.dwt2(img_array[:, :, channel], 'haar')
                    cA, (cH, cV, cD) = coeffs
                    
                    # Embed in horizontal and vertical detail coefficients
                    detail_coeffs = [cH, cV]
                    
                    for detail_coeff in detail_coeffs:
                        if bit_index >= len(binary_message):
                            break
                        
                        # Flatten coefficient matrix
                        flat_coeff = detail_coeff.flatten()
                        
                        # Embed bits in significant coefficients
                        for i in range(0, len(flat_coeff), 4):  # Skip some coefficients
                            if bit_index >= len(binary_message):
                                break
                            
                            bit_to_embed = int(binary_message[bit_index])
                            
                            # Modify coefficient based on bit
                            if bit_to_embed == 1:
                                flat_coeff[i] = abs(flat_coeff[i]) + self.quantization_factor
                            else:
                                flat_coeff[i] = abs(flat_coeff[i]) - self.quantization_factor
                            
                            bit_index += 1
                        
                        # Reshape back
                        detail_coeff[:] = flat_coeff.reshape(detail_coeff.shape)
                    
                    # Reconstruct image
                    reconstructed = pywt.idwt2((cA, (cH, cV, cD)), 'haar')
                    img_array[:, :, channel] = reconstructed
                
                # Convert back to image
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)
                stego_img = Image.fromarray(img_array)
                stego_img.save(output_path, 'PNG')
                
                return True
                
        except Exception as e:
            raise Exception(f"Error hiding message with DWT: {str(e)}")
    
    def extract_message_dwt(self, stego_image_path):
        """Extract message using DWT method."""
        try:
            with Image.open(stego_image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array
                img_array = np.array(img, dtype=np.float32)
                
                # Extract bits
                binary_message = ''
                
                # Process each color channel
                for channel in range(3):
                    # Apply DWT
                    coeffs = pywt.dwt2(img_array[:, :, channel], 'haar')
                    cA, (cH, cV, cD) = coeffs
                    
                    # Extract from horizontal and vertical detail coefficients
                    detail_coeffs = [cH, cV]
                    
                    for detail_coeff in detail_coeffs:
                        # Flatten coefficient matrix
                        flat_coeff = detail_coeff.flatten()
                        
                        # Extract bits from significant coefficients
                        for i in range(0, len(flat_coeff), 4):  # Skip some coefficients
                            coeff = flat_coeff[i]
                            
                            # Extract bit based on coefficient sign/magnitude
                            if coeff > 0:
                                binary_message += '1'
                            else:
                                binary_message += '0'
                            
                            # Check for stop sequence
                            if len(binary_message) >= len(self.stop_sequence):
                                if binary_message[-len(self.stop_sequence):] == self.stop_sequence:
                                    # Remove stop sequence and convert to text
                                    binary_message = binary_message[:-len(self.stop_sequence)]
                                    return self.binary_to_text(binary_message)
                
                # If no stop sequence found, return what we have
                return self.binary_to_text(binary_message)
                
        except Exception as e:
            raise Exception(f"Error extracting message with DWT: {str(e)}")
    
    def hide_message_lsb(self, image_path, message, output_path, password=None):
        """Hide message in image using LSB method with pseudo-random placement (optimized with NumPy)."""
        import numpy as np
        import hashlib
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_array = np.array(img)
                max_chars = self.calculate_capacity_lsb(image_path)
                if len(message) > max_chars:
                    raise Exception(f"Message too long! Maximum capacity: {max_chars} characters")
                binary_message = self.text_to_binary(message) + self.stop_sequence
                total_bits = len(binary_message)
                flat_img = img_array.flatten()
                if total_bits > len(flat_img):
                    raise Exception("Image too small to hide the message.")
                # Use int seed from password hash or message length
                if password:
                    seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % (2**32)
                else:
                    seed = len(message)
                rng = np.random.default_rng(seed)
                indices = rng.permutation(len(flat_img))[:total_bits]
                bits = np.fromiter((int(b) for b in binary_message), dtype=np.uint8)
                flat_img[indices] = (flat_img[indices] & 0xFE) | bits
                stego_array = flat_img.reshape(img_array.shape)
                stego_img = Image.fromarray(stego_array.astype(np.uint8))
                stego_img.save(output_path, 'PNG')
                return True
        except Exception as e:
            raise Exception(f"Error hiding message with LSB: {str(e)}")

    def extract_message_lsb(self, stego_image_path, password=None, message_length=None):
        """Extract message from image using LSB method with pseudo-random placement (optimized with NumPy)."""
        import numpy as np
        import hashlib
        try:
            with Image.open(stego_image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_array = np.array(img)
                flat_img = img_array.flatten()
                if message_length is None:
                    max_bits = len(flat_img)
                else:
                    max_bits = message_length * 8 + len(self.stop_sequence)
                if password:
                    seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % (2**32)
                else:
                    seed = message_length if message_length is not None else len(flat_img)
                rng = np.random.default_rng(seed)
                indices = rng.permutation(len(flat_img))[:max_bits]
                bits = flat_img[indices] & 1
                binary_message = ''.join(bits.astype(str))
                stop_idx = binary_message.find(self.stop_sequence)
                if stop_idx != -1:
                    binary_message = binary_message[:stop_idx]
                return self.binary_to_text(binary_message)
        except Exception as e:
            raise Exception(f"Error extracting message with LSB: {str(e)}")
    
    def hide_message_in_image(self, image_path, message, output_path, method='lsb', password=None):
        """Hide message in image using specified method."""
        if method == 'lsb':
            return self.hide_message_lsb(image_path, message, output_path, password=password)
        elif method == 'dct':
            return self.hide_message_dct(image_path, message, output_path)
        elif method == 'dwt':
            return self.hide_message_dwt(image_path, message, output_path)
        else:
            raise ValueError("Method must be 'lsb', 'dct' or 'dwt'")
    
    def extract_message_from_image(self, stego_image_path, method='lsb', password=None):
        """Extract message from image using specified method."""
        if method == 'lsb':
            return self.extract_message_lsb(stego_image_path, password=password)
        elif method == 'dct':
            return self.extract_message_dct(stego_image_path)
        elif method == 'dwt':
            return self.extract_message_dwt(stego_image_path)
        else:
            raise ValueError("Method must be 'lsb', 'dct' or 'dwt'")


class AudioSteganography:
    """Handles audio steganography using LSB technique only."""
    
    def __init__(self):
        self.stop_sequence = "1111111111111110"  # 16-bit stop sequence
        self.frame_size = 1024  # For DCT frames (unused)
        self.quantization_factor = 0.01  # Controls embedding strength (unused)
    
    def text_to_binary(self, text):
        """Convert text to binary string."""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary
    
    def binary_to_text(self, binary_string):
        """Convert binary string to text."""
        text = ''
        for i in range(0, len(binary_string), 8):
            byte = binary_string[i:i+8]
            if len(byte) == 8:
                try:
                    text += chr(int(byte, 2))
                except ValueError:
                    continue
        return text
    
    def calculate_capacity_lsb_audio(self, audio_path):
        """Calculate maximum message capacity for LSB audio (in characters)."""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                if params.sampwidth != 2 or params.nchannels != 1:
                    raise Exception("Only 16-bit mono WAV files are supported for LSB audio.")
                frames = wav_file.getnframes()
                # Each sample can hide 1 bit
                max_bits = frames
                max_bits -= len(self.stop_sequence)
                max_chars = max_bits // 8
                return max_chars
        except Exception as e:
            raise Exception(f"Error calculating LSB audio capacity: {str(e)}")

    def hide_message_lsb_audio(self, audio_path, message, output_path, password=None):
        """Hide message in audio using LSB method with pseudo-random placement (optimized with NumPy)."""
        import numpy as np
        import hashlib
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                if params.sampwidth != 2 or params.nchannels != 1:
                    raise Exception("Only 16-bit mono WAV files are supported for LSB audio.")
                frames = wav_file.readframes(params.nframes)
                audio_data = np.frombuffer(frames, dtype=np.int16).copy()
                max_chars = self.calculate_capacity_lsb_audio(audio_path)
                if len(message) > max_chars:
                    raise Exception(f"Message too long! Maximum capacity: {max_chars} characters")
                binary_message = self.text_to_binary(message) + self.stop_sequence
                total_bits = len(binary_message)
                if total_bits > len(audio_data):
                    raise Exception("Audio file too small to hide the message.")
                audio_data_uint16 = audio_data.view(np.uint16)
                if password:
                    seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % (2**32)
                else:
                    seed = len(message)
                rng = np.random.default_rng(seed)
                indices = rng.permutation(len(audio_data_uint16))[:total_bits]
                bits = np.fromiter((int(b) for b in binary_message), dtype=np.uint16)
                audio_data_uint16[indices] = (audio_data_uint16[indices] & 0xFFFE) | bits
                audio_data = audio_data_uint16.view(np.int16)
                with wave.open(output_path, 'wb') as output_wav:
                    output_wav.setparams(params)
                    output_wav.writeframes(audio_data.tobytes())
                return True
        except Exception as e:
            raise Exception(f"Error hiding message with LSB audio: {str(e)}")

    def extract_message_lsb_audio(self, stego_audio_path, password=None, message_length=None):
        """Extract message from audio using LSB method with pseudo-random placement (optimized with NumPy)."""
        import numpy as np
        import hashlib
        try:
            with wave.open(stego_audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                if params.sampwidth != 2 or params.nchannels != 1:
                    raise Exception("Only 16-bit mono WAV files are supported for LSB audio.")
                frames = wav_file.readframes(params.nframes)
                audio_data = np.frombuffer(frames, dtype=np.int16)
                if message_length is None:
                    max_bits = len(audio_data)
                else:
                    max_bits = message_length * 8 + len(self.stop_sequence)
                if password:
                    seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16) % (2**32)
                else:
                    seed = message_length if message_length is not None else len(audio_data)
                rng = np.random.default_rng(seed)
                indices = rng.permutation(len(audio_data))[:max_bits]
                bits = audio_data[indices] & 1
                binary_message = ''.join(bits.astype(str))
                stop_idx = binary_message.find(self.stop_sequence)
                if stop_idx != -1:
                    binary_message = binary_message[:stop_idx]
                return self.binary_to_text(binary_message)
        except Exception as e:
            raise Exception(f"Error extracting message with LSB audio: {str(e)}")

    def calculate_capacity(self, audio_path, method='lsb'):
        """Calculate maximum message capacity for audio (LSB only)."""
        return self.calculate_capacity_lsb_audio(audio_path)

    def hide_message_in_audio(self, audio_path, message, output_path, method='lsb', password=None):
        """Hide message in audio using LSB method only."""
        return self.hide_message_lsb_audio(audio_path, message, output_path, password=password)

    def extract_message_from_audio(self, stego_audio_path, method='lsb', password=None):
        """Extract message from audio using LSB method only."""
        return self.extract_message_lsb_audio(stego_audio_path, password=password)