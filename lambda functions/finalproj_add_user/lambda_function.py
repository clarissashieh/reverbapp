#
# add_user()
#
# Called when a user writes a new song journal entry. To keep the blurbs private and secure
# the function encrypts the text using an AWS KMS generated encryption key. 
#

import json
import bcrypt
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
    print("**Call to Lambda /user...")

    #
    # setup AWS based on config file:
    #
    config_file = 'reverbapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)

    try:
        # Parse incoming data from the event
        data = json.loads(event['body'])  # Assuming the client sends JSON in the body
        print(data)

        # Hash the password securely using bcrypt, gensalt makes sure the same passwords don't have the same hashing
        pwdhash = bcrypt.hashpw(data["pwdhash"].encode('utf-8'), bcrypt.gensalt())

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

       
        # Check if the username already exists
        sql1 = "SELECT * FROM users WHERE username = %s;"
        check = datatier.retrieve_one_row(dbConn, sql1, [data["username"]])

        # If the username exists, return a message and do nothing
        if check:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Sorry! This username already exists. Please try again.",
                })
            }

        # If the user does not exist, insert a new user
        else: 
            sql2 = """
                INSERT INTO users (username, pwdhash)
                VALUES (%s, %s);
            """
            datatier.perform_action(dbConn, sql2, [data["username"], pwdhash.decode('utf-8')]) # decode turns the binary hash into a string

            # Get the inserted user ID
            sql3 = "SELECT LAST_INSERT_ID();"
            row = datatier.retrieve_one_row(dbConn, sql3)
            userid = row[0]
            
            print("Account created! Your userid is:", userid)

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "created",
                    "userid": userid
                })
            }
	
    except Exception as err:
        print("**ERROR**")
        print(str(err))
        
        return {
        'statusCode': 500,
        'body': json.dumps(str(err))
    }
