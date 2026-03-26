import requests
import pandas as pd
import io 



def get_tag_value(game_text, tag_name):
    for line in game_text.split("\n"):
        if line.startswith(f"[{tag_name} "):
            parts = line.split('"')
            return parts[1]
    return "Unknown"

def parse_pgn_data(pgn_text, username):
    games = pgn_text.strip().split("\n\n\n")
    processed_data = []
    for game in games:
        if not game.strip():
            continue
        white_player = get_tag_value(game, "White")
        black_player = get_tag_value(game, "Black")
        result_raw = get_tag_value(game, "Result")
        opening = get_tag_value(game, "Opening")

        if white_player == username:
            my_color = "white"
        else:
            my_color ="black"
        if result_raw == "1/2-1/2":
            outcome = "draw"
        elif (my_color =="white" and result_raw =="1-0") or \
             (my_color =="black" and result_raw =="0-1"):
            outcome ="win"
        else:
            outcome ="loss"

        game_dict = {
            "opening": opening,
            "color": my_color,
            "outcome": outcome
        }
        processed_data.append(game_dict)
    return processed_data 

def get_lichess_data(username, limit=50):
    url = f"https://lichess.org/api/games/user/{username}?max={limit}&opening=true"
    headers = {"Accept": "application/x-chess-pgn"}
    try:
        response  =requests.get(url, headers=headers)
        if response.status_code ==200:
            return response.text
        elif response.status_code ==404:
            print("Error: User not found.")
            return None
        else:
            print(f"Error: Lichess returned status code {response.status_code}")
            return None
        
    except Exception as e:
        print(f"Connection error:{e}")
        return None
    
    
username = input("Introduce your lichess username: ").strip()
raw_data = get_lichess_data(username)

if raw_data:
    my_games_list = parse_pgn_data(raw_data, username)
    print(f"\nSuccessfully processed {my_games_list} games")

    for g in my_games_list[:5]:
        print(f"Color: {g['color']} | Result: {g['outcome']} | Opening: {g['opening']}")

else:
    print("No data to process")

import sqlite3 