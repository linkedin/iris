import requests
import MySQLdb

def fetch_users_from_oncall(oncall_base_url):
    oncall_user_endpoint = oncall_base_url + '/api/v0/users?fields=name&fields=contacts&fields=active'
    oncallUserList = []
    for user in requests.get(oncall_user_endpoint).json():
        if user['active']:
            #print user['name']
            oncallUserList.append(user['name'])
    return oncallUserList

def deleteInactiveUsers():

    print "Checking db for inactive users, connecting to oncall..."

    activeUserList  = fetch_users_from_oncall("http://0.0.0.0:8080")


    db = MySQLdb.connect("localhost","root","","irismobile" )

    usersToDelete = []
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    #get and iterate through all the users in the db
    cursor.execute("SELECT username from users")
    numrows = cursor.rowcount
    for x in xrange(0,numrows):
      row = cursor.fetchone()
      #check if the users also exist in the activeUserList if they don't add them to the userstodelete list
      if(row[0] not in activeUserList):
          usersToDelete.append(row[0])

    #deletin inactive users
    for usr in usersToDelete:
        print usr + " does not have active credentials, revoking authentication!"
        query = "DELETE FROM users WHERE username = %s"
        cursor.execute(query, (usr,))

        # accept the change
        db.commit()

    db.close

    print "Check complete, " + str(len(usersToDelete)) + " innactive user(s) found!"
