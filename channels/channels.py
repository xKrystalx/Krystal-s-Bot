def initialize_channels(cursor):
    values = [('text',), ('voice',)]
    query = """INSERT INTO channel_types ('type') VALUES (?)"""
    cursor.executemany(query, values)
    print("Channel types initialized.")