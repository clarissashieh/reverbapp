#
# Python program to get JSON file of upcoming concerts from finalproj_concerts. 
# Triggered by API Gateway after concerts is finished running.
#

import json
import boto3
import os

from configparser import ConfigParser

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
    
    response = s3.Object(bucketname, "concerts_results.json").get()
    file_content = response['Body'].read().decode('utf-8') 
    print(response)

    return {
      'statusCode': 200,
      'body': json.dumps(file_content)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }