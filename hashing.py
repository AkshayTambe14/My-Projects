import os

def SHA256(message):
    #Constants comes from the cube roots of the first sixty-four prime numbers
    K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]

    padded_message = pad(message)
    blocks = split_to_blocks(padded_message, 512)

    #Initial hash values
    H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]

    for block in blocks:
        W = create_message_schedule(block)
        a, b, c, d, e, f, g, h = H

        for i in range(64):
            s1 = ROTR(e, 6) ^ ROTR(e, 11) ^ ROTR(e, 25)
            Ch = (e & f) ^ ((~e) & g)
            temp1 = (h + s1 + Ch + K[i] + W[i]) & 0xFFFFFFFF

            s0 = ROTR(a, 2) ^ ROTR(a, 13) ^ ROTR(a, 22)
            Maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + Maj) & 0xFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        H = [
            (H[0] + a) & 0xFFFFFFFF,
            (H[1] + b) & 0xFFFFFFFF,
            (H[2] + c) & 0xFFFFFFFF,
            (H[3] + d) & 0xFFFFFFFF,
            (H[4] + e) & 0xFFFFFFFF,
            (H[5] + f) & 0xFFFFFFFF,
            (H[6] + g) & 0xFFFFFFFF,
            (H[7] + h) & 0xFFFFFFFF]

    return concatenate(H)

def hash_password(message, salt=None):
    if salt is None:
        salt = generate_salt()
    return SHA256(salt+message), salt

def generate_salt():
    return os.urandom(16).hex()

def verify_password(stored, entered, salt):
    return SHA256(salt + entered) == stored

def pad(message):
    if isinstance(message, str):
        message = message.encode('utf-8')
        #Convert to binary

    message_len = len(message) * 8
    message += b'\x80'

    while ((len(message)*8) % 512) != 448:
        message += b'\x00'
    #Pad with a 1, then 0s until there is 64 bits less than 512 (or a multiple)
    
    message += message_len.to_bytes(8, byteorder='big')

    return message

def split_to_blocks(plaintext, block_size):
    #Split message into 512 bit blocks

    block_len = block_size // 8

    return [plaintext[i:i+block_len] for i in range(0, len(plaintext), block_len)]

def create_message_schedule(block):

    W = [int.from_bytes(block[i:i+4], byteorder='big') for i in range(0, 64, 4)]
    #Split message into 16, 32 bit words

    for i in range(16, 64):
        s0 = ROTR(W[i-15], 7) ^ ROTR(W[i-15], 18) ^ (W[i-15] >> 3)
        s1 = ROTR(W[i-2], 17) ^ ROTR(W[i-2], 19) ^ (W[i-2] >> 10)
        W.append((W[i-16] + s0 + W[i-7] + s1) & 0xFFFFFFFF)

    return W

def concatenate(H):
    #Coverting the final list into a hex string

    return ''.join(f'{h:08x}' for h in H)

def ROTR(inp, number_of_rotates):
    #Right rotation, bits wrap

    return ((inp >> number_of_rotates) | (inp << (32 - number_of_rotates))) & 0xFFFFFFFF
