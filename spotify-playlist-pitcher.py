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
"""
1) turn credentials (the string) into bytes
2) encode the bytes in base64 format (groups of 6 bits, instead of 8, that represent a character)
3) decode the base64 string into a string
"""
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# get the access token
token_url = 'https://accounts.spotify.com/api/token'
payload = urllib.parse.urlencode({'grant_type': 'client_credentials'}) # this is called "URL-encoded"
data = payload.encode('utf-8')

headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/x-www-form-urlencoded'
}
request = urllib.request.Request(token_url, data=data, headers=headers, method='POST')

with urllib.request.urlopen(request) as response:
    result = response.read()
    token_data = json.loads(result.decode('utf-8')) # load the result into a JSON object
    access_token = token_data['access_token']

print(access_token)

# GET Playlist
playlist_id = '0hirpPpHlxxCmI4m3N8DpE'
playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'

playlist_headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

playlist_request = urllib.request.Request(playlist_url, headers=playlist_headers)

try:
    with urllib.request.urlopen(playlist_request) as response:
        result = response.read()
        playlist_data = json.loads(result.decode('utf-8'))

    print(playlist_data)

except urllib.error.HTTPError as e:
    print(f"Error: {e}")