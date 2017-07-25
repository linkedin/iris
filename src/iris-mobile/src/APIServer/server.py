

# Let's get this party started!
#gunicorn
#iris
#oncall
#iris sender

import falcon
from falcon import HTTPNotFound, HTTPFound, HTTPBadRequest
import MySQLdb
import pyqrcode
import hmac
import hashlib
import oncallSync
import time
import calendar
import threading
import requests
import urllib
import json
import datetime
import jinja2
from jinja2 import Environment, PackageLoader, select_autoescape
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from json2html import *
import os
from os import urandom
import base64
from base64 import b64encode
from gcm import *
from keys import IRIS_KEY, GCM_KEY, APP_NAME, BASE_GET, BASE_CLAIM







mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff'}


#nonblocking check if users have active ldap credentials every 20 minutes
def scheduledInactiveUserPurge():
    t = threading.Timer(1200.0, scheduledInactiveUserPurge)
    t.start()
    oncallSync.deleteInactiveUsers()

t = threading.Timer(1200.0, scheduledInactiveUserPurge)
#t.start()
###
### t.start()  is commented out while testing shold be uncommented in prod
###

def load_template(name):

    path = os.path.join('templates', name)
    with open(os.path.abspath(path), 'r') as fp:
        return jinja2.Template(fp.read())


