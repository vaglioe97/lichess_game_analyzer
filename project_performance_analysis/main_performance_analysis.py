import requests
import pandas as pd 


#Helper Functions

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
        if not game.strip(): continue

        white_player = get_tag_value(game, "White")
        result_raw = get_tag_value(game, "Result")
        opening = get_tag_value(game, "Opening")

        my_color = "white" if white_player == username else "black" #COLOR

        if result_raw == "1/2-1/2":                                 #RESULTS
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


#API Functions


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
    
    


#Database Functions

import sqlite3 
def create_database():
    
    conn = sqlite3.connect("lichess_games.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opening TEXT,
        color TEXT,
        outcome TEXT
        )""")

    conn.commit()
    return conn

def save_games_to_db(conn, games_list):
    cursor = conn.cursor()

    for game in games_list:
        opening = game['opening']
        color = game['color']
        outcome = game['outcome']
        
        cursor.execute("""
            INSERT INTO games (opening, color, outcome)
            VALUES (?,?,?)
        """, (opening, color, outcome))
    
    conn.commit()
    print(f"Succesfully saved {len(games_list)} games to the database.")


def analyze_white_openings(conn):
    query = "SELECT opening, outcome FROM games WHERE color == 'white'"
    df = pd.read_sql(query,conn)

    if df.empty:
        print("No matches found playing as white.")
        return None
    summary = df.groupby('opening')['outcome'].value_counts().unstack().fillna(0)
    summary['total_games'] = summary.sum(axis=1)

    if 'win' in summary.columns:
        summary['win_rate %'] = (summary['win'] / summary['total_games'] *100).round(2)

    print("\n--- PERFORMANCE WITH WHITE PIECES ---")
    print(summary.sort_values(by='total_games', ascending=False).head(10))

    return summary


import matplotlib.pyplot as plt
def plot_win_rate(summary_df):
    top_performers = summary_df[summary_df['total_games'] > 2].sort_values(by='win_rate %', ascending=False)

    if top_performers.empty:
        print("\n[!] Not enough data for a consistent graph.")
        return

    top_performers['win_rate %'].plot(kind='bar', color='skyblue', figsize=(10, 6))

    plt.title('Win Rate by Opening (White Pieces)', fontsize=14)
    plt.xlabel('Opening Name', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.xticks(rotation=45, ha='right') 
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()



#Main Execution

if __name__ =="__main__":
    username = input("Introduce your lichess username: ").strip()
    raw_data = get_lichess_data(username, limit=100)

    if raw_data:
        my_games_list = parse_pgn_data(raw_data, username)

        db_conn = create_database()
        save_games_to_db(db_conn, my_games_list)

        stats_summary = analyze_white_openings(db_conn)
        if stats_summary is not None:
            plot_win_rate(stats_summary)

        db_conn.close()
        print("\nAll games have been saved successfully.")

    else:
        print("No data to process. Check your username or your connection")




