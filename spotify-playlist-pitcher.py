import os
import urllib.request # for making http requests
import urllib.parse # for encoding
import urllib.error # for handling errors
import base64 # for encoding
import json

# credentials
CLIENT_ID = '94c7b98fe83b4398a60014ae6535ff78'
CLIENT_SECRET = '0051fd2c66274720a68f826e9bdbc67b'
credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"

# get the access token
encoded_credentials = base64.b64encode(credentials.encode()).decode()
token_url = 'https://accounts.spotify.com/api/token'
payload = urllib.parse.urlencode({'grant_type': 'client_credentials'}) # "URL-encoded"
print(payload)