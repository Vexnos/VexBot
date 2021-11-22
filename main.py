'''

    main.py

    Author: Vexnos
    Date: 2021-08-08

    VexBot Main
    
'''

import discord
import random
import asyncio
import time
from config import *
from music import *

start = time.time()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

queues = {}
loops = {}
loopqueue = {}
playing = {}
paused = {}

async def queue_manager(guild):
  queue = queues[guild.id]
  queued = False
  counter = 0
  vc = guild.voice_client
  while ((len(queue) > 0 or (guild.id in loops and loops[guild.id] == 1))) and counter < 60:
    #play songs
    if paused[guild.id]:
      del playing[guild.id]
      return await vc.disconnect()
    if guild.id not in loops or loops[guild.id] == 0 or not queued:
      location,volume,name,id = queue.pop(0)
      queues[guild.id] = queue
      queued = True
    vc.play(discord.FFmpegPCMAudio(location),after=None)
    vc.source = discord.PCMVolumeTransformer(vc.source)
    vc.source.volume = volume
    if guild.id in playing and guild.id in loopqueue and loopqueue[guild.id] == 1:
      queues[guild.id].append(playing[guild.id])
    playing[guild.id] = [location,volume,name,id]
    while vc.is_playing():
      if len(vc.channel.members) == 1:
        counter += 1
      else: counter = 0
      if counter >= 60:
        vc.pause()
      await asyncio.sleep(0.5)
    queue = queues[guild.id]
  del playing[guild.id]
  await vc.disconnect()

@client.event
async def on_ready():
  global channel_log
  print("Target Acquired")
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))
  stop = time.time()
  startup_time = stop-start
  try:
    channel_log = client.get_channel(833837328430530580)
    await channel_log.send(f"Target Acquired\nStartup took {startup_time:.2f}s\n")
  except discord.errors.Forbidden:
    pass

  print(f"Startup took {startup_time:.2f}s")
  #await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the economy plummet"), status=discord.Status.do_not_disturb)
  #await client.change_presence(activity=discord.Streaming(name="Minecraft", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

