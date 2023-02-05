import discord
import json
from youtube_videos import youtube_search
import youtube_dl
from discord.ext import commands
import sys
import sqlite3
import os
import os.path
import random

import games.games as db_games
import channels.channels as db_channels
from datetime import datetime, timedelta
#import commands.music.music

description = 'A work in progress Bot written in Python by Krystal'
prefix = '!'
shutdown_emoji = ':diamond_shape_with_a_dot_inside:'
database_path = 'database/discord.db'
database_init_path = 'database/init.txt'


cursor = None
conn = None

bot = commands.Bot(pm_help = True, description = description, command_prefix = prefix)
player = None

@bot.event
async def on_ready():
    print('Connected')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    load_database()
#######################################################################################
#           DATABASE LOADING STUFF
#######################################################################################
def load_database():
    global conn
    global cursor
    print("Loading the database...")
    if not os.path.isfile(database_path):
        initialize_database()
    else:
        try:
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
        except sqlite3.Error as e:
            print("Database error: ", e.args[0])
            return
        print('Database loaded...')
    
def initialize_database():
    global conn
    global cursor
    if conn is not None:
        print('Closing existing connection.')
        conn.close()
        cursor = None
    if os.path.isfile(database_path):
        os.remove(database_path)
    if not os.path.isfile(database_init_path):
        print('No database initialization file!')
        return False
    query = open(database_init_path, 'r').read()
    if sqlite3.complete_statement(query):
        try:
            conn = sqlite3.connect(database_path)
        except sqlite3.Error as e:
            print('Database error: ', str(e))
            return
        cursor = conn.cursor()
        try:
            cursor.executescript(query)
        except Exception as e:
            print('Database error: ', str(e))
            return
        print('Loading initial data...')
        cursor.execute("""PRAGMA foreign_keys = ON""")
        db_channels.initialize_channels(cursor)
        db_games.initialize_games(cursor)
        register_users()
        register_channels()
        register_roles()
        conn.commit()
        print('Database initialized.')
    return

def register_users():
    global cursor
    for user in bot.get_all_members():
        cursor.execute("""INSERT OR IGNORE INTO clients ('userid', 'username', 'join_date') VALUES (?,?,?)""", (user.id, user.name, user.joined_at))

    conn.commit()
    return

def register_channels():
    global cursor
    for channel in bot.get_all_channels():
        chnl_type = None
        if channel.type is discord.ChannelType.voice:
            chnl_type = 'voice'
        if channel.type is discord.ChannelType.text:
            chnl_type = 'text'
        if chnl_type is not None:
            cursor.execute("""INSERT INTO channels ('id', 'name', 'type') VALUES (?,?,?)""", (channel.id, channel.name, chnl_type))
    return

def register_roles():
    global cursor
    for user in bot.get_all_members():
        for roles in user.roles:
            cursor.execute("""INSERT OR IGNORE INTO roles ('name', 'clients_userid') VALUES (?,?)""",(roles.name, user.id))
    return

async def sql_execute(query, ctx):
    global cursor
    try:
        cursor.execute(query)
    except Exception as e:
            print('Database error: ', str(e))
            await bot.send_message(ctx.message.channel, 'Database error: {}'.format(str(e)))
            return
    names = [description[0] for description in cursor.description]
    print(names)
    result = cursor.fetchall()
    msg = 'Format: {\n'
    for column in names:
        msg += '>>> ' + str(column) + ' <<<\n'
    msg += '}'
    for rows in result:
        msg += '\n{\n'
        for col in rows:
            msg += '>>> ' + str(col) + ' <<<\n'
        msg += '}'
    f = open("query.txt", "w+", encoding = 'utf-8')
    f.write(msg)
    f.close
    f = open("query.txt", "rb")
    await bot.send_file(ctx.message.author, f)
    f.close


@bot.command(pass_context = True)
async def initialize_db(ctx):
    initialize_database()
    await bot.send_message(ctx.message.channel, 'Reinitialized the database. :slight_smile:')
    return

#####################################################################
#               DATABASE RELATED COMMANDS
#####################################################################

