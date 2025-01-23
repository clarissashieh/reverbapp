#
# Python program to find upcoming concert for each of user's top 5 artists. Triggered by authorization of 
# Spotify account through API Gateway. Creates JSON file of results and uploads to S3 bucket.
#

import urllib3
import urllib
import json
import boto3
import os
import base64

from configparser import ConfigParser

###################################################################
#
# classes
#
class Concert:
  def __init__(self, artist, body):
    self.artist = artist
    self.date = body['dates']['start']['localDate']
    print("***Got date***")
    location_result = body['_embedded']['venues'][0]
    if "city" in location_result:
      self.location = location_result['city']['name']
    if "state" in location_result:
      self.location = self.location + ', ' + location_result['state']['name']
    if "country" in location_result:
      self.location = self.location + ', ' + location_result['country']['name']
    print("***Got location***")
    self.link = body['url']
    print("***Got link***")
  
  def to_dict(self):
    return {
      'artist': self.artist,
      'date': self.date,
      'location': self.location,
      'link': self.link
    }

###################################################################

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: finalproj_concerts**")
    #
    # setup AWS based on config file:
    #
    config_file = 'reverbapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
  
    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)
    
    bucketname = configur.get('s3', 'bucket_name')
    
    s3 = boto3.resource('s3')
    
    #
    # get spotify and ticketmaster api baseurls
    #
    spotifybaseurl = configur.get('spotify', 'webservice')

    #
    # make sure baseurl does not end with /, if so remove:
    #
    lastchar = spotifybaseurl[len(spotifybaseurl) - 1]
    if lastchar == "/":
      spotifybaseurl = spotifybaseurl[:-1]

    ticketmasterbaseurl = configur.get('ticketmaster', 'webservice')
    lastchar = ticketmasterbaseurl[len(ticketmasterbaseurl) - 1]
    if lastchar == "/":
      ticketmasterbaseurl = ticketmasterbaseurl[:-1]

    #
    # get authorization and access token from Spotify API
    #
    http = urllib3.PoolManager()
    client_id = configur.get('spotify', 'client_id')
    client_secret = configur.get('spotify', 'client_secret')
    redirect_uri = 'https://t3jlpdy0mi.execute-api.us-east-2.amazonaws.com/prod/callback'

    code = event['queryStringParameters']['code']
    print(code)
    
    print("**Getting access token**")
    auth_url = 'https://accounts.spotify.com/api/token'

    headers = {
      'content-type': 'application/x-www-form-urlencoded',
      'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    }

    data = {
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    data = urllib.parse.urlencode(data)

    res = http.request('POST', auth_url, headers=headers, body=data)

    if res.status == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status)
      print("url: " + auth_url)
      if res.status == 500:
        # we'll have an error message
        body = json.loads(res.data.decode('utf-8'))
        print("Error message:", body)
      #
      return
    body = json.loads(res.data.decode('utf-8'))
    access_token = body['access_token']
    print(access_token)

    print("***Access token retrieved**")
    # 
    # get top 5 artists with Spotify API
    #
    print("**Searching Spotify API for user's top artists**")
    api = '/me/top/artists'
    url = spotifybaseurl + api
    header = {
      "Authorization": "Bearer " + access_token
    }

    res = http.request('GET', url, headers=header)

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
    items = body['items']
    
    artists = []
    for i in range(5):
      artist = items[i]['name']
      artists.append(artist)

    print(artists)

    print("**COMPLETE**")

    # 
    # search for next 3 attractions with Ticketmaster API for each top artist
    #
    print("**Searching Ticketmaster API for upcoming concerts**")
    consumer_key = configur.get('ticketmaster', 'consumer_key')
    
    # artists = ["Tate McRae", "Billie Eilish", "Sabrina Carpenter"]
    concerts = []
    # find next concerts for each top artist
    for artist in artists:
      api = '/events.json?'
      url = ticketmasterbaseurl + api
      data = {
        "apikey": consumer_key,
        "size": "1",
        "classificationName": "music",
        "keyword": artist
      }
      data = urllib.parse.urlencode(data)

      res = http.request('GET', url + data)

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
      print(body)
      if "_embedded" not in body: 
        continue

      else:
        # get details for each result
        results = body['_embedded']['events'][0]
        print("next concerts for one artist: ")
        print(results)
        print("***Searching for details for each result***")
        id = results['id']
        print(id)
        if (id is not ''):
          api = '/events/' + id + '?'
          url = ticketmasterbaseurl + api
          data = {
            "apikey": consumer_key,
          }
          data = urllib.parse.urlencode(data)
          
          res = http.request('GET', url + data)

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
        print("details for each concert: ")
        print(body)
        concerts.append(Concert(artist, body).to_dict())


    print("**Upload JSON results to S3**")
    s3.Object(bucketname, "concerts_results.json").put(
        Body=json.dumps(concerts),
        ContentType='application/json'
    )

    print("**COMPLETE**")

    #
    # list upcoming concerts
    #
    print("Upcoming concerts:")
    for concert in concerts:
      print(concert)

    return {
      'statusCode': 200,
      'body': json.dumps("success - return to client")
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }