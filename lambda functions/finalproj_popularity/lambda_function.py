#
# Python program to retrieve most recent song of the day of user from database. It then searches
# Spotify using the Spotify API and gets the popularity score of the song.
#

import json
import os
import base64
import datatier
import urllib3
import urllib

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: finalproj_popularity**")

    #
    # setup AWS based on config file:
    #
    config_file = 'reverbapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')
    
    #
    # open connection to the database:
    #
    print("**Opening DB connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    # 
    # Check if the username already exists
    # 
    if "username" in event:
      username = event["username"]
    elif "pathParameters" in event:
      if "username" in event["pathParameters"]:
        username = event["pathParameters"]["username"]
      else:
        raise Exception("requires username parameter in pathParameters")
    else:
        raise Exception("requires username parameter in event")

    sql = "SELECT userid FROM users WHERE username = %s;"
    userid = datatier.retrieve_one_row(dbConn, sql, [username])

    # If the username doesn't exist, return a message and do nothing
    if not userid:
      return {
        "statusCode": 401,
        "body": json.dumps({
            "message": "Username does not exist.",
        })
      }
    
    #
    # get most recent song from DB
    #
    print("**Get most recent DB entry**")
    sql = """
      SELECT songname, artist FROM entries 
      WHERE userid = %s
      ORDER BY entrydate DESC
    """
    
    result = datatier.retrieve_one_row(dbConn, sql, [userid])
    print(result)
    song = result[0]
    artist = result[1]
    print(song)
    print(artist)
    print("**Most recent song received**")

    #
    # get spotify api baseurl
    #
    spotifybaseurl = configur.get('spotify', 'webservice')

    #
    # make sure baseurl does not end with /, if so remove:
    #
    lastchar = spotifybaseurl[len(spotifybaseurl) - 1]
    if lastchar == "/":
      spotifybaseurl = spotifybaseurl[:-1]

    #
    # Get Spotify authorization
    #
    print("**Getting Spotify authorization**")
    http = urllib3.PoolManager()
    client_id = configur.get('spotify', 'client_id')
    client_secret = configur.get('spotify', 'client_secret')
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    data = urllib.parse.urlencode(data)

    res = http.request('POST', url, headers=headers, body=data)

    if res.status == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status)
      print("url: " + url)
      if res.status == 500:
        # we'll have an error message
        body = json.loads(res.data.decode('utf-8'))
        print("Error message:", body)
      #
      return

    body = json.loads(res.data.decode('utf-8'))
    access_token = body["access_token"]
     
    print("**Authorization successful**")

    #
    # Search for track on Spotify and get id if it exists
    #
    print("**Searching for track**")
    api = '/search?'
    url = spotifybaseurl + api
    header = {
      "Authorization": "Bearer " + access_token
    }
    data = {
      "q": "track%" + song + "artist%" + artist,
      "type": "track"
    }
    data = urllib.parse.urlencode(data)

    res = http.request('GET', url + data, headers=header)

    if res.status == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status)
      print("url: " + url)
      if res.status == 500:
        # we'll have an error message
        body = json.loads(res.data.decode('utf-8'))
        print("Error message:", body)
      #
      return
    
    body = json.loads(res.data.decode('utf-8'))
    print("**Getting Popularity**") 
    #
    # check if results were found
    #

    if "tracks" not in body or "items" not in body["tracks"] or len(body["tracks"]["items"]) <= 0:
      return {
        'statusCode': 404,
        'body': json.dumps("Your most recent song of the day was not found on Spotify :(")
      }
    else:  
      popularity = body["tracks"]["items"][0]["popularity"]
      song_name = body["tracks"]["items"][0]["name"]
      artist_name = body["tracks"]["items"][0]["artists"][0]["name"]


    print("**COMPLETED**")
    
    return {
      'statusCode': 200,
      'body': json.dumps({
        'song': song_name,
        'artist': artist_name,
        'popularity': popularity
      })
    }

  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