@bot.command(pass_context = True)
async def query(ctx, qr:str):
    await sql_execute(qr, ctx)

@bot.command(pass_context = True)
async def toss(ctx, guess:str = ''):
    global cursor
    if guess is '':
        await bot.send_message(ctx.message.channel, "```Usage: tails / t or heads / h```")
        return
    cursor.execute("SELECT id FROM games WHERE name LIKE ('coin toss')")
    game_id = cursor.fetchone()
    '''
    cursor.execute("SELECT * FROM game_results WHERE games_id = ?", game_id)
    results = cursor.fetchall()
    roll = random.choice(results)
    if guess.lower() in roll[0].lower():
        points = roll[1]
    '''
    cursor.execute("SELECT points FROM game_results WHERE games_id = ?", game_id)
    result_points = cursor.fetchone()
    results = ['Tails', 'Heads']
    roll = random.choice(results)
    if guess.lower() in roll.lower():
        points = "{}".format(*result_points)
    else: points = 0
    await bot.send_message(ctx.message.channel, roll + "\n" + str(points) + " points given!")
    cursor.execute("""INSERT INTO game_history ('clients_userid', 'result', 'game_id', 'points', 'game_date') VALUES (?,?,?,?, (strftime('%Y-%m-%d %H:%M:%f', 'now')))""", (ctx.message.author.id, roll, *game_id, points))
    conn.commit()
    return
    
@bot.command(pass_context = True)
async def db_dump(ctx, name:str = ''):
    global cursor
    msg = ''
    if name is '':
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
        for rows in cursor.fetchall():
            msg += str(*rows)
            msg += '\n'
        await bot.send_message(ctx.message.channel, '```\nList of available tables:\n'+msg+'\n```')
    else:
        query = "SELECT * FROM {}".format(name)
        cursor.execute(query)
        names = [description[0] for description in cursor.description]
        print(names)
        result = cursor.fetchall()
        msg = 'Format: {\n'
        for column in names:
            msg += '>>> ' + str(column) + ' <<<\n'
        msg += '}'
        for rows in result:
            msg += '\n{\n'
            for col in rows:
                msg += '>>> ' + str(col) + ' <<<\n'
            msg += '}'
        f = open("dump.txt", "w+", encoding = 'utf-8')
        f.write(msg)
        f.close
        f = open("dump.txt", "rb")
        await bot.send_file(ctx.message.author, f)
        f.close

@bot.command(pass_context = True)
async def mute(ctx):
    global cursor
    cursor.execute("""SELECT name FROM roles WHERE name = 'Admun' AND clients_userid = ?""", (ctx.message.author.id,))
    isAdmin = cursor.fetchone()
    if isAdmin is None:
        await bot.send_message(ctx.message.channel,":x: You don't have the required role.")
        return
    for mentions in ctx.message.mentions:
        if mentions.id is not bot.user.id:
            await mute_user(mentions.id)
            await bot.send_message(ctx.message.channel,":x: User " + mentions.mention + " has been muted :x:")

async def mute_user(id):
    global cursor
    cursor.execute("""INSERT INTO roles ('name', 'clients_userid') VALUES ('Muted', ?)""", (id,))
    conn.commit()


@bot.command(pass_context = True)
async def unmute(ctx):
    global cursor
    cursor.execute("""SELECT name FROM roles WHERE name = 'Admun'AND clients_userid = ?""", (ctx.message.author.id,))
    isAdmin = cursor.fetchone()
    if isAdmin is None:
        await bot.send_message(":x: You don't have the required role.")
        return
    for mentions in ctx.message.mentions:
        cursor.execute("""DELETE FROM roles WHERE name = 'Muted' AND clients_userid = ?""", (mentions.id,))
        await bot.send_message(ctx.message.channel,":white_check_mark: User " + mentions.mention + " has been unmuted :white_check_mark:")
    conn.commit()

@bot.command(pass_context = True)
async def points(ctx):
    global cursor
    for mention in ctx.message.mentions:
        cursor.execute("""SELECT SUM(points) FROM game_history WHERE clients_userid = ?""", (mention.id,))
        points = cursor.fetchone()
        if points[0] is None:
            points = 0
        else:
            points = "{}".format(*points)
        await bot.send_message(ctx.message.channel, mention.mention + " currently has: " + str(points) + " points :ok_hand:")

