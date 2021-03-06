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

countries = ["Iceland",
              "Faroe Islands",
              "Portugal",
              "Spain",
              "Andorra",
              "France",
              "Ireland",
              "United Kingdom",
              "Switzerland",
              "Italy",
              "Luxembourg",
              "Belgium",
              "Netherlands",
              "Germany",
              "Poland",
              "Czechia",
              "Slovakia",
              "Austria",
              "Hungary",
              "Denmark",
              "Norway",
              "Sweden",
              "Finland",
              "Slovenia",
              "Croatia",
              "Bosnia & Herzegovina",
              "Montenegro",
              "Serbia",
              "Kosovo",
              "North Macedonia",
              "Albania",
              "Greece",
              "Turkey",
              "Bulgaria",
              "Romania",
              "Moldova",
              "Estonia",
              "Latvia",
              "Lithuania",
              "Belarus",
              "Ukraine",
              "Russia"]

start = time.perf_counter()

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
    # play songs
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
  # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the economy plummet"), status=discord.Status.do_not_disturb)
  # await client.change_presence(activity=discord.Streaming(name="Youtube", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
  startup_time = time.perf_counter() - start
  try:
    channel_log = client.get_channel(log_id)
    await channel_log.send(f"Target Acquired\nStartup took {startup_time:.2f}s\n")
  except discord.errors.Forbidden:
    pass
  for guild in client.guilds:
    bot = guild.get_member(client.user.id)
    if bot.nick != "":
      try:
        await bot.edit(nick="")
      except discord.errors.Forbidden:
        pass

  print(f"Startup took {startup_time:.2f}s")

@client.event
async def on_member_update(before,after):
  if after.id == client.user.id and after.nick is not None:
    try:
      await after.edit(nick=None)
    except discord.errors.Forbidden:
      print("Changing nickname failed")
      pass

