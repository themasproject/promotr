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

# START STREAMING
# put API query parameters into a dict so I can URL encode them
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
query_parameters = {
    "q":"@",
    "type": "playlist",
    "limit": 50
}
base_url = "https://api.spotify.com/v1/search"
query_string = urllib.parse.urlencode(query_parameters)
full_url = f"{base_url}?{query_string}"

# create a Request object which Spotify wants
req = urllib.request.Request(full_url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        result = response.read() # here it's just binary
        result_dict = json.loads(result.decode('utf-8')) # decoding turns it into json, loads turns it into a dict

    # print(result_dict)


except urllib.error.HTTPError as e:
    print(f"Error: {e}")

# print(result_dict['playlists']['items'][0].keys())
print(result_dict['playlists']['items'][0])

# only save those with over 100,000 saves
matches = []

for i in result_dict['playlists']['items']:
    # here, I need to create a function for the api call so I can stop repeating so much code. then GET playlist
    # need to filter for values that represent LEGTITIMATE playlists. 
    # time on playlist, whether followers of the playulist are bgeing banned or not, etc etc