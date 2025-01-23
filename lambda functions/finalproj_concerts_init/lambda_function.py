#
# Python program to get Spotify authorization from user for the concerts function. 
# The function triggers API Gateway once the user gives authorization and triggers 
# another lambda function that gives the user their upcoming concerts for their top
# artists.
#

import urllib.parse
import json
import os

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: finalproj_concerts_init**")
    #
    # setup AWS based on config file:
    #
    config_file = 'reverbapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)

    #
    # get authorization and access token from Spotify API
    #
    print("**Getting authorization from user**")
    client_id = configur.get('spotify', 'client_id')
    client_secret = configur.get('spotify', 'client_secret')
    redirect_uri = 'https://t3jlpdy0mi.execute-api.us-east-2.amazonaws.com/prod/callback'

    params = {
      'response_type': 'code',
      'client_id': client_id,
      'scope': 'user-read-private user-read-email user-top-read',
      'redirect_uri': redirect_uri
    }

    params = urllib.parse.urlencode(params)
    print('**Please copy and paste this link into your browser to grant Reverb authorization to your Spotify account: https://accounts.spotify.com/authorize?' + params + ' **')

    url = 'https://accounts.spotify.com/authorize?' + params
    return {
      'statusCode': 200,
      'body': json.dumps(url)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }