from dotenv import load_dotenv
import os
import base64
import requests
from requests import post, get
import json
from flask import Flask, render_template, request
from tkinter import filedialog


load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def cut_playlist_id(url):
    if "spotify.com/playlist/" in url:
        playlist_id = url.split("spotify.com/playlist/")[1].split("?")[0]
        return playlist_id
    else:
        return None


def get_playlist_tracks(token, playlist_id, offset):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset={offset}&limit=100"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result


def download_image(song_name, artist_name, url, directory, downloaded_images_url):
    # if not os.path.exists("directory"):
    #     os.makedirs("directory")

    # specify the path to the file, which includes the folder name
    invalid_chars = r'<>:"/\|?*'
    filename = song_name + " - " + artist_name
    for c in invalid_chars:
        filename = filename.replace(c, '')
    path = os.path.join(directory, filename + ".jpg")

    if url in downloaded_images_url:
        print(f"{filename} image already downloaded, skipping...")
        return
    else:
        downloaded_images_url.add(url)

    response = get(url)

    with open(path, "wb") as f:
        f.write(response.content)
    


def download_playlist_images(token, playlist_id):
    downloaded_images_url = set()
    downloaded_images_url.clear()

    offset = 0
    limit = 100  

    # prompt the user to select a directory
    directory = filedialog.askdirectory()

    total = float("inf")
    while offset < total:
        playlist_tracks = get_playlist_tracks(token, playlist_id, offset)
        total = playlist_tracks['total']
        for i in range(len(playlist_tracks['items'])):
            song_name = playlist_tracks['items'][i]['track']['name']
            artist_name = playlist_tracks['items'][i]['track']['artists'][0]['name']
            url = playlist_tracks['items'][i]['track']['album']['images'][0]['url']
            download_image(song_name, artist_name, url, directory, downloaded_images_url)
            
        offset += limit

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        playlist_id = cut_playlist_id(url)
        token = get_token()
        if token:
            print(f"Got Access token")
        else:
            print("Token does not exist.")
        download_playlist_images(token, playlist_id)
        return "Playlist images downloaded successfully!"
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=False)
