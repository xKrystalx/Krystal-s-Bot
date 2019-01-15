def initialize_games(cursor):
    initialize_coin_toss(cursor)
    print("Games initialized.")
    return

def initialize_coin_toss(cursor):
    name = "Coin Toss"
    results = ["Tails", "Heads"]
    points = 20
    cursor.execute("""INSERT INTO games ('name') VALUES (?)""", (name,))
    cursor.execute("SELECT id FROM games WHERE name = ?", (name,))
    game_id = cursor.fetchone()
    values = [(results[0], points, *game_id), (results[1], points, *game_id)]
    cursor.executemany("""INSERT INTO game_results ('result', 'points', 'games_id') VALUES (?,?,?)""", values)
    print(name + " initialized.")
    return
