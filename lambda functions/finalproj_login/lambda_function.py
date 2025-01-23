#
# Authenticaion
#
# Validates user account when a user signs in to write or read a journal entry.  
#

import json
import bcrypt
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
    print("**Call to Lambda /login...")

    #
    # setup AWS based on config file:
    #
    config_file = 'reverbapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)

    try:
        # Parse incoming data from the event
        data = json.loads(event['body'])
        username = data["username"]
        pwdhash = data["pwdhash"]   

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
        # Check if the username already exists
        # 
        sql1 = "SELECT * FROM users WHERE username = %s;"
        check_user = datatier.retrieve_one_row(dbConn, sql1, [username])

        # If the username doesn't exist, return a message and do nothing
        if not check_user:
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "message": "Login failed. Username does not exist. Please make a new account!",
                })
            }

        # If the user exists, check the password
        else: 
            sql2 = "SELECT pwdhash FROM users WHERE username = %s;"
            real_pw = datatier.retrieve_one_row(dbConn, sql2, [username]) 

            if bcrypt.checkpw(pwdhash.encode('utf-8'), real_pw[0].encode('utf-8')): #checkpw() checks if the string matches its hashed form
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": "Login successful!"})
                }
            
            else: 
                return {
                    "statusCode": 401,
                    "body": json.dumps({"message": "Login failed. Invalid password"})
                }
	
    except Exception as err:
        print("**ERROR**")
        print(str(err))
        
        return {
        'statusCode': 500,
        'body': json.dumps(str(err))
    }