class IrisAuth(requests.auth.AuthBase):
    def __init__(self, app, key):
        self.header = b'hmac %s:' % app if isinstance(app, bytes) else app.encode('utf8')
        self.HMAC = hmac.new(key if isinstance(app, bytes) else key.encode('utf8'), b'', hashlib.sha512)

    def __call__(self, request):
        HMAC = self.HMAC.copy()
        path = request.path_url.encode('utf8')
        method = request.method.encode('utf8')
        body = request.body or b''
        window = str(int(time.time()) // 5).encode('utf8')
        HMAC.update(b'%s %s %s %s' % (window, method, path, body))
        digest = base64.urlsafe_b64encode(HMAC.digest())
        request.headers['Authorization'] = self.header + digest
        return request


class IrisClient(requests.Session):
    def __init__(self, app, key, base=BASE_CLAIM, version=0):
        super(IrisClient, self).__init__()
        self.auth = IrisAuth(app, key)
        self.url = base + '/v%d/' % version
        self.verify = False

    def incident(self, incidentId, owner):
        r = self.post(self.url + 'incidents/'+incidentId, json={'owner': owner})
        r.raise_for_status()
        try:
            return r.json()
        except:
            raise ValueError('Failed to decode json: %s' % r.text)

class ClaimResource(object):

    def on_post(self, req, resp):
        """Handles POST requests"""

        uri = req.uri
        print "URI: "+uri

        try:
            raw_json = req.stream.read()
        except Exception as ex:
            raise falcon.HTTPError(falcon.HTTP_400,
                'Error',
                ex.message)
        print(raw_json)
        try:
            result_json = json.loads(raw_json, encoding='utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_400,
                'Malformed JSON',
                'Could not decode the request body. The '
                'JSON was incorrect.')



        if 'username' not in result_json:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400
            return

        #check that the request has not expired
        if 'exp' not in result_json:
            resp.body = "BAD REQUEST: no expiration time"
            resp.status = falcon.HTTP_400
            return
        # else:
        #     if int(result_json['exp']) < int(calendar.timegm(time.gmtime())): #if the expiry time has alreay past
        #         resp.body = "BAD REQUEST: request time-out"
        #         resp.status = falcon.HTTP_408
        #         return

        #get uri

        usr = result_json['username']
        exp = result_json['exp']
        idList = result_json['listOfIds']



        contentToHMAC = uri + usr + str(exp) + str(idList)
        print(contentToHMAC)

        #get content of Authorization header
        if req.auth:
            client_digest = req.auth
        else:
            resp.body = "BAD REQUEST: no auth header"
            resp.status = falcon.HTTP_401  # This is the default status
            return

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT api_key from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        secret = row[0]
        db.close()



        #calculate signature using the shared secret and uri
        server_digest = hmac.new(secret, contentToHMAC, hashlib.sha256).hexdigest()
        print "Server calculated signature : " + str(server_digest)
        print "Client signature: " + str(client_digest)

        client = IrisClient(
            APP_NAME,
            IRIS_KEY
        )


        if hmac.compare_digest(server_digest,client_digest):

            print "VALID SIGNATURE!"

            owner = usr
            #go through each incident id and send a post to iris to claim it
            for incidentId in idList.split(","):

                #prepare HMAC signature
                print client.incident(incidentId,owner)



            resp.status = falcon.HTTP_200
            resp.body = "claimed"
        else:
            resp.body = "INVALID SIGNATURE!"
            resp.status = falcon.HTTP_401  # This is the default status
            return




        resp.status = falcon.HTTP_202
        resp.body = json.dumps(result_json, encoding='utf-8')

class GetAllResource(object):

    def on_get(self, req, resp):
        print "get request"
        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400
            return
        if 'limit' not in req.params:
            resp.body = "BAD REQUEST: no limit"
            resp.status = falcon.HTTP_400
            return

        #check that the request has not expired
        if 'exp' not in req.params:
            resp.body = "BAD REQUEST: no expiration time"
            resp.status = falcon.HTTP_400
            return
        else:
            if int(req.params['exp']) < int(calendar.timegm(time.gmtime())): #if the expiry time has alreay past
                resp.body = "BAD REQUEST: request time-out"
                resp.status = falcon.HTTP_408
                return



        #get uri
        uri = req.uri
        print "URI: "+uri


        #get content of Authorization header
        if req.auth:
            client_digest = req.auth
        else:
            resp.body = "BAD REQUEST: no auth header"
            resp.status = falcon.HTTP_401  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']
        #get limit
        lim = req.params['limit']

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT api_key from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        secret = row[0]
        db.close()



        #calculate signature using the shared secret and uri
        server_digest = hmac.new(secret, uri, hashlib.sha256).hexdigest()
        print "Server calculated signature : " + str(server_digest)
        print "Client signature: " + str(client_digest)




        if hmac.compare_digest(server_digest,client_digest):
            print "VALID SIGNATURE!"
            requestURL = BASE_GET+'/v0/incidents?target=%s&active=0&limit=%s' %(usr,lim)

            jsonObject = requests.get(requestURL).json()


            #repplace the ingraph url with a base64 encoded version of the image so it can be viewed outside corp network
            for incident in jsonObject:

                incident['created'] = str(datetime.datetime.fromtimestamp(incident['created']))
                if ('graph_image_url' in incident['context']):

                    gurl = incident['context']['graph_image_url']

                    if incident['context'].get('graph_image_url'):
                        content = "<img class='graph' src='data:;base64,"+base64.b64encode(urllib.urlopen(gurl).read())+ "'/>"
                        incident['context']['graph_image_url'] = content
                    else:
                        incident['context']['graph_image_url'] = ""



            resp.status = falcon.HTTP_200
            resp.content_type = 'application/json'
            resp.body = json.dumps(jsonObject)
        else:
            resp.body = "INVALID SIGNATURE!"
            resp.status = falcon.HTTP_401  # This is the default status
            return


class GetActiveResource(object):

    def on_get(self, req, resp):

        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400
            return

        #check that the request has not expired
        if 'exp' not in req.params:
            resp.body = "BAD REQUEST: no expiration time"
            resp.status = falcon.HTTP_400
            return
        else:
            if int(req.params['exp']) < int(calendar.timegm(time.gmtime())): #if the expiry time has alreay past
                resp.body = "BAD REQUEST: request time-out"
                resp.status = falcon.HTTP_408
                return


        #get uri
        uri = req.uri
        print "URI: "+uri


        #get content of Authorization header
        if req.auth:
            client_digest = req.auth
        else:
            resp.body = "BAD REQUEST: no auth header"
            resp.status = falcon.HTTP_401  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT api_key from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        secret = row[0]
        db.close()



        #calculate signature using the shared secret and uri
        server_digest = hmac.new(secret, uri, hashlib.sha256).hexdigest()
        print "Server calculated signature : " + str(server_digest)



        if hmac.compare_digest(server_digest,client_digest):
            print "VALID SIGNATURE!"
            requestURL = BASE_GET+'/v0/incidents?target=%s&active=1' %(usr)

            jsonObject = requests.get(requestURL).json()


            #repplace the ingraph url with a base64 encoded version of the image so it can be viewed outside corp network
            for incident in jsonObject:

                incident['created'] = str(datetime.datetime.fromtimestamp(incident['created']))
                if ('graph_image_url' in incident['context']):

                    gurl = incident['context']['graph_image_url']

                    if incident['context'].get('graph_image_url'):
                        content = "<img class='graph' src='data:;base64,"+base64.b64encode(urllib.urlopen(gurl).read())+ "'/>"
                        incident['context']['graph_image_url'] = content
                    else:
                        incident['context']['graph_image_url'] = ""



            resp.status = falcon.HTTP_200
            resp.content_type = 'application/json'
            resp.body = json.dumps(jsonObject)
        else:
            resp.body = "INVALID SIGNATURE!"
            resp.status = falcon.HTTP_401  # This is the default status
            return


#talk to iris
#TODO get rid of jinja and calls to iris prod
class TalkToIrisResource(object):

    def on_get(self, req, resp):

        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400
            return

        #check that the request has not expired
        if 'exp' not in req.params:
            resp.body = "BAD REQUEST: no expiration time"
            resp.status = falcon.HTTP_400
            return
        else:
            if int(req.params['exp']) < int(calendar.timegm(time.gmtime())): #if the expiry time has alreay past
                print req.params['exp']
                print calendar.timegm(time.gmtime())
                resp.body = "BAD REQUEST: request time-out"
                resp.status = falcon.HTTP_408
                return


        #get uri
        uri = req.uri
        print "URI: "+uri


        #get content of Authorization header
        if req.auth:
            client_digest = req.auth
        else:
            resp.body = "BAD REQUEST: no auth header"
            resp.status = falcon.HTTP_401  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT api_key from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        secret = row[0]
        db.close()



        #calculate signature using the shared secret and uri
        server_digest = hmac.new(secret, uri, hashlib.sha256).hexdigest()
        print "Server calculated signature : " + str(server_digest)



        if hmac.compare_digest(server_digest,client_digest):
            print "VALID SIGNATURE!"


            template = load_template('incidents.html')

            resp.status = falcon.HTTP_200
            resp.content_type = 'text/html'
            resp.body = template.render()
        else:
            resp.body = "INVALID SIGNATURE!"
            resp.status = falcon.HTTP_401  # This is the default status
            return





class AddDeviceResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        uri = req.uri
        print "URI: "+uri
        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400
            return
        #check that the request has a username field
        if 'deviceid' not in req.params:
            resp.body = "BAD REQUEST: no deviceid"
            resp.status = falcon.HTTP_400
            return



        #check that the request has a os field
        if 'os' not in req.params:
            resp.body = "BAD REQUEST: no os"
            resp.status = falcon.HTTP_400
            return

        #check that the request has not expired
        if 'exp' not in req.params:
            resp.body = "BAD REQUEST: no expiration time"
            resp.status = falcon.HTTP_400
            return
        else:
            if int(req.params['exp']) < int(calendar.timegm(time.gmtime())): #if the expiry time has alreay past
                resp.body = "BAD REQUEST: request time-out"
                resp.status = falcon.HTTP_408
                return

        #get uri


        #content of Authorization header
        #get content of Authorization header
        if req.auth:
            client_digest = req.auth
        else:
            resp.body = "BAD REQUEST: no auth header"
            resp.status = falcon.HTTP_401  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT api_key from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        secret = row[0]


        # accept the change
        #db.commit()


        print "Client's signature: "+ client_digest

        #calculate signature using the shared secret and uri
        server_digest = hmac.new(secret, uri, hashlib.sha256).hexdigest()
        print "Server calculated signature : " + str(server_digest)

        if hmac.compare_digest(server_digest,client_digest):
            print "VALID SIGNATURE!"

            # Prepare SQL query to update deviceid
            sql = "UPDATE users SET deviceid = %s, os = %s WHERE username = %s"
            try:

               values =(req.params['deviceid'],req.params['os'],usr)
               # Execute the SQL command
               cursor.execute(sql,values)
               # Commit your changes in the database
               db.commit()
            except MySQLdb.Error, e:
                try:
                    print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "MySQL Error: %s" % str(e)

        else:
            print "INVALID SIGNATURE!"
            resp.status = falcon.HTTP_401
            return

        # disconnect from server
        db.close()
        resp.status = falcon.HTTP_200
        resp.body = 'Device registered'


class QRKeyResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""




        resp.status = falcon.HTTP_200  # This is the default status

        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']

        #Generate crypto-secure 256 bit secret
        random_bytes = urandom(32)
        secret = b64encode(random_bytes).decode('utf-8')

        print "User: " + usr
        print "Secret: "+secret



        hmacFilename = hmac.new(str(secret), usr, hashlib.sha256).hexdigest()
        imageName = str(hmacFilename)+".png"
        qr = pyqrcode.create(secret)
        qr.png(imageName, scale=5)



        # Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()

        query = "DELETE FROM users WHERE username = %s"
        cursor.execute(query, (usr,))

        # accept the change
        db.commit()


        # Prepare SQL query to INSERT a record into the database.
        sql = "INSERT INTO users(username,api_key) VALUES (%s,%s)"
        try:
           values =(usr,secret)
           # Execute the SQL command
           cursor.execute(sql,values)
           # Commit your changes in the database
           db.commit()
        except:
           # Rollback in case there is any error
           print("ERROR EXECUTING SQL STATEMENT")
           db.rollback()

        # disconnect from server
        db.close()


        #return png of qr code containing secret then subsequently deletes it
        filepath =  imageName
        resp.content_type = "image/png"
        resp.stream = open(filepath, 'rb')
        resp.stream_len = os.path.getsize(filepath)
        os.remove(filepath)

# Credit to Werkzeug for implementation


class StaticResource(object):
    allow_read_no_auth = True
    frontend_route = False

    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp, filename):
        suffix = os.path.splitext(req.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = os.path.join(self.path, filename)
        try:
            resp.stream = open(filepath, 'rb')
            resp.stream_len = os.path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


#api to send push notifictions
class PushResource(object):
    def on_get(self, req, resp):

        #check that the request has a username field
        if 'username' not in req.params:
            resp.body = "BAD REQUEST: no username"
            resp.status = falcon.HTTP_400  # This is the default status
            return
        #check that the request has a username field
        if 'message' not in req.params:
            resp.body = "BAD REQUEST: no message"
            resp.status = falcon.HTTP_400  # This is the default status
            return

        #get username from get request parameters
        usr = req.params['username']

        #get key for username# Open database connection
        db = MySQLdb.connect("localhost","root","","irismobile" )

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        #get Secret corresponding to the username
        cursor.execute("""SELECT deviceid, os from users WHERE username = %s""", (usr,))
        row = cursor.fetchone()
        regId = row[0]
        os = row[1]

        if os == "Android":

            gcm = GCM(GCM_KEY)
            data = {'message': req.params['message']}

            gcm.plaintext_request(registration_id=regId, data=data)


        resp.status = falcon.HTTP_200
        resp.body = "PUSHED"



class LoginResource(object):
    def on_get(self, req, resp):
        template = load_template('login.html')

        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.body = template.render(something='testing')




app = falcon.API()


qrKey = QRKeyResource()

addDevice = AddDeviceResource()

talkToIris = TalkToIrisResource()

login = LoginResource()

getActive = GetActiveResource()

getAll = GetAllResource()

claim = ClaimResource()

push = PushResource()

app.add_route('/push', push)

app.add_route('/claim', claim)

app.add_route('/getall', getAll)

app.add_route('/getactive', getActive)

app.add_route('/login', login)#sample to be removed

app.add_route('/static/images/{filename}', StaticResource('/static/images'))

#generate qr key
app.add_route('/qrkey', qrKey)
#add device
app.add_route('/newdevice', addDevice)
#connect to iris and generate main page
app.add_route('/tti', talkToIris)

# app.add_route('/static/{filename}', StaticResource())
