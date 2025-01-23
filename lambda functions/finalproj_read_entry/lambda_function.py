#
# read_entry() 
#
# Retrieves and returns the user's old journal entry. 
#
#

import json
import boto3
from base64 import b64encode
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: finalproj_read_entry**")
    
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
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    #
    # check path parameters
    #
    print("**Accessing Parameters**")
    
    if "username" in event:
      username = event["username"]
    elif "pathParameters" in event:
      if "username" in event["pathParameters"]:
        username = event["pathParameters"]["username"]
      else:
        raise Exception("requires username parameter in pathParameters")
    else:
        raise Exception("requires username parameter in event")
    
    if "date" in event:
      date = event["date"]
    elif "pathParameters" in event:
      if "date" in event["pathParameters"]:
        date = event["pathParameters"]["date"]
      else:
        raise Exception("requires username parameter in pathParameters")
    else:
        raise Exception("requires username parameter in event")


    #
    # check date format
    #
    if len(date) != 10 or date[4] != '-' or date[7] != '-': # invalid 
      return {
        "statusCode": 200,
        "body": json.dumps("Invalid date. Use YYYY-MM-DD.")
      }

    #
    # now retrieve all the users:
    #
    print("**Retrieving entry**")


    sql1 = '''
      SELECT userid FROM users 
      WHERE username = %s;
    '''
    userid = datatier.retrieve_one_row(dbConn, sql1, [username])[0]

    sql2 = '''
      SELECT * FROM entries 
      WHERE userid = %s AND entrydate = %s;
    '''
    
    row = datatier.retrieve_one_row(dbConn, sql2, [userid, date])

    # no entry that matches both user and date 
    if not row: 
      return {
        'statusCode': 200,  
        'body': json.dumps("You did not write an entry on this date!")
      }
    

    else: 
      print("**Entry Found**")
      #
      # Decryption
      # 
      blurb_encrypted = row[5]
      key_encrypted = row[6]
      # print("blurb", blurb_encrypted)
      # print("key", key_encrypted)
      # print(len(key_encrypted))
      # print(len(blurb_encrypted))

      # decrypt key that is unique to each entry
      kms_client = boto3.client('kms')
      key_response = kms_client.decrypt(
        CiphertextBlob=key_encrypted,
      )
      key_decrypted = key_response['Plaintext']
      print(key_decrypted)

      # decrypt blurb with decrypted key
      blurb_decrypted = kms_client.decrypt(
        CiphertextBlob=blurb_encrypted    
      )['Plaintext'].decode('utf-8')
      
      entry = {
        'entryid': row[0],
        'username': username, 
        'entrydate': str(row[2]),
        'songname': row[3],
        'artist': row[4],
        'blurb': blurb_decrypted
      }
    
      return {
        'statusCode': 200,
        'body': json.dumps(entry)
      }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
