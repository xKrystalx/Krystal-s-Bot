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