@bot.command(pass_context = True)
async def banword(ctx, word):
    global cursor
    await bot.send_message(ctx.message.channel,":white_check_mark: Word " + word + " has been banned")
    cursor.execute("""INSERT INTO banned_words ('message') VALUES(?)""", (word,))
    conn.commit()

@bot.command(pass_context = True)
async def mutedusers(ctx):
    global cursor
    cursor.execute("""SELECT user.username, role.clients_userid FROM clients user INNER JOIN roles role ON user.userid = role.clients_userid WHERE role.name = 'Muted'""")
    results = cursor.fetchall()
    print(results)
    if not results:
        await bot.send_message(ctx.message.channel, "No muted users.")
        return
    msg = await bot.send_message(ctx.message.channel,"Loading...")
    emoji = discord.utils.get(bot.get_all_emojis(), name='monkaW')

    for result in results:
        embed = discord.Embed(title="Muted Users", description="", color=0x00ff00)
        embed.add_field(name = "Name:", value = "{}".format(result[0]), inline = True)
        embed.add_field(name = "ID:", value = "{}".format(result[1]), inline = True)
        await bot.edit_message(msg, embed=embed)
        await bot.add_reaction(msg, emoji)
        reacted = await bot.wait_for_reaction(emoji = emoji, timeout = 30, message = msg, check=lambda reaction, user: user != bot.user)
        if reacted is None:
            await bot.send_message(ctx.message.channel, "Request Timeout.")
            return
        await bot.remove_reaction(msg, emoji, reacted.user)

@bot.command(pass_context = True)
async def logs(ctx):
    mention = None
    ban_flag = None
    global cursor
    while mention is None:
        await bot.send_message(ctx.message.channel, "Mention a user you want logs of (10s timeout).")
        res = await bot.wait_for_message(timeout = 10, author = ctx.message.author, channel = ctx.message.channel)
        if res:
            mention = res.mentions[0]
    if ban_flag is None:
        await bot.send_message(ctx.message.channel, "Ban flag? (say anything or wait 5s).")
        res = await bot.wait_for_message(timeout = 5, author = ctx.message.author, channel = ctx.message.channel)
        if res:
            ban_flag = 1
    if ban_flag:
        cursor.execute("""SELECT user.username, msg.clients_userid, msg.message, (datetime(msg.msg_date)) FROM clients user INNER JOIN chat_history msg ON user.userid = msg.clients_userid WHERE msg.clients_userid = ? AND ban_flag = 1 LIMIT 100""", (mention.id,))
    else:
        cursor.execute("""SELECT user.username, msg.clients_userid, msg.message, (datetime(msg.msg_date)) FROM clients user INNER JOIN chat_history msg ON user.userid = msg.clients_userid WHERE msg.clients_userid = ? LIMIT 100""", (mention.id,))
    results = reversed(cursor.fetchall())
    if not results:
        await bot.send_message(ctx.message.channel, "No chat history for that user.")
        return
    msg = await bot.send_message(ctx.message.channel,"Loading...")
    emoji = discord.utils.get(bot.get_all_emojis(), name='monkaW')

    for result in results:
        embed = discord.Embed(title="Chat History", description="", color=0x00ff00)
        embed.add_field(name = "Name:", value = "{}".format(result[0]), inline = True)
        embed.add_field(name = "ID:", value = "{}".format(result[1]), inline = True)
        embed.add_field(name = "Date:", value = "{}".format(result[3]), inline = True)
        embed.add_field(name = "Message:", value = "{}".format(result[2]), inline = False)
        await bot.edit_message(msg, embed=embed)
        await bot.add_reaction(msg, emoji)
        reacted = await bot.wait_for_reaction(emoji = emoji, timeout = 30, message = msg, check=lambda reaction, user: user != bot.user)
        if reacted is None:
            await bot.send_message(ctx.message.channel, "Request Timeout.")
            return
        await bot.remove_reaction(msg, emoji, reacted.user)


