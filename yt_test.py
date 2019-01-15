import json
from youtube_videos import youtube_search

yt = youtube_search("omegalul")
print (yt)
yt_result = yt[1]

for video in yt_result:
    print (video['snippet']['title'])