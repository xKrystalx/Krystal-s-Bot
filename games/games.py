def initialize_games(cursor):
    initialize_coin_toss(cursor)
    initialize_youtube_game(cursor)
    print("Games initialized.")
    return

def initialize_coin_toss(cursor):
    name = "Coin Toss"
    points = 20
    cursor.execute("""INSERT INTO games ('name') VALUES (?)""", (name,))
    cursor.execute("SELECT id FROM games WHERE name = ?", (name,))
    game_id = cursor.fetchone()
    values = (points, *game_id)
    cursor.execute("""INSERT INTO game_results ('points', 'games_id') VALUES (?,?)""", values)
    print(name + " initialized.")
    return

def initialize_youtube_game(cursor):
    name = "You Tube"
    points = -10
    cursor.execute("""INSERT INTO games ('name') VALUES (?)""", (name,))
    cursor.execute("SELECT id FROM games WHERE name = ?", (name,))
    game_id = cursor.fetchone()
    values = (points, *game_id)
    cursor.execute("""INSERT INTO game_results ('points', 'games_id') VALUES (?,?)""", values)
    print(name + " initialized.")