@bot.command(pass_context = True)
async def ythistory(ctx):
    mention = None
    global cursor
    while mention is None:
        await bot.send_message(ctx.message.channel, "Mention a user you want logs of (10s timeout).")
        res = await bot.wait_for_message(timeout = 10, author = ctx.message.author, channel = ctx.message.channel)
        if res:
            mention = res.mentions[0]
    cursor.execute("""SELECT user.username, yt.clients_userid, yt.url, (datetime(yt.yt_date)) FROM clients user INNER JOIN youtube_history yt ON user.userid = yt.clients_userid WHERE yt.clients_userid = ? LIMIT 100""", (mention.id,))
    results = reversed(cursor.fetchall())
    if not results:
        await bot.send_message(ctx.message.channel, "No you tube history for that user.")
        return
    msg = await bot.send_message(ctx.message.channel,"Loading...")
    emoji = discord.utils.get(bot.get_all_emojis(), name='monkaW')

    for result in results:
        embed = discord.Embed(title="Youtube History", description="", color=0x00ff00)
        embed.add_field(name = "Name:", value = "{}".format(result[0]), inline = True)
        embed.add_field(name = "ID:", value = "{}".format(result[1]), inline = True)
        embed.add_field(name = "Date:", value = "{}".format(result[3]), inline = True)
        embed.add_field(name = "Url:", value = "{}".format(result[2]), inline = False)
        await bot.edit_message(msg, embed=embed)
        await bot.add_reaction(msg, emoji)
        reacted = await bot.wait_for_reaction(emoji = emoji, timeout = 30, message = msg, check=lambda reaction, user: user != bot.user)
        if reacted is None:
            await bot.send_message(ctx.message.channel, "Request Timeout.")
            return
        await bot.remove_reaction(msg, emoji, reacted.user)

@bot.command(pass_context = True)
async def vctime(ctx):
    mention = None
    global cursor
    while mention is None:
        await bot.send_message(ctx.message.channel, "Mention a user you want voice chat time of (10s timeout).")
        res = await bot.wait_for_message(timeout = 10, author = ctx.message.author, channel = ctx.message.channel)
        if res:
            mention = res.mentions[0]
    cursor.execute("""SELECT user.username, vc.clients_userid, vc.channels_id, vc.connection_time, vc.last_left FROM clients user INNER JOIN voice_chat_time vc ON user.userid = vc.clients_userid WHERE vc.clients_userid = ? LIMIT 10""", (mention.id,))
    results = reversed(cursor.fetchall())
    if not results:
        await bot.send_message(ctx.message.channel, "User has not been in a voice channel.")
        return
    msg = await bot.send_message(ctx.message.channel,"Loading...")
    emoji = discord.utils.get(bot.get_all_emojis(), name='monkaW')

    for result in results:
        cursor.execute("""SELECT name FROM channels WHERE id = ?""",(result[2],))
        channel_name = cursor.fetchone()
        embed = discord.Embed(title="Youtube History", description="", color=0x00ff00)
        embed.add_field(name = "Name:", value = "{}".format(result[0]), inline = True)
        embed.add_field(name = "ID:", value = "{}".format(result[1]), inline = True)
        embed.add_field(name = "Channel:", value = "{}".format(*channel_name), inline = True)
        embed.add_field(name = "Last Seen:", value = "{}".format(result[4]), inline = False)
        
        minutes, seconds = divmod(result[3], 60)
        hours , minutes = divmod(minutes, 60)
        embed.add_field(name = "Time:", value = "{} hours {} minutes {} seconds".format(hours, minutes, seconds), inline = True)
        await bot.edit_message(msg, embed=embed)
        await bot.add_reaction(msg, emoji)
        reacted = await bot.wait_for_reaction(emoji = emoji, timeout = 30, message = msg, check=lambda reaction, user: user != bot.user)
        if reacted is None:
            await bot.send_message(ctx.message.channel, "Request Timeout.")
            return
        await bot.remove_reaction(msg, emoji, reacted.user)

