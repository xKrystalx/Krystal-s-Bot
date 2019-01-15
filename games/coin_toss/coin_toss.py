def initialize_coin_toss():
    global cursor
    name = 'Coin Toss'
    results = ['tails', 'heads']
    points = 20
    db_cursor.execute("""INSERT INTO games ('name') VALUES (?)""", name)
    game_id = db_cursor.execute("SELECT id FROM games WHERE name = ?", name)
    values = [(results[0], points, game_id), (results[1], points, game_id)]
    db_cursor.executemany("""INSERT INTO game_results ('result', 'points', 'games_id') VALUES (?,?,?)""", values)
    print(name + " initialized.")
    return