@client.event
async def on_message(message):
  if message.author.bot: return #don't consider other bots
  #if message.author == client.user: return

  author = message.author.id
  content = " " + message.content.lower() + " "

  if message.content.startswith(prefix):
    length = len(prefix)
    rest = message.content[length:]
    words = rest.split(" ")
    command = words[0].lower()
    args = words[1:]

    #Kill command
    if command == "begone":
      info = await client.application_info()
      if message.author == info.owner:
        await message.channel.send(random.choice(["Shutting down...", "Goodnight", "Sleep mode activated", "Hibernating..."]))
        for guild in client.guilds:
          voice_client = discord.utils.get(client.voice_clients, guild=guild)
          if voice_client != None:
            await guild.voice_client.disconnect()
        await client.change_presence(status=discord.Status.offline) #await client.change_presence(activity=discord.Game("Among Us"))
        await client.close()
        quit()
      else:
        await message.channel.send(f"Stop shooting!")

    #Play Command
    elif command == "play":
      guild_id = message.guild.id
      voice = message.author.voice
      if voice == None:
        await message.channel.send("Voice channel is unoccupied")
        #they are not in a voice channel
      else:
        if len(args) > 0:
          for name in args:
          #name = args[0]
            if name in music.keys():
              location = music[name][0]
              volume = music[name][1]
              await message.channel.send(f"{name} added to queue")
              if guild_id in queues:
                queues[guild_id].append([location,volume,name,author])
              else: queues[guild_id] = [[location,volume,name,author]]
            else:
              return await message.channel.send("Invalid song")
        else:
          return await message.channel.send("No song specified")
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client == None:
          #not in voice, join the new channel
          paused[guild_id] = False
          await voice.channel.connect()
          await queue_manager(message.guild)
        elif message.author.guild_permissions.move_members:
          #move the bot
          await message.guild.voice_client.move_to(voice.channel)

    #Disconnect Command
    elif command == "dc" or command == "disconnect":
      #if message.author.guild_permissions.move_members:
      voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
      if voice_client != None:
        queues[message.guild.id] = []
        loops[message.guild.id] = 0
        loopqueue[message.guild.id] = 0
        await message.guild.voice_client.disconnect()
      else: await message.channel.send("Target lost")
      #else: await message.channel.send("Stop violating my first amendment rights!")

    #Skip Command
    elif command == "skip":
      id = message.guild.id
      if message.author.voice == None:
          return await message.channel.send("You are not in voice")
      #if message.author.guild_permissions.move_members or (id in playing and (playing[id][3] == author or playing[id][3] == 0)):
      voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
      if voice_client != None:
          message.guild.voice_client.stop()
      else: await message.channel.send("I am not in voice")
      #else: await message.channel.send("Come on, surely your mother taught you patience")

    #Loop Command
    elif command == "loop":
      loopqueue[message.guild.id] = 0
      if message.guild.id in loops:
          loops[message.guild.id] = 1 - loops[message.guild.id]
      else: loops[message.guild.id] = 1
      if loops[message.guild.id] == 1:
          await message.channel.send("The current song will now be looped")
      else: await message.channel.send("Cancelling the current loop")

    #Loopqueue Command
    elif command == "loopqueue":
      loops[message.guild.id] = 0
      if message.guild.id in loopqueue:
          loopqueue[message.guild.id] = 1 - loopqueue[message.guild.id]
      else: loopqueue[message.guild.id] = 1
      if loopqueue[message.guild.id] == 1:
          await message.channel.send("The current queue will now be looped")
      else: await message.channel.send("Cancelling the current loop")

    #Queue Command
    elif command == "queue":
      if message.guild.id in queues:
          queue = queues[message.guild.id] if message.guild.id in queues else []
          result = "Queue of length " + str(len(queue))
          if message.guild.id in playing:
              result += "\nNow playing: " + playing[message.guild.id][2]
          for item in queue:
              result += "\n" + item[2]
          await message.channel.send(result)
      else: await message.channel.send("The queue is empty")

    #Rock, Paper, Scissors
    elif command == "rps":
      if len(args) > 0:
        user = args[0]
        possible_actions = ["rock", "paper", "scissors"]
        nuke = random.randint(1,100)
        if nuke == 1:
          response = "nuke"
        else:
          response = random.choice(possible_actions)
        await message.channel.send(f"You chose {user}, I chose {response}.")

        #Tie
        if user == response:
          await message.channel.send(f"Both players selected {user}. It's a tie!")

        #Rock responses
        elif user == "rock":
          if response == "scissors":
            await message.channel.send("Rock smashes scissors. You win.")
          else:
            await message.channel.send("Paper covers rock. You lose!")
        
        #Paper responses
        elif user == "paper":
          if response == "rock":
            await message.channel.send("Paper covers rock. You win.")
          else:
            await message.channel.send("Scissors cuts paper. You lose!")

        #Scissors responses
        elif user == "scissors":
          if response == "paper":
            await message.channel.send("Scissors cuts paper. You win.")
          else:
            await message.channel.send("Rock smashes scissors. You lose!")

        #Surprise
        elif nuke == 1:
          await message.channel.send("Nuke, I win!")

        #User has not provided a valid input
        else:
          await message.channel.send("You have not provided a valid input")
      else:
        await message.channel.send("You have not provided a valid input")

    #Nuke a channel with the Russian flag
    elif command == "nuke":
      info = await client.application_info()
      if message.author == info.owner:
        await message.channel.send("No regrets!")
        await asyncio.sleep(2)
        async for message in message.channel.history():
          try:
            await message.add_reaction("🇷🇺")
          except discord.errors.Forbidden:
            pass 
      else:
        await message.channel.send("Please restrain your bloodlust for destruction!")

    #Get a list of music
    elif command == "music":
      await message.channel.send("There are " + str(len(music.keys())) + " songs loaded (Note: I have to abbreviate some song names because they're too long) : " + str(", ".join(music.keys())))

    #Help command
    elif command == "help":
      embed = discord.Embed(title="Commands", description="Commands you can utulise")
      commands = {
      "help" : "Become inception : Is this how you want to spend your time?",
      "play <song>" : "Listen to some tunes : To play music, join a voice channel, then type .play <song> to listen to music :D",
      "dc" : "Out darned spot, out! : Clears the queue and disconnects VexBot from the voice channel (Why would you do such a thing?)",
      "skip" : "Realise you have no patience : Skips the current song",
      "loop" : "Become Groundhog day : Loop the current song, this command is a toggle",
      "loopqueue" : "Groundhog Day: DLC : Loop the current queue, this command is a toggle",
      "rps <your choice here>" : "Play rock, paper, scissors",
      "music" : "See the songs you can play",
      "info <song>" : "Displays the author/s of a specified song, contains featured artists if applicable and the full song name for a specified song.",
      "status" : "Check the status of Tuddlet",
      "clear <limit>" : "Clear messages from a channel : This is an admin command only",
      "begone" : "Realise you have an urge to murder robots : Kills Tuddlet (How dare you)"}
      if len(args) > 0:
        if args[0] in commands:
            return await message.channel.send(commands[args[0]])
      for command in commands.keys():
          embed.add_field(name=prefix+command,value=commands[command])
      await message.channel.send(content=None, embed=embed)

    #Checks against ... error
    elif command == prefix*len(command):
      pass

    #Info Command (For music)
    elif command == "info":
      if len(args) > 0 and len(args) < 2:
        name = args[0]
        if name in music.keys():
          if len(music[name]) > 2:
            await message.channel.send(f"Author: {music[name][2]}\nFull Song Name: {music[name][3]}\n")
          else:
            await message.channel.send("Author: this track's author is unknown")
        else:
          await message.channel.send("Invalid track, please enter again.")
      else:
        await message.channel.send("Either you have not entered a track or you have entered too many. Please enter one track")

    #Dab
    elif command == "dab":
      await message.channel.send("<o/")

    #Status Command
    elif command == "status":
      await message.channel.send("Template: Hello?")
      info = await client.application_info()
      if message.author == info.owner:
        start_time = time.time()
        await message.channel.send("Response: Hello")
        stop_time = time.time()
        rep_time = stop_time - start_time
        await message.channel.send(f"Response took {rep_time:.2f}s")
      else:
        await message.channel.send(random.choice(["Response: Who said that?", "Response: I'm not defective!", "Response: You can't fire me, I quit!"]))

    #Clean Command
    elif command == "clear":
      banned_clients = [530362316408225817]
      if message.author in banned_clients: return
      clean_num = 0
      if message.author.guild_permissions.move_members:
        if len(args) > 0:
          try:
            clean_num = int(args[0])
          except ValueError:
            await message.channel.send("Value Error, please try again")
            pass
          async for message in message.channel.history(limit=clean_num):
            try:
              await message.delete()
            except discord.errors.Forbidden:
              await message.channel.send("No permissions to delete messages")
              break
          else:
            await channel_log.send("Clear complete")
        else:
          await message.channel.send("You need to provide a number")
      else:
        await message.channel.send("You do not have permission to remove messages")

    else:
      await message.channel.send("Invalid Command")

  else:
    content = " " + message.content.lower() + " "

  #Keyword Replies
  '''if " surprise " in content:
    await message.channel.send("A surprise? I love surprises!")
  if " music " in content:
    await message.channel.send("I can play music for you")'''

  #1 in 100 messages
  '''hundred = ["https://static3.srcdn.com/wordpress/wp-content/uploads/2020/01/Odo--In-MY-Meme-.jpg?q=50&fit=crop&w=740&h=307&dpr=1.5",
             "https://tenor.com/view/loading-discord-loading-discord-boxes-squares-gif-16187521",
             "Fun fact: if a sentence starts with 'fun fact', you will read the entire sentence",
             "https://media1.tenor.com/images/23aeaaa34afd591deee6c163c96cb0ee/tenor.gif"]

  onehundred = random.choice(hundred)

  if random.randint(1,100) == 1:
    await message.channel.send(onehundred)'''

client.run(token)

#logging channel id: 787123260164669450
#new logging channel id: 833837328430530580