@bot.command(pass_context = True)
async def pointhistory(ctx):
    mention = None
    global cursor
    while mention is None:
        await bot.send_message(ctx.message.channel, "Mention a user you want logs of (10s timeout).")
        res = await bot.wait_for_message(timeout = 10, author = ctx.message.author, channel = ctx.message.channel)
        if res:
            mention = res.mentions[0]
    cursor.execute("""SELECT user.username, pts.clients_userid, pts.points, (datetime(pts.game_date)), pts.game_id FROM clients user INNER JOIN game_history pts ON user.userid = pts.clients_userid WHERE pts.clients_userid = ? LIMIT 100""", (mention.id,))
    results = reversed(cursor.fetchall())
    if not results:
        await bot.send_message(ctx.message.channel, "No you tube history for that user.")
        return
    msg = await bot.send_message(ctx.message.channel,"Loading...")
    emoji = discord.utils.get(bot.get_all_emojis(), name='monkaW')

    for result in results:
        cursor.execute("""SELECT name FROM games WHERE id = ?""",(result[4],))
        game_name = cursor.fetchone()
        print(game_name)
        embed = discord.Embed(title="Point History", description="", color=0x00ff00)
        embed.add_field(name = "Name:", value = "{}".format(result[0]), inline = True)
        embed.add_field(name = "ID:", value = "{}".format(result[1]), inline = True)
        embed.add_field(name = "Date:", value = "{}".format(result[3]), inline = True)
        embed.add_field(name = "Service:", value = "{}".format(*game_name), inline = False)
        embed.add_field(name = "Points:", value = "{}".format(result[2]), inline = True)
        await bot.edit_message(msg, embed=embed)
        await bot.add_reaction(msg, emoji)
        reacted = await bot.wait_for_reaction(emoji = emoji, timeout = 30, message = msg, check=lambda reaction, user: user != bot.user)
        if reacted is None:
            await bot.send_message(ctx.message.channel, "Request Timeout.")
            return
        await bot.remove_reaction(msg, emoji, reacted.user)
###################################################################
#               DATABASE EVENTS
###################################################################

@bot.event
async def on_message(message):
    global cursor
    global conn
    flagged = None
    cursor.execute("""SELECT name FROM roles WHERE clients_userid = ? AND name = 'Muted'""", (message.author.id,))
    isMuted = cursor.fetchone()
    if isMuted is not None:
        print("Delete Muted Message")
        await bot.delete_message(message)
    cursor.execute("""SELECT message FROM banned_words""")
    words = cursor.fetchall()
    for word in words:
        word = "{}".format(*word)
        print(word)
        if word.lower() in message.content.lower():
            print("Banned word found")
            flagged = True
            print("gonna mute")
            await mute_user(message.author.id)
            await bot.send_message(message.channel,":x: User " + message.author.mention + " has been muted :x:")

    await bot.process_commands(message)
    if flagged is None:
        cursor.execute("""INSERT INTO chat_history ('message', 'clients_userid', 'channels_id', 'msg_date') VALUES(?,?,?,?)""", (message.content, message.author.id, message.channel.id, message.timestamp))
    else:
        cursor.execute("""INSERT INTO chat_history ('message', 'clients_userid', 'channels_id', 'msg_date', ban_flag) VALUES(?,?,?,?,1)""", (message.content, message.author.id, message.channel.id, message.timestamp))
    conn.commit()

@bot.event
async def on_message_edit(before, after):
    print(after.timestamp)
    global cursor
    global conn
    cursor.execute("""UPDATE chat_history SET message = ?, date_edited = ? WHERE msg_date = ?""", (after.content, after.edited_timestamp, after.timestamp))
    conn.commit()

@bot.event
async def on_message_delete(message):
    global cursor
    global conn
    cursor.execute("""DELETE FROM chat_history WHERE  msg_date = ? AND clients_userid = ? AND channels_id = ?""", (message.timestamp, message.author.id, message.channel.id))
    conn.commit()


@bot.event
async def on_member_join(member):
    global cursor
    global conn
    print('New member ' + member.id)
    cursor.execute("""INSERT INTO clients ('userid', 'username') VALUES(?,?)""", (member.id, member.name))
    conn.commit()

