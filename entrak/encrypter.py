from Crypto.Cipher import AES
import base64
import os


class EntrakEncrypter():

    # the block size for the cipher object; must be 16, 24, or 32 for AES
    DEFAULT_BLOCK_SIZE = 16

    # the character used for padding--with a block cipher such as AES, the value
    # you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
    # used to ensure that your value is always a multiple of BLOCK_SIZE
    DEFAULT_PADDING = '$'

    def __init__(self, secret, block_size=DEFAULT_BLOCK_SIZE, padding=DEFAULT_PADDING):
        # create a cipher object using the random secret
        self.cipher = AES.new(secret)
        self.block_size = block_size
        self.padding = padding[0:1]

    def right_pad(self, input_string):
        return input_string + (self.block_size - len(input_string) % self.block_size) * self.padding

    def encode(self, input_string):
        return base64.urlsafe_b64encode(self.cipher.encrypt(self.right_pad(input_string)))

    def decode(self, encrypted_string):
        return self.cipher.decrypt(base64.urlsafe_b64decode(encrypted_string)).rstrip(self.padding)