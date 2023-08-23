import base64
import requests
from requests import post, get, post
import json
from flask import Flask, request, url_for, session, redirect #will be used for redirect_uri; esssentially where our "app" is hosted
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import string
import random

# These are the client ids of the app for the Spotify API
client_id = "0344808376044123b52d771e92858c83"
client_secret = "c358e0a6e90d480cacbc745fddc15cf7"
redirct_uri = "http://127.0.0.1:5000/redirected"
TOKEN_INFO = "token_info"
REFRESH_INFO = "refresh_token_info"

app = Flask(__name__)
app.secret_key = "oijdwaoidjwaiojdai"
app.config['SESSION_COOKIE_NAME'] = 'COOKIE'

@app.route('/') 
def start_login():
    scope = "playlist-modify-public playlist-modify-private"
    state = generate_random_string(16)
    auth_url = ('https://accounts.spotify.com/authorize?'f'response_type=code&client_id={client_id}&'f'scope={scope}&redirect_uri={redirct_uri}&'f'state={state}')
    
    return redirect(auth_url)


# swap the authorization code for the access token (since the user authorized us (gave us code)), we gon swap it for access token
# access token will be used to create playlists and shit

#Response
#If the user accepts your request, then the user is redirected back to the application using the redirect_uri passed on the authorized request described above.
#The callback contains two query parameters:
#Query Parameter   |  	 Value
#code	|    An authorization code that can be exchanged for an Access Token.
#state	|    The value of the state parameter supplied in the request.

@app.route('/redirected') #returns here
def handle_redirect():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    auth_code = request.args.get('code')
    state = request.args.get('state')
    
    if state is None:
        return 'auth_code request failed'
    
    else:
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirct_uri
        }
        header = {
            "Authorization" : "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, headers=header,data=data)
        
        if response.status_code == 200:
            json_result = json.loads(response.content)
            token = json_result["access_token"]
            refresh_token = json_result["refresh_token"]
            session[TOKEN_INFO] = token
            session[REFRESH_INFO] = refresh_token
            return redirect(url_for('getTracks', _external=True))
        
    return "token retrieve fails"

@app.route('/getTracks')
def getTracks():
    token = get_token() #checks if expired or nah
    return "token retrieved" + token

def get_token():
    token = session.get(TOKEN_INFO, None)
    if token:
        return token
    else:
        refreshed_token = refresh_token()
        if refreshed_token:
            return refreshed_token
    return None
        #get token information for artist search and playlist creation
        #create a refresh token
        
def refresh_token():
    refresh_token = session.get(REFRESH_INFO, None)
    
    if refresh_token:
        auth_string = client_id + ":" + client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        url = "https://accounts.spotify.com/api/token"
        
        data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        header = {
            "Authorization" : "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, headers=header, data=data)
        
        if response.status_code == 200:
            json_result = json.loads(response.content)
            new_access_token = json_result["access_token"]
            session[TOKEN_INFO] = new_access_token
            return new_access_token
        else:
            return None
    return None
        
def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))
    
app.run()