@bot.event
async def on_member_remove(member):
    global cursor
    global conn

    cursor.execute("""DELETE FROM clients WHERE userid = ?""", ((member.id,)))
    conn.commit()
@bot.event
async def on_member_update(before, after):
    global cursor
    global conn

    cursor.execute("""UPDATE OR IGNORE clients SET username = ? WHERE userid = ?""",(after.name, after.id))

    for roles in after.roles:
        cursor.execute("""INSERT OR IGNORE INTO roles ('name', 'clients_userid') VALUES (?,?)""",(roles.name, after.id))
        for prev_role in before.roles:
            if prev_role not in after.roles:
                cursor.execute("""DELETE FROM roles WHERE name = ? AND clients_userid = ?""",(prev_role.name, before.id))
        
    conn.commit()

@bot.event
async def on_channel_create(channel):
    global cursor
    global conn
    chnl_type = None
    if channel.type is discord.ChannelType.voice:
        chnl_type = 'voice'
    if channel.type is discord.ChannelType.text:
        chnl_type = 'text'
    if chnl_type is not None:
        cursor.execute("""INSERT INTO channels ('id', 'name', 'type') VALUES(?,?,?)""", (channel.id, channel.name, chnl_type))
        conn.commit()

@bot.event
async def on_channel_delete(channel):
    global cursor
    global conn

    cursor.execute("""DELETE FROM channels WHERE id = ?""", ((channel.id,)))

    print('Deleted a channel: ', channel.name, ' from the database')
    conn.commit()

@bot.event
async def on_voice_state_update(before, after):
    global cursor
    global conn

    if before.voice.voice_channel is None:
        print('User ', before.name, ' joined a VC')
        cursor.execute("""SELECT * FROM voice_chat_time WHERE clients_userid = ? AND channels_id = ?""",(before.id, after.voice.voice_channel.id))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("""INSERT INTO voice_chat_time ('last_joined', 'clients_userid', 'channels_id') VALUES ((strftime('%Y-%m-%d %H:%M:%f', 'now')),?,?)""", (before.id, after.voice.voice_channel.id))
        else:
            cursor.execute("""UPDATE voice_chat_time SET last_joined = (strftime('%Y-%m-%d %H:%M:%f', 'now')) WHERE clients_userid = ? AND channels_id = ?""", (before.id, after.voice.voice_channel.id))
    if after.voice.voice_channel is None:
        print('User ', before.name, ' left a VC')
        cursor.execute("""SELECT * FROM voice_chat_time WHERE clients_userid = ? AND channels_id = ?""",(before.id, before.voice.voice_channel.id))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("""INSERT INTO voice_chat_time ('last_left', 'clients_userid', 'channels_id') VALUES ((strftime('%Y-%m-%d %H:%M:%f', 'now')),?,?)""", (before.id, before.voice.voice_channel.id))
        else:
            last_joined = result[1]
            if last_joined is None:
                return
            cursor.execute("SELECT strftime('%s','now')")
            last_left = cursor.fetchone()
            cursor.execute("""SELECT strftime('%s',?)""", (last_joined,))
            last_joined = cursor.fetchone()
            cursor.execute("""SELECT connection_time FROM voice_chat_time WHERE clients_userid = ? AND channels_id = ?""", (before.id, before.voice.voice_channel.id))
            connection_time = cursor.fetchone()
            connection_time = int(str(*connection_time))
            last_left = str(*last_left)
            last_joined = str(*last_joined)
            connection_time += int(last_left) - int(last_joined)
            cursor.execute("""UPDATE voice_chat_time SET last_left = (strftime('%Y-%m-%d %H:%M:%f', 'now')), connection_time = ? WHERE clients_userid = ? AND channels_id = ?""", (connection_time, before.id, before.voice.voice_channel.id))
    conn.commit()


