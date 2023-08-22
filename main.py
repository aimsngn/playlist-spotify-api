import base64
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

app = Flask(__name__)
app.secret_key = "oijdwaoidjwaiojdai"
app.config['SESSION_COOKIE_NAME'] = 'COOKIE'

@app.route('/') 
def start_login():
    scope = "playlist-modify-public playlist-modify-private"
    state = generate_random_string(16)
    auth_url = ('https://accounts.spotify.com/authorize?'f'response_type=code&client_id={client_id}&'f'scope={scope}&redirect_uri={redirct_uri}&'f'state={state}')
    
    return redirect(auth_url)

@app.route('/redirected') #returns here
def handle_redirect():
    return "redirected"


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))
    
app.run()