@client.event
async def on_message(message):
  if message.author.bot or message.author.id in banned_clients: return # don't consider other bots or banned clients
  # if message.author == client.user: return

  author = message.author.id
  content = " " + message.content.lower() + " "

  if message.content.startswith(prefix):
    length = len(prefix)
    rest = message.content[length:]
    words = rest.split(" ")
    command = words[0].lower()
    args = words[1:]

    # Kill command
    if command == "begone":
      info = await client.application_info()
      if message.author == info.owner:
        await message.channel.send(random.choice(["Shutting down...", "Goodnight", "Sleep mode activated", "Hibernating..."]))
        for guild in client.guilds:
          voice_client = discord.utils.get(client.voice_clients, guild=guild)
          if voice_client != None:
            await guild.voice_client.disconnect()
        await client.change_presence(status=discord.Status.offline) # await client.change_presence(activity=discord.Game("Among Us"))
        await client.close()
        quit()
      else:
        await message.channel.send(f"Stop shooting!")
        print(f"{message.author.display_name} attempted to murder me!")

    # Play Command
    elif command == "play":
      guild_id = message.guild.id
      voice = message.author.voice
      if voice == None:
        await message.channel.send("Voice channel is unoccupied")
        # they are not in a voice channel
      else:
        if len(args) > 0:
          for name in args:
          # name = args[0]
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
          # not in voice, join the new channel
          paused[guild_id] = False
          await voice.channel.connect()
          await queue_manager(message.guild)
        elif message.author.guild_permissions.move_members:
          # move the bot
          await message.guild.voice_client.move_to(voice.channel)

    # Disconnect Command
    elif command == "dc" or command == "disconnect":
      # if message.author.guild_permissions.move_members:
      voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
      if voice_client != None:
        queues[message.guild.id] = []
        loops[message.guild.id] = 0
        loopqueue[message.guild.id] = 0
        await message.guild.voice_client.disconnect()
      else: await message.channel.send("Target lost")
      # else: await message.channel.send("Stop violating my first amendment rights!")

    # Skip Command
    elif command == "skip":
      id = message.guild.id
      if message.author.voice == None:
          return await message.channel.send("You are not in voice")
      # if message.author.guild_permissions.move_members or (id in playing and (playing[id][3] == author or playing[id][3] == 0)):
      voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
      if voice_client != None:
          message.guild.voice_client.stop()
      else: await message.channel.send("I am not in voice")
      # else: await message.channel.send("Come on, surely your mother taught you patience")

    # Loop Command
    elif command == "loop":
      if len(args) > 0:
        if args[0] == "queue": # Loop Queue
          loops[message.guild.id] = 0
          if message.guild.id in loopqueue:
            loopqueue[message.guild.id] = 1 - loopqueue[message.guild.id]
          else: loopqueue[message.guild.id] = 1
          if loopqueue[message.guild.id] == 1:
            await message.channel.send("The current queue will now be looped")
          else: await message.channel.send("Cancelling the current loop")
        else:
          pass
      else: # Loop Track
        loopqueue[message.guild.id] = 0
        if message.guild.id in loops:
          loops[message.guild.id] = 1 - loops[message.guild.id]
        else: loops[message.guild.id] = 1
        if loops[message.guild.id] == 1:
          await message.channel.send("The current song will now be looped")
        else: await message.channel.send("Cancelling the current loop")

      # Loopqueue Command
      '''elif command == "loopqueue":
        loops[message.guild.id] = 0
        if message.guild.id in loopqueue:
          loopqueue[message.guild.id] = 1 - loopqueue[message.guild.id]
        else: loopqueue[message.guild.id] = 1
        if loopqueue[message.guild.id] == 1:
          await message.channel.send("The current queue will now be looped")
        else: await message.channel.send("Cancelling the current loop")'''

    # Queue Command
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

    # Rock, Paper, Scissors
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

        # Tie
        if user == response:
          await message.channel.send(f"Both players selected {user}. It's a tie!")

        # Rock responses
        elif user == "rock":
          if response == "scissors":
            await message.channel.send("Rock smashes scissors. You win.")
          else:
            await message.channel.send("Paper covers rock. You lose!")
        
        # Paper responses
        elif user == "paper":
          if response == "rock":
            await message.channel.send("Paper covers rock. You win.")
          else:
            await message.channel.send("Scissors cuts paper. You lose!")

        # Scissors responses
        elif user == "scissors":
          if response == "paper":
            await message.channel.send("Scissors cuts paper. You win.")
          else:
            await message.channel.send("Rock smashes scissors. You lose!")

        # Surprise
        elif nuke == 1:
          await message.channel.send("Nuke, I win!")

        # User has not provided a valid input
        else:
          await message.channel.send("You have not provided a valid input")
      else:
        await message.channel.send("You have not provided a valid input")

    # Nuke a channel with the Russian flag
    elif command == "nuke":
      info = await client.application_info()
      if message.author == info.owner:
        await message.channel.send("No regrets!")
        await asyncio.sleep(2)
        async for message in message.channel.history():
          try:
            await message.add_reaction("????????")
          except discord.errors.Forbidden:
            pass 
      else:
        await message.channel.send("Please restrain your bloodlust for destruction!")

    # Get a list of music
    elif command == "music":
      await message.channel.send("There are " + str(len(music.keys())) + " songs loaded (Note: I have to abbreviate some song names because they're too long) : " + str(", ".join(music.keys())))

    # Help command
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
      "8ball <question>" : "Ask a question and shake the magic 8 ball!",
      "music" : "See the songs you can play",
      "info <song>" : "Displays the author/s of a specified song, contains featured artists if applicable and the full song name for a specified song.",
      "status" : "Check the status of Tuddlet : Owner command only",
      "clear <limit>" : "Clear messages from a channel : This is an admin command only",
      "nick <user> <nickname>" : "Change a user's nickname : This is an admin command only",
      "website" : "Get a link to my website!",
      "begone" : "Realise you have an urge to murder robots : Kills Tuddlet (How dare you) : Owner command only"}
      if len(args) > 0:
        if args[0] in commands:
            return await message.channel.send(commands[args[0]])
      for command in commands.keys():
          embed.add_field(name=prefix+command,value=commands[command])
      await message.channel.send(content=None, embed=embed)

    # Checks against prefix error
    elif command == prefix*len(command):
      pass

    # Info Command (For music)
    elif command == "info":
      if len(args) > 0 and len(args) < 2:
        name = args[0]
        if name in music.keys():
          if len(music[name][2]) > 2:
            await message.channel.send(f"Author: {music[name][2]}\nFull Song Name: {music[name][3]}\n")
          else:
            await message.channel.send(f"Author: this track's author is unknown\nFull Song Name: {music[name][3]}\n")
        else:
          await message.channel.send("Invalid track, please enter again.")
      else:
        await message.channel.send("Either you have not entered a track or you have entered too many. Please enter one track")

    # Dab
    elif command == "dab":
      await message.channel.send("<o/")

    # Status Command
    elif command == "status":
      await message.channel.send("Template: Hello?")
      info = await client.application_info()
      if message.author == info.owner:
        start_time = time.time()
        await message.channel.send("Response: Hello")
        stop_time = time.time()
        rep_time = stop_time - start_time
        uptime = random.randint(1, 100)
        ping = client.latency * 1000
        await message.channel.send(f"Response took {rep_time:.2f}s\nPing: {ping:.0f} ms\nUptime: {uptime} hours")
      else:
        await message.channel.send(random.choice(["Response: Who said that?", "Response: I'm not defective!", "Response: You can't fire me, I quit!"]))

    # Clear Command
    elif command == "clear":
      if message.author.id in banned_clients: return # Banned people can't use clear
      amount = 0
      if message.author.guild_permissions.manage_messages:
        if len(args) > 0:
          try:
            amount = int(args[0])
          except ValueError:
            await message.channel.send("Value Error, please try again")
            pass
          try:
            await message.channel.purge(limit=amount)
            await channel_log.send("Clear complete")
          except discord.errors.Forbidden:
            await message.channel.send("No permissions to delete messages")
            pass
        else:
          await message.channel.send("You need to provide a number")
      else:
        await message.channel.send("You do not have permission to remove messages")
        print(f"{message.author.display_name} attempted to clear messages")

    # Website Command
    elif command == "website":
      await message.channel.send("Come visit my website! https://vexnos.github.io")

    # Spam Command
      '''elif command == "spam":
        info = await client.application_info()
        if message.author == info.owner:
          if len(args) > 0:
            try:
              amount = int(args[0])
            except ValueError:
              pass
            msg = " ".join(args[1:])
            for _ in range(amount):
              await message.channel.send(msg)
          else:
            await message.channel.send("Provide an amount and message")
        else:
          await message.channel.send("No")
          print(f"{message.author.display_name} tried to spam in {message.channel} in {message.guild}")'''

    # Magic 8 ball command
    elif command == "8ball":
      if len(args) > 0:
        question = " ".join(args[0:])
        if question.endswith("?"):
          responses = ["It is certain",
                      "It is decidedly so",
                      "Without a doubt",
                      "Yes definitely",
                      "You may rely on it",
                      "Reply hazy, try again",
                      "Ask again later",
                      "Better not tell you now",
                      "Cannot predict now",
                      "Concentrate and ask again",
                      "Don't count on it",
                      "My reply is no",
                      "My sources say no",
                      "Outlook not so good",
                      "Very doubtful"]

          await message.channel.send(f"Question: {question}\nAnswer: {random.choice(responses)}")
        else:
          await message.channel.send("That's not a question")
      else:
        await message.channel.send("You haven't provided a question!")

    # Change Nickname
    elif command == "nick":
      if message.author.guild_permissions.manage_nicknames:
        if len(args) > 0:
          if "!" in args[0]: # Author is on PC
            id = int(args[0][3:-1])
          else: # Author is on Mobile
            id = int(args[0][2:-1])
          member = message.guild.get_member(id)
          nick = " ".join(args[1:])
          try:
            await member.edit(nick=nick)
          except discord.errors.Forbidden:
            await message.channel.send("No perms to change nickname")
        else:
          await message.channel.send("You haven't entered anything")
      else:
        await message.channel.send("You do not have permission to execute this command")
        print(f"{message.author.display_name} attempted a nick change but lacked permission")

    # Actions command for Battle Royale
    # Actions include War, Alliance, Ideology
    elif command == "action":
      actions = ["war", "alliance", "ideology"]
      action = random.choice(actions)
      if action == "alliance":
        country1 = random.choice(countries)
        country2 = random.choice(countries)
        while country2 == country1:
          country2 = random.choice(countries)
        await message.channel.send(f"{country1} allies with {country2}!")
      elif action == "war":
        directions = ["Northerly",
                      "Northeasterly",
                      "Easterly",
                      "Southeasterly",
                      "Southerly",
                      "Southwesterly",
                      "Westerly",
                      "Northwesterly"]
        country = random.choice(countries)
        await message.channel.send(f"{country} will invade in a {random.choice(directions)} direction")
      elif action == "ideology":
        ideologies = ["Democratic",
                      "Communist",
                      "Fascist",
                      "Monarchy",
                      "Dictatorship",
                      "Oligarchic",
                      "Autocratic",
                      "Theocratic"]
        country = random.choice(countries)
        ideology = random.choice(ideologies)
        await message.channel.send(f"{country} has suffered a revolution and has turned into a {ideology} state!")
      else:
        pass

    # Invade command for Battle Royale
    elif command == "invade":
      name = " ".join(args)
      if len(args) > 0:
        if name in countries:
          countries.remove(name)
          await message.channel.send(f"{name} has been successfully invaded")
        else:
          await message.channel.send("Country does not exist")
      else:
        await message.channel.send("You failed to provide a country!")

    # Survivor command for Battle Royale
    elif command == "survivors":
      if len(countries) > 1:
        await message.channel.send("There are " + str(len(countries)) + " survivors remaining: " + str(", ".join(countries)))
      else:
        await message.channel.send(countries[0])
    
    # Invalid Command
    else:
      await message.channel.send("Invalid Command")

  else:
    content = " " + message.content.lower() + " "

  # Swearing check
  for swear in swears:
    if swear in content:
      try:
        await message.delete()
      except discord.errors.Forbidden: # No perms to delete messages
        pass

client.run(token)