@bot.group(pass_context = True)
async def music(ctx, *, search_keyword:str):
    """Returns suggestions from youtube."""
    #embed = discord.Embed(title = 'Music Search for: "' + search_keyword + '"', type = 'rich', color = 0x18a7f9)

    if 'youtube.com/watch?v=' in search_keyword:
        await play(ctx, search_keyword)
    else:
        yt = youtube_search(search_keyword)
        yt_results = yt[1]
        num = 1
        title = []
        url = []
        buffer_search = '```html\nMusic Search for: <' + search_keyword + '>\n'
        for video in yt_results:
            title.append(video['snippet']['title'])
            url.append('https://www.youtube.com/watch?v=' + video['id']['videoId'])
            buffer_search +='\n<# ' + str(num) + '.="' + title[num-1] + '">'
            num += 1

        buffer_search += '\n<# 0. "Cancel this request.">```'

        await bot.send_message(ctx.message.channel, buffer_search)

        msg = await bot.wait_for_message(author=ctx.message.author)
        if str(msg.content) == "1" or str(msg.content) == "2" or str(msg.content) == "3" or str(msg.content) == "4" or str(msg.content) == "5" :
            index = int(msg.content) - 1
            msg.content = title[index]
            await play(ctx, url[index])
        else:
            await bot.send_message(ctx.message.channel, 'Canceled Request.')
                

@bot.command(pass_context=True)
async def volume(ctx, value:float):
    author = ctx.message.author
    voice_channel = author.voice_channel
    global player

    if not bot.is_voice_connected(ctx.message.server):
        return await bot.send_message(ctx.message.channel, 'Currently not in a voice channel.')

    if player.is_playing():
        player.volume = value
        return await bot.send_message(ctx.message.channel, '***Volume set to:*** [{}]'.format(value))
    else:
        return await bot.send_message(ctx.message.channel, 'Currently not playing.')

async def play(ctx, url:str):
    global cursor
    global conn
    cursor.execute("""SELECT SUM(points) FROM game_history WHERE clients_userid = ?""", (ctx.message.author.id,))
    total_points = cursor.fetchone()
    if total_points[0] is None:
        total_points = 0
    else:
        total_points = "{}".format(*total_points)
    if int(total_points) < 10:
        await bot.send_message(ctx.message.channel, ":slight_frown: You don't have the required amount of points. Current points: "+str(total_points))
        return
    if 'index=' in url:
        url = url.split('index=')[0]

    author = ctx.message.author
    voice_channel = author.voice_channel

    if voice_channel == None:
        await bot.send_message(ctx.message.channel, '{} Please join a voice channel.'.format(author.mention))
        return

    if not bot.is_voice_connected(ctx.message.server):
        voice = await bot.join_voice_channel(voice_channel)

    global player
    player = await voice.create_ytdl_player(url)
    player.start()
    await bot.send_message(ctx.message.channel, '**Playing:** ' + player.title + '  || {}'.format(author.mention))
    cursor.execute("""INSERT INTO youtube_history ('url', 'clients_userid', 'yt_date') VALUES (?,?,?)""", (url, author.id, ctx.message.timestamp))
    cursor.execute("SELECT id FROM games WHERE name LIKE ('you tube')")
    game_id = cursor.fetchone()
    cursor.execute("SELECT points FROM game_results WHERE games_id = ?", game_id)
    result_points = cursor.fetchone()
    result_points = "{}".format(*result_points)
    await bot.send_message(ctx.message.channel, result_points + " deducted from " + author.mention)
    cursor.execute("""INSERT INTO game_history ('clients_userid', 'result', 'game_id', 'points', 'game_date') VALUES (?,?,?,?, (strftime('%Y-%m-%d %H:%M:%f', 'now')))""", (ctx.message.author.id, url, *game_id, result_points))
    conn.commit()


@bot.command(pass_context=True)
async def disconnect(ctx):
    if bot.is_voice_connected(ctx.message.server):
        for voice_channel in bot.voice_clients:
            if(voice_channel.server == ctx.message.server):
                await bot.send_message(ctx.message.channel, 'Disconnected from the voice channel.')
                return await voice_channel.disconnect()
    else:
        await bot.send_message(ctx.message.channel, 'Currently not in a voice channel.')

@bot.command()
async def shutdown():
    """Forces the bot to disconnect and close."""
    await bot.say(shutdown_emoji + ' Shutting down... ' + shutdown_emoji)
    await bot.logout()

bot.run('put your bot token here')
