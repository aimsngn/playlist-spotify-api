import base64
from requests import post, get
import json

client_id = "0344808376044123b52d771e92858c83"
client_secret = "c358e0a6e90d480cacbc745fddc15cf7"

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = 'https://accounts.spotify.com/api/token' #endpoint
    headers = {
        "Authorization": "Basic " +auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url,headers=headers,data=data )
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def get_artist_followers(token):
    artist_id = "29zSTMejPhY0m7kwNQ9SPI"
    url = "https://api.spotify.com/v1/artists/{}".format(artist_id)
    data = {"followers": "total"}
    response = get(url, get_auth_header(token), data=data)

    if response.status_code == 200:
        followers_result = json.loads(followers_result.content)
        followers = followers_result["artist"]["followers"]["total"]
    else:
        print(response.status_code)
        return "eror"
    
    return str(followers)

def search_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    header = get_auth_header(token)
    query = f"q={artist_name}&type=artist&limit=1"
    query_url = url + "?" + query
    
    result = get(query_url, headers=header)
    json_result = json.loads(result.content)["artists"]["items"]
    
    print(json_result[0]["followers"]["total"])

token = get_token()
#print(get_artist_followers(token))
search_artist(token, "Lola Amour")

