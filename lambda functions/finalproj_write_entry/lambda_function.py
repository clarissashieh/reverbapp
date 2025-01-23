#
# write_entry()
#
# Called when a user writes a new song journal entry. To keep the blurbs private and secure
# the function encrypts the text using an AWS KMS generated encryption key. 
#

import json
import boto3
import os
from base64 import b64encode
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: write_entry**")
    
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
    # Parse user inputs
    #
    
    data = json.loads(event['body'])  
    username = data["username"]
    date = data["date"]

    # get corresponding userid to username
    sql1 = "SELECT userid FROM users WHERE username = %s;"
    row = datatier.retrieve_one_row(dbConn, sql1, [username])
    userid = row[0]

    #
    # Scenario 1: only a date is passed. That means we just want to check if it's valid
    #
    
    if "song" not in data or "artist" not in data or "blurb" not in data:
      # check date format 
      if len(date) != 10 or date[4] != '-' or date[7] != '-': # invalid 
        return {
          "statusCode": 400,
          "body": json.dumps({
            "message": "Invalid date. Use YYYY-MM-DD."
            })
        }
      
      #
      # Users can only make ONE journal entry a day. If entry has already been made on a certain date,
      # the user cannot make another under the same date
      #

      sql2 = '''
      SELECT * FROM entries 
      WHERE userid = %s AND entrydate = %s;
      '''
      check_entry = datatier.retrieve_one_row(dbConn, sql2, [userid, date])
      #print("Database check entry:", check_entry)
      if check_entry and check_entry[0] is not None: 
        return {
          "statusCode": 400,
          "body": json.dumps({
          "message": "Invalid date. You already made an entry for today!",
          })
        }
      else: 
        return {
          "statusCode": 200,
          "body": json.dumps({
          "message": "Date valid.",
          })
        }

    #
    # Scenario 2: Valid date, make entry
    #

    else: 
      song = data["song"]
      artist = data["artist"]
      blurb = data["blurb"]

      print("**Logging entry**")

      # 
      # AWS KMS Encryption: generate a encryption key to encrypt the blurb 
      #                     so that it's unreadable in the database
      #
      kms_client = boto3.client('kms')
      key_id = 'alias/reverbapp-key'
      
      # Encrypt the blurb using the plaintext data key
      blurb_encrypted = kms_client.encrypt(
        KeyId=key_id,
        Plaintext=blurb.encode('utf-8') # turn blurb into bytes array before encryption
      )['CiphertextBlob'] # encrypted blurb

      # Retrieve encrypted key (CiphertextBlob) for storage (though not needed for decryption here)
      encryptionkey = kms_client.generate_data_key(
        KeyId=key_id,
        KeySpec='AES_256'
      )['CiphertextBlob']
      #
      # Update entries database
      #
      print("**Adding entry row to database**")
      
      sql2 = """
        INSERT INTO entries(userid, entrydate, songname, artist, blurb, encryptionkey)
                    VALUES(%s, %s, %s, %s, %s, %s);
      """
      
      datatier.perform_action(dbConn, sql2, [userid, date, song, artist, blurb_encrypted, encryptionkey])

      #
      # Entry upload done, return new entryid:
      #
      sql3 = "SELECT LAST_INSERT_ID();"
      
      row = datatier.retrieve_one_row(dbConn, sql3)
      entryid = row[0]
      
      print("entryid:", entryid)
      print("**DONE**")
      
      return {
        'statusCode': 200,
        'body': json.dumps({"message": "** entry logged! **"})
        } 
      
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }
