#
# Client-side python app for Reverb app, which is calling
# a set of lambda functions in AWS through API Gateway.
#
# Reverb's overall purpose is to act as a music diary — users
# can journal their daily song choices, receive playlist recommendations
# based on their most recent entries, and get concert times for the 
# top artists of their Spotify accounts.
#
# Authors:
#  Clarissa Shieh
#  Kaitlyn Wang
#
#   Prof. Joe Hummel
#   Northwestern University
#   CS 310
#

import requests
import json
import pathlib
import logging
import sys
import time

from configparser import ConfigParser


############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.username = row[1]
    self.pwdhash = row[2]


class Entry:

  def __init__(self, row):
    self.entryid = row[0]
    self.userid = row[1]
    self.entrydate = row[2]
    self.songname = row[3]
    self.artist = row[4]
    self.blurb = row[5]
    self.encryptionkey = row[6]


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    
###################################################################
#
# web_service_put
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_put(url, data):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.put(url, json=data)
        
      if response.status_code in [200, 400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_put() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None

###################################################################
#
# web_service_post
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_post(url, data):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.post(url, json=data)
        
      if response.status_code in [200, 400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_post() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
  
############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => create an account")
    print("   2 => write a song journal entry")
    print("   3 => read an old journal entry")
    print("   4 => get song popularity score")
    print("   5 => see upcoming concerts")

    cmd = input()

    if cmd == "":
      cmd = -1
    elif not cmd.isnumeric():
      cmd = -1
    else:
      cmd = int(cmd)

    return cmd

  except Exception as e:
    print("**ERROR")
    print("**ERROR: invalid input")
    print("**ERROR")
    return -1

###################################################################
#
# add_user
#
def add_user(baseurl):
  """
  Prompts the user for the new user's username and then inserts
  this user into the database. But if the user's
  username already exists in the database, then we
  tell the user that they've already made an account.
  
  Parameters
  ----------
  baseurl: baseurl for web service
  
  Returns
  -------
  nothing
  """

  try:
    print("**Welcome!**")
    
    print("Make a username> ")
    username = input()

    print("Make a password> ")
    password = input()

    #
    # build the new user data packet:
    #
    
    data = {
      "username": username,
      "pwdhash": password
    }

    #
    # call the web service:
    #
    api = '/user'
    url = baseurl + api
    
    res = web_service_post(url, data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code in [400, 500]:  # we'll have an error message
        body = res.json()
        print("Error message:", body["message"])
      #
      return

    #
    # success, extract userid:
    #
    body = res.json()

    if "userid" in body:
      userid = body["userid"]
      message = body["message"]
      print("User", userid, "successfully", message)
    else: 
      print(body["message"])

  except Exception as e:
    logging.error("add_user() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# write_entry
#
def write_entry(baseurl):
  """
  Adds a new journal entry to the Reverb database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # get the log in info
    #
    username = input("Enter username>")
    password = input("Enter password>")

    # 
    # Call the login lambda function to see if user is valid
    #
    login_url = baseurl + "/login"
    login_data = {
        "username": username,
        "pwdhash": password
    }

    # debug
    # print("Login URL:", login_url)
    
    login_res = web_service_post(login_url, login_data)

    if login_res.status_code == 200:  # Login successful
        print("Login successful! Let's get to your journal...")
    else:
        print(login_res.json().get("message", "Login failed."))
        return

    # proceed to entry if login successful

    date = input("Enter the date today (YYYY-MM-DD)> ")

    #
    # call the web service:
    #

    # check if date is valid (right format AND the user has not written an entry on that date yet)
    api = '/write'
    url = baseurl + api

    date_data = {
      "username": username,
      "date": date
    }
    date_check = web_service_post(url, date_data)
    if date_check.status_code == 200:  # date is valid. proceed
        pass
    else:
        print(date_check.json().get("message", "Invalid date."))
        return
    
    #
    # if date is valid, proceed to make entry
    #

    print("\n**Let's record your Song of the Day!**")
    song = input("Song name> ")
    artist = input("Artist name> ")
    blurb = input("Write a short blurb about anything!> ")

    data = {
      "username": username,
      "date": date, 
      "song": song, 
      "artist": artist,
      "blurb": blurb
    }

    res = web_service_post(url, data)
    body = res.json()
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      print(body["message"])
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return


  except Exception as e:
    logging.error("**ERROR: failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# read_entry
#
def read_entry(baseurl):
  """
  Prints the journal entry written by the user that 
  matches the inputted date

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # get the log in info
    #
    username = input("Enter username> ")
    password = input("Enter password> ")

    # 
    # Call the login lambda function to see if user is valid
    #
    login_url = baseurl + "/login"
    login_data = {
        "username": username,
        "pwdhash": password
    }
    
    
    login_res = web_service_post(login_url, login_data)

    if login_res.status_code == 200:  # Login successful
        print("Login successful! Let's get to your journal...")
    else:
        print(login_res.json().get("message", "Login failed."))
        return

    # If login is successful, search for entry 
    date = input("Enter the date of the old entry (YYYY-MM-DD)> ")

    # make input data 
    
    #
    # call the web service:
    #
    api = '/read/'
    url = baseurl + api + username + "/" + date

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      try:
        body = res.json() # date was valid
        if isinstance(body, dict):
          print("** " + body["username"] + "'s Past Entry **")
          print("Date:", body["entrydate"])
          print("  Song of the Day:", body["songname"], "by", body["artist"])
          print("  Blurb:", body["blurb"])
          print("** End of Entryid:", body["entryid"], " **")
        else:
          # invalid date
          print(body)

      except ValueError:
        print("Error: Invalid Response")
        print(res.text)

    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return


  except Exception as e:
    logging.error("**ERROR: read_entry() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# popularity
#
def popularity(baseurl):
  """
  Searches for user's most recent song of the day and gives them its popularity score.
  
  Parameters
  ----------
  baseurl: baseurl for web service
  
  Returns
  -------
  nothing
  """

  try:
    print("Enter username>")
    username = input()
    #
    # call the web service:
    #
    api = '/popularity/' + username
    url = baseurl + api
    
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      body = res.json()
      if res.status_code == 404: # unsuccessful search, user probably inputted invalid song
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code in [400, 500]:  # we'll have an error message
        print("Error message:", body["message"])
      #
      return
    
    #
    # success
    #
    body = res.json()
    if "artist" not in body:
      print("Your most recent song of the day was \"" + body['song'] + "\" and its popularity score on Spotify is " + str(body["popularity"]) + ".")
    else: 
      print("Your most recent song of the day was \"" + body['song'] + "\" by " + body['artist'] + " and its popularity score on Spotify is " + str(body["popularity"]) + ".")

    
  except Exception as e:
    logging.error("popularity() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# concerts
#
def concerts(baseurl):
  """
  Gets users top 5 artists from Spotify API and searches for each's next concert using Ticketmaster API.
  
  Parameters
  ----------
  baseurl: baseurl for web service
  
  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/concerts-init'
    url = baseurl + api
    
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code in [400, 500]:  # we'll have an error message
        body = res.json()
        print("Error message:", body["message"])
      #
      return
    
    #
    # success
    #
    body = res.json()

    print("**IF YOU HAVEN\'T ALREADY: Please email clarissashieh2027@u.northwestern.edu with the email associated with your Spotify account so you can be added as a user to the app on Spotify's API!**")
    print("\n**Please copy and paste this link into your browser to grant Reverb authorization to your Spotify account:\n\n" + body)

    while(True):
      complete = input("\nHave you authorized your Spotify account? (y/n)> ")
      if (complete == "y"):
        print("\n**Searching for upcoming concerts from your top artists…**")
    
        api = '/concerts'
        url = baseurl + api
        
        res = web_service_get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code != 200:
          # failed:
          print("Failed with status code:", res.status_code)
          print("url: " + url)
          if res.status_code in [400, 500]:  # we'll have an error message
            body = res.json()
            print("Error message:", body["message"])
          #
          return
        #
        # success
        #
        body = res.json()
        concerts = json.loads(body)
        
        print()
        if(concerts == ""):
          print("None of your top artists have upcoming concerts :(")
        for row in concerts:
          for key, value in row.items():
            print(f"{key}: {value}")
          print("-" * 100)

        break

    
  except Exception as e:
    logging.error("concerts() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
# main
#
try:
  print('** Welcome to Reverb **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'reverbapp-client-config.ini'

  print("Config file to use for this session?")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    if cmd == 1:
      add_user(baseurl)
    elif cmd == 2:
      write_entry(baseurl)
    elif cmd == 3:
      read_entry(baseurl)
    elif cmd == 4:
      popularity(baseurl)
    elif cmd == 5:
      concerts(baseurl)
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
