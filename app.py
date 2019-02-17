#!/usr/bin/env python
#C:\Users\cdore\AppData\Local\Programs\Python\Python36-32

import pdb
#; pdb.set_trace()
import sys, os, io, time, re, cgi, csv, urllib.parse, urllib.request
import smtplib

from http.server import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from socket import gethostname, gethostbyname 
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
from sys import argv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
MAIL_USER = 'charles.dore@nexio.com' 

cookie = SimpleCookie()

def millis():
   """ returns the elapsed milliseconds (1970/1/1) since now """
   dt = datetime.now() - datetime(1970, 1, 1)
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return ms

HOSTserv = 'http://127.0.0.1:3000/'
HOSTclient = 'http://localhost:8080/'
HOSTcors = 'https://cdore00.github.io'
#self.headers["Host"] == 'cdore.ddns.net'

#Log file
LOG_DIR =os.getcwd() + '/log'
if not os.path.exists(LOG_DIR):
	os.makedirs(LOG_DIR)
LOG_FILE = LOG_DIR + '/' + str(int(millis())) + '.log'
print("logfile= " + LOG_FILE)

global logPass 
logPass = ""
if os.getenv('PINFO') is not None:
	logPass = os.environ['PINFO']

# MongoDB
import pymongo
from pymongo import MongoClient

dbase = "golf"
port = 27017
uri = "mongodb://localhost"
if os.environ.get('MONGODB_USER'):
	port = int(os.environ['MONGODB_PORT'])
	user = urllib.parse.quote_plus(os.environ['MONGODB_USER'])
	passw = urllib.parse.quote_plus(os.environ['MONGODB_PASSWORD'])
	domain = urllib.parse.quote_plus(os.environ['MONGODB_SERVICE'])
	dbase = urllib.parse.quote_plus(os.environ['MONGODB_DATABASE'])
	uri = "mongodb://%s:%s@%s/%s?authMechanism=SCRAM-SHA-1" % (user, passw, domain, dbase)
	if domain == "192.168.10.11":
		HOSTclient = 'https://cdore.ddns.net/'
		HOSTserv = 'https://cdore.ddns.net/pyt/'
	else:
		HOSTclient = 'https://cdore00.github.io/golf/'
		HOSTserv = 'https://pytgolf-cd-serv.1d35.starter-us-east-1.openshiftapps.com/'
		#HOSTclient = 'https://pytgolf-cdore2.a3c1.starter-us-west-1.openshiftapps.com/'
	print("HOSTclient=" + HOSTclient)

client = MongoClient(uri, port)
data = client[dbase]
from bson import ObjectId
from bson.json_util import dumps
from bson.json_util import loads
import json
	
# HTTPRequestHandler class
class golfHTTPServer(BaseHTTPRequestHandler):
	localClient = False
	@staticmethod
	def call_Func(strURL):
		pos = strURL.find("?")
		if pos == -1:
		  func = strURL[1:]
		else:
		  func = strURL[1:pos]
		fpart = func.split("/")
		func = fpart[len(fpart)-1]
		return func
	
	@staticmethod
	def return_Res(self,mess):
		if isinstance(mess, (int)) and mess == False:
			return
		else:
			#pdb.set_trace()
			# Send response status code
			self.send_response(200)
			# Send headers
			self.send_header('Content-type','text/html')
			if self.localClient:
				self.send_header('Access-Control-Allow-Origin', '*')
			else:
				self.send_header('Access-Control-Allow-Origin', HOSTcors)
				self.send_header('Access-Control-Allow-Credentials', 'true')
				self.send_header("Access-Control-Allow-Headers", "Origin, Content-Type, Cookie")
			#  Set cookie
			#self.send_header('Set-Cookie','superBig=zag;max-age=31536000')
			self.end_headers()
			# Write content as utf-8 data
			self.wfile.write(bytes(mess, "utf8"))
			return

	# GET
	def do_GET(self):
		"""Manage GET request received"""
		self.localClient = (self.client_address[0] == '127.0.0.1') 
		# Send message back to client
		query_components = parse_qs(urlparse(self.path).query)
		url = self.path
		#print("GET " + url)
		message = case_Func(self.call_Func(url), query_components, self)
		self.return_Res(self,message)
		return

	# POST	
	def do_POST(self):
		"""Manage POST request received"""
		self.localClient = (self.client_address[0] == '127.0.0.1')  # or self.client_address[0] == '172.17.0.1')
		#pdb.set_trace()	
		ctype, pdict = cgi.parse_header(self.headers['content-type'])
		if len(pdict) > 0:
			pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
			fields = cgi.parse_multipart(self.rfile, pdict)
			self.fields = fields
			if  'info' in fields:
				self.fields = fields['info'][0].decode()	
		else:
			content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
			post_data = self.rfile.read(content_length) # <--- Gets the data itself

		cook =  self.headers["Cookie"]
		print('Cookies Allow do_POST= ' + str(cook))

		
		# Send message back to client
		query_components = parse_qs(urlparse(self.path).query)
		if not query_components and len(pdict) == 0:
			query_components = urllib.parse.parse_qsl(str(post_data.decode('utf-8')))
		url = self.path
		
		##print("POST2 " + url)
		message = case_Func(self.call_Func(url), query_components, self)
		self.return_Res(self,message)
		
		return		
	
	def fields_TO_obj(self):
		pos = self.fields.find("{")
		strobj = self.fields[pos:]
		return loads(strobj)
	
#End class

def case_Func(fName, param, self):
	if fName == "ose":
		return(ose(self))
	elif fName == "listLog":
		return(listLog(param))
	elif fName == "addUserIdent":
		return(addUserIdent(param, self))
	elif fName == "confInsc":
		return(confInsc(param, self))
	elif fName == "identUser":
		return(authUser(param, self))
	elif fName == "getPass":
		return(getPass(param, self))
	elif fName == "getPassForm":
		return(getPassForm(self))		
	elif fName == "saveUser":
		return(saveUser(param, self))
	elif fName == "getUser":
		return(getUserInfo(param, self))		
	elif fName == "updUser":
		return(updateUser(param, self))	
	elif fName == "savePass":
		return(savePassword(param, self))		
	elif fName == "showLog":
		return(showLog(param))
	elif fName == "getRegions":
		return(getRegionList())
	elif fName == "getParcInfo":
		return(getParcInfo(param, self))
	elif fName == "getFav":
		return(getFav(param, self))
	elif fName == "updateFav":
		return(updateFav(param, self))		
	elif fName == "searchResult":
		return(searchResult(param, self))
	elif fName == "getClubList":
		return(getClubList(param, self))
	elif fName == "getClubData":
		return(getClubData(param, self))
	elif fName == "getClubParc":
		return(getClubParc(param, self))
	elif fName == "getBloc":
		return(getBloc(param, self))
	elif fName == "getClubParcTrous":
		return(getClubParcTrous(param, self))
	elif fName == "setGolfGPS":
		return(setGolfGPS(param, self))
	elif fName == "countUserGame":
		return(countUserGame(param, self))
	elif fName == "getGameList":
		return(getGameList(param, self));
	elif fName == "getGameTab":
		return(getGameTab(param, self))
	elif fName == "endDelGame":
		return(endDelGame(param, self))
	elif fName == "updateGame":
		return(updateGame(param, self))
	elif fName == "getGolfGPS":
		return(getGolfGPS(param, self))
	elif fName == "getGame":
		return(getGame(param, self))
	elif fName == "saveClub":
		return(saveClub(param, self))
	elif fName == "delClub":
		return(delClub(param, self))
	elif fName == "setPosition":
		return(setPosition(param, self))
	elif fName == "getPosition":
		return(getPosition(param, self))		
	else:
		return("DB server3" + str(param))


# Requests
def ose(self):
	print(logPass)
	ostxt = (os.environ)
	
	#f = open('workfile.txt', 'w')
	#f.write("testtt\n")
	#f.close()
	#f = open(LOG_DIR + '/myScore.csv','r')
	# Autre techique
	#x = json.dumps([1, 'simple', 'list'])
	#json.dump(x, f)
			
	log_Info('oseFunct')
	print(ostxt)
	return(logPass)

def getID(strID):
	if len(strID) < 5:
		return int(strID)
	else:	
		return ObjectId(strID)

def cursorTOdict(doc):
	strCur = dumps(doc)
	jsonCur = loads(strCur)
	return dict(jsonCur[0])

def checkSession(self, role = None):
	""" Session ID check for user"""
	#pdb.set_trace()
	strCook =  self.headers["Cookie"]
	print('1-Cookies = ' + str(strCook))
	if strCook and 'sessID' in strCook and 'userID' in strCook:
		cookie.load(strCook)
		sID = cookie['sessID'].value
		uID = getID(cookie['userID'].value)
		coll = data.users
		print('2-Role = ' + str(role))
		if role is None:
			doc = coll.find({"_id": uID, "sessID": sID}, ["_id"])
		else:
			doc = coll.find({"_id": uID, "sessID": sID, "niveau":{"$in": role }}, ["_id"])
		if doc.count() > 0:
			return True
		else:
			return False
	else:
		return False

def addUserIdent(param, self):
	""" To add new user account """
	try:
		if param.get("email") and param.get("pass"):
			email = param["email"][0]
			passw = param["pass"][0]
			user = ""
			if param.get("user"):
				user = param["user"][0]

			coll = data.users
			docs = coll.find({"courriel": email})
			#pdb.set_trace()
			if docs.count() > 0:
				doc = cursorTOdict(docs)
				if doc['actif'] == False:
					if doc['motpass'] == passw:
						sendConfMail( HOSTserv + "confInsc?data=" + email , email, doc['Nom'])
						return dumps({"code":1, "message": "S0050"})	#existInactif(doc)
					else:
						return dumps({"code":3, "message": "S0051"})
				if doc['actif'] == True:
					return dumps({"code":2, "message": "S0058"})
			else:
				res = coll.insert({"Nom": user , "courriel": email, "motpass": passw , "niveau": "MEM", "actif": False}, {"new":True})

				name = user
				if name == "":
					name = email

				sendConfMail( HOSTserv + "confInsc?data=" + email , email, name)
				log_Info("Nouveau compte créé: " + email)
				return dumps({"code":-1, "message": "S0052"})
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def confInsc(param, self):
	""" To Confirm new account"""
	try:
		if param.get("data"):
			user = param["data"][0]
			coll = data.users
			docs = coll.find({"courriel": user})
			if docs[0]['actif'] == True:
				return ("<h1>Le compte " + docs[0]['courriel'] + " est d&eacute;j&agrave; actif.</h1>")
			else:
				#activateAccount(loginUser(res, docs[0].courriel, docs[0].motpass))
				res = coll.update({"courriel": user}, { "$set": {"actif": True}})
				log_Info("Nouveau compte activé: " + docs[0]['courriel'])

				redir = """<html><head><script type="text/javascript" language="Javascript">function initPage(){var cliURL = "%s",user = "%s",pass = "%s";document.location.href = cliURL + "login.html?data=" + user + "$pass$" + pass;}</script></head><body onload="initPage()"><h1>Confirmation en cours...</h1></body></html>""" % (HOSTclient, docs[0]['courriel'], docs[0]['motpass'])
				return redir
		else:	
			return("Confirm" + str(param))		
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def getPass(param, self):
	""" Recover password by email """
	try:
		if param.get("data"):
			email = param["data"][0]
			coll = data.users
			docs = coll.find({"courriel": email, "actif": True})
			if docs.count() > 0:
				sendRecupPassMail(docs[0]['courriel'], docs[0]['Nom'], docs[0]['motpass'])
				return dumps({"code":-1, "message": "S0054"})
			else:
				return dumps({"code": 1, "message": "S0055"})
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def getPassForm(self):
	""" Return HTML code form to change password """
	htmlContent = '<div id="accountForm"><div id="titrePref">Edit account</div><form id="formPass"></br> <div class="prefList"><label for="passUser" class="identLbl">New password</label><div class="prefVal"><input id="passUser" type="text" size="15" maxlength="20"/></div></div> <div><input id="okPref" class="bouton" type="submit" onClick="savePass(); return false;" value="Ok" /><input id="annulePref" class="bouton" type="button" onClick="closePref(); return false;"  value="Cancel"/></div></form></div>'
	writeCook(self,htmlContent)
	return False	
		
def writeCook(self, mess, sessID=False, userID=False):
	""" Write cookies and end session (caller function must return False) """
	#pdb.set_trace()
	self.send_response(200)
	self.send_header('Content-type','text/html')
	if self.localClient:
		self.send_header('Access-Control-Allow-Origin', '*')
	else:
		self.send_header('Access-Control-Allow-Origin', HOSTcors)
		self.send_header('Access-Control-Allow-Credentials', 'true')
		self.send_header("Access-Control-Allow-Headers", "Origin, Content-Type, Cookie")
		cook =  self.headers["Cookie"]
		#print('Cookies Allow authUser N= ' + str(cook))
		#  Set cookie
		if sessID:
			cookInfo = 'sessID=' + sessID + ';max-age=31536000'
			self.send_header('Set-Cookie', cookInfo)
		if userID:
			cookInfo = 'userID=' + userID + ';max-age=31536000'
			self.send_header('Set-Cookie', cookInfo)
	self.end_headers()
	# Write content as utf-8 data
	self.wfile.write(bytes(mess, "utf8"))
	return
		
def authUser(param, self):
	""" To Authenticate or return user info to modify """
	try:	
		
		if param:
			if not isinstance(param, (list)) and param.get("user"):
				user = param["user"][0]
				#print("1- user= " + str(user))
				coll = data.users
				doc = coll.find({"courriel": user, "actif": True}, ["_id","Nom", "courriel", "motpass", "niveau"])
				
				def setSessID(mess, userID):
					sessID = str(ObjectId())
					res = coll.update({"courriel": user}, { "$set": {"sessID": sessID}})
					writeCook(self, mess, sessID=sessID, userID=userID)
					
				if doc.count() == 0:
					return dumps({'resp': {"result": 0} })	# Authenticate fail
				else:
					dic = cursorTOdict(doc)
					dic['_id'] = str(dic['_id'])
				if param.get("pass") and not isinstance(param, (list)):
					passw = param["pass"][0]
					if str(dic['motpass']) == passw:
						del dic['motpass']
						docs = {"resp": {"result":True, "user": dic} }
						res = dumps(docs)	# Authenticated
						setSessID(res, dic['_id'])
						return False
					else:
						return dumps({'resp': {"result": 0} })	# Authenticate fail
				else:
					if param.get("action"):
						action = int(param["action"][0])
						if action > 0:	# To modifiy account
							del dic['motpass']
						return dumps(dic)  # To modifiy
					else:
						return dumps({'resp': {"result": 0} })	# Authenticate fail password empty
			else:
				return dumps({'resp': {"result": 0} })	# User is empty
		else:
			return dumps({'resp': {"result": 0} })	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def saveUser(param, self):
	""" To modify user account info"""
	try:
		if param.get("cour") and param.get("pass") and param.get("id"):
			user = param["cour"][0]
			passw = param["pass"][0]
			id = param["id"][0]
			name = param["name"][0]

			coll = data.users
			
			def updUser(doc):
				if str(doc['motpass']) == passw:
					if param.get("newpass"):
						Npass = param["newpass"][0]
						coll.update({"_id": o_id, "actif": True}, { "$set": {'Nom': name, 'courriel': user, 'motpass': Npass } })
					else:
						coll.update({"_id": o_id, "actif": True}, { "$set": {'Nom': name, 'courriel': user} })
					return dumps({"resp": {"result":True, "email": user} })
				else:
					return dumps({"resp": {"result":False, "message": "S0059"} }) # Invalid password
			
			def checkEmailExist(doc):
				docs = coll.find({"courriel": user, "_id": {"$ne": o_id}})
				if docs.count() > 0:
					return dumps({"resp": {"result":False, "message": "S0056"} }) # The new email allredy exist
				else:
					return updUser(doc)
			
			o_id = getID(id)
			docs = coll.find({"_id": o_id, "actif": True})
			
			if docs.count() > 0:
				dic = cursorTOdict(docs)
				return checkEmailExist(dic);
			else:
				return dumps({resp: {"result":False, "message": "S0057"} }) # The new email allredy exist
		
			return dumps({ })	# modified
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))	

def getUserInfo(param, self):
	""" Get user account info by administrator"""
	try:
		if self.localClient or checkSession(self, role = ['ADM']):
			coll = data.users
			if param.get("id"):
				o_id = getID(param["id"][0])
				doc = coll.find({"_id": o_id}, ["_id", "Nom", "courriel", "niveau", "actif", "note"])
				dic = cursorTOdict(doc)
				dic['role']	= ["MEM", "MEA", "ADM"]
				return dumps(dic)
			else:
				word = param["word"][0]
				if word == "xxxxx":
					doc = coll.find({}, ["_id", "Nom", "courriel", "actif"])
				else:
					doc = coll.find({"courriel": {'$regex': word}}, ["_id", "Nom", "courriel", "actif"]) 
				return dumps(doc)	
		else: 
			return ('{"n":0,"ok":0, "message": "S0062"}')	
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def updateUser(param, self):
	""" To modify user account info by administrator"""
	try:
		if self.localClient or checkSession(self, role = ['ADM']):
			if param.get("id"):
				o_id = getID(param["id"][0])
				user = param["user"][0]
				if "name" in param:
					name = param["name"][0]
				else:
					name = ""
				role = param["role"][0]
				active = param["active"][0]
				active = True if active == '1' else False
				
				coll = data.users
				docr = coll.update({"_id": o_id}, { "$set": {'Nom': name, 'courriel': user, "niveau": role, "actif": active } })
				return dumps(docr)
			else:
				return dumps({'ok': 0})	# No param
		else: 
			return ('{"n":0,"ok":0, "message": "S0062"}')
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))			
		
		
def savePassword(param, self):
	""" To modify password account by administrator"""
	try:
		if self.localClient or checkSession(self, role = ['ADM']):
			if param.get("id") and param.get("pass"):
				
				o_id = getID(param["id"][0])
				passw = param["pass"][0]
				
				"""strCook =  self.headers["Cookie"]
				if not strCook is None:
					cookie.load(strCook)
					admMail = cookie['userMail'].value
				"""
				coll = data.users
				docr = coll.update({"_id": o_id}, { "$set": {'motpass': passw } })
				if param.get("user_mail"):
					email = param["user_mail"][0]
					name = param["user_name"][0] if param.get("user_name") else "" 
					sendRecupPassMail(email, name, passw)
				return dumps(docr)
			else:
				return dumps({'ok': 0})	# No param
		else: 
			return ('{"n":0,"ok":0, "message": "S0062"}')
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))				


def getRegionList():
	col = data.regions
	docs = col.find({})
	res = dumps(docs)
	return res
	
	
def getParcInfo(param, self):
	try:
		if param.get("data"):
			parcID = getID(param["data"][0])
			coll = data.parcours
			docs = coll.find({"_id": parcID})
			return dumps(docs)
		else:
			return dumps({'ok': 0})	# No param	
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))			
	
def searchResult(param, self):

	try:
		if param.get("qn"):
			qNom = param["qn"][0]
			qVille = param["qv"][0]
		if param.get("qr"):
			qReg = int(param["qr"][0])
		if param.get("qd"):
			dist = float(param["qd"][0])
			lng = float(param["qlt"][0])
			lat = float(param["qln"][0])
		qT = []
		col = data.club
		
		if 'qNom' in locals():
			regxN = re.compile(qNom, re.IGNORECASE)
			regxV = re.compile(qVille, re.IGNORECASE)
			q1 = {"$or": [ {"nom": {"$regex": regxN } } , {"municipal": {"$regex": regxV} } ]}
			qT.append(q1)
		
		if 'qReg' in locals():
			q2 = {'region': qReg}
			qT.append(q2)

		if 'dist' in locals():
			q3 = {"location": { "$near" : {"$geometry": { "type": "Point",  "coordinates": [ lng , lat ] }, "$maxDistance": dist }}};
			qT.append(q3)
			
		query = { "$and": qT }
		docs = col.find(query).sort("nom")
		res = dumps(docs)
		return res
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def getFav(param, self):
	try:
		if param.get("data"):
			userID = getID(param["data"][0])
			coll = data.userFavoris
			docs = coll.find({"USER_ID": userID}, ["CLUB_ID"])
			
			def getClubNameList(clubList):
				coll = data.club
				favDocs = coll.find({"_id":{"$in": clubList }},["_id","nom"]).sort("nom")
				return dumps(favDocs)
			
			ids = []
			for x in docs:
				ids.append(x['CLUB_ID'])			

			return getClubNameList(ids)
		else:
			return dumps({'ok': 0})	# No param		
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def updateFav(param, self):
	""" Add club to user favorite list"""
	try:
		if param.get("data"):
			clubList = param["data"][0]
			ids = [x for x in clubList.split("$")]
			clubID = int(ids[0])
			userID = getID(ids[1])
			action = int(ids[2])

			coll = data.userFavoris

			if action == 1:
				docs = coll.insert_one({"CLUB_ID": clubID , "USER_ID": userID})
				if docs.acknowledged:
					r = {'n': 0, 'ok': 1.0}
				else:
					r = {'n': 0, 'ok': 0}
			else:
				docs = coll.remove({"CLUB_ID": clubID , "USER_ID": userID})
				r = docs
			return dumps(r)
		else:
			return dumps({'ok': 0})	# No param	
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
			
def getClubList(param, self):
	""" To get clubs list info"""
	if param.get("data"):
		clubList = param["data"][0]
		ids = [int(x) for x in clubList.split(",")]

		coll = data.club
		docs = coll.find({"_id": {"$in": ids }}, {"_id": 1,"nom": 1, "adresse": 1, "municipal": 1, "telephone": 1, "telephone2": 1, "telephone3": 1, "location": 1, "courses.TROUS": 1}).sort("nom")
		
		return dumps(docs)
	else:
		return dumps({'ok': 0})	# No param

def getClubData(param, self):
	try:
		if param.get("data"):
			oData = []
			oData.append(getRegionList())
			clb = getClubParc(param, self)
			oData.append(clb)
			clb = loads(clb)

			strParc = ""
			for x in clb[0]['courses']:
				strParc += str(int(x['_id'])) + "$"
			strParc=strParc[0:len(strParc)-1]
			pBlc = {}
			pBlc['data'] = [strParc]
			oData.append(getBloc(pBlc, self))
			
			return dumps(oData)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + str(sys.exc_info()[1]))		
		
def getClubParc(param, self):
	""" To get club and his courses info"""
	try:
		if param.get("data"):
			clubList = param["data"][0]
			ids = [x for x in clubList.split("$")]
			clubID = int(ids[0])
			userID = None if ids[1] == 'null' else ids[1]

			if userID:
				if len(userID) < 5:
					userID = int(userID)
				else:	
					userID = ObjectId(userID)
			
			def isFavorite(doc):
				if userID is not None and len(str(userID)) > 0:
					coll = data.userFavoris
					favDoc = coll.find({"CLUB_ID": clubID , "USER_ID": userID}, ["CLUB_ID"])
					if favDoc.count() > 0:
						doc['isFavorite'] = True
					else:
						doc['isFavorite'] = False
				return doc
				
			coll = data.club
			docs = coll.find({"_id": clubID })
			dic = cursorTOdict(docs)

			return (dumps([(isFavorite(dic))]))
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + str(sys.exc_info()[1]))
		
def getBloc(param, self):
	try:	
		if param.get("data"):
			
			blocList = param["data"][0]
			ids = [int(x) for x in blocList.split("$")]
			coll = data.blocs 
			docs = coll.find({"PARCOURS_ID":{"$in": ids }}).sort("PARCOURS_ID")
			return dumps(docs)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))	
		
def getClubParcTrous(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			ids = [int(x) for x in param.split("$")]
			clubID = ids[0]
			courseID = ids[1]

			coll = data.club
			doc = coll.find({"_id": clubID }, ["_id","nom", "courses", "latitude", "longitude"])

			if doc.count() > 0:
				coll = data.golfGPS
				docs = coll.find({"Parcours_id": courseID }).sort([['Parcours_id', pymongo.ASCENDING], ['trou', pymongo.ASCENDING]])
				if docs.count() > 0:
					dic = cursorTOdict(doc)
					res = [dic]				
					res[0]['trous'] = docs
					return dumps(res)
				else:
					return dumps(doc)

		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def setGolfGPS(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			courseId = int(para[0])
			trou = int(para[1])
			lat = float(para[2])
			lng = float(para[3])
			toInit = int(para[4])
			clubId = int(para[5])
			
			coll = data.golfGPS
			if self.localClient or checkSession(self, role = ['ADM','MEA']):
				if toInit == 0:
					docr = coll.update({ 'Parcours_id': courseId, 'trou': trou }, { '$set': {'Parcours_id': courseId, 'trou': trou, 'latitude': lat, 'longitude': lng } },  upsert=True )
					return dumps(docr)
				else:
					for i in range(toInit):
						holeNo = i + 1
						resp = coll.update({ 'Parcours_id': courseId, 'trou': holeNo }, { '$set': {'Parcours_id': courseId, 'trou': holeNo, 'latitude': lat, 'longitude': lng } },  upsert=True)
						if holeNo == toInit:
							#pdb.set_trace()
							coll = data.parcours
							pRep = coll.update({"_id":courseId}, {"$set":{"GPS": True }})
							pa = coll.find({'CLUB_ID': clubId})
							strCur = dumps(pa)
							cur = loads(strCur)
							coll = data.club
							res = coll.update({'_id': clubId}, {'$set':{"courses": cur }})
							return dumps(res)
			else: 
				return ('{"n":0,"ok":0, "message": "S0062"}')
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def countUserGame(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			user = getID(para[0])
			is18 = int(para[1])
			#pdb.set_trace()
			withGroup = True if len(para) > 2 else False
			
			coll = data.score
			if (is18 == 18):
				count = coll.find({"USER_ID": user, "T18": { "$exists": True, "$nin": [ 0 ] }}).count()
				if withGroup == True:
					group = coll.aggregate([ {"$match" : {"USER_ID": user, "T18": { "$exists": True, "$nin": [ 0 ] }}}, {"$group" : {"_id":{"name":"$name","parcours":"$PARCOURS_ID"}, "count":{"$sum":1}}} ])
			else:
				count = coll.find({"USER_ID": user, "$or":[{"T18":0},{"T18":None}]  } ).count()
				if withGroup == True:
					group = coll.aggregate([ {"$match" : {"USER_ID": user, "$or":[{"T18":0},{"T18":None}]  }}, {"$group" : {"_id":{"name":"$name","parcours":"$PARCOURS_ID"}, "count":{"$sum":1}}} ])
			if withGroup == True:
				return ('{"count":' + str(count) + ',"group":' + dumps(group) + '}')
			else:
				return ('{"count":' + str(count) + '}')
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))		

		
def getGameList(param, self):
	"""Return game list result """
	try:
		if param.get("user"):
			user = int(param["user"][0])
			skip = int(param["skip"][0])
			limit = int(param["limit"][0])
			is18 = int(param["is18"][0])
			intDate = int(param["date"][0])
			if param.get("parc"):
				parc = int(param["parc"][0])
			else:
				parc = 0
			if param.get("tele"):
				intTele = int(param["tele"][0])
			else:
				intTele = 0

			if intDate == 0:   # ou 0 ???
				intDate = 9999999999999

			cur = []
			coll = data.score
			
			def addCur(doc):
				
				for x in doc:
					if intTele != 2:  # If Not JSON then convert millisecond to date and ObjectId
						ts = x['score_date'] / 1000
						x['score_date'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
						x['_id'] = str(x['_id'])
					cur.append(x)
				
				if (intTele > 0):	# Request for download result in file
					self.send_response(200)
					self.send_header('Content-type','text/html')
					self.send_header('Access-Control-Allow-Origin', '*')
					if (intTele == 2):	# JSON file
						self.send_header('Content-disposition', 'attachment; filename=myScore.json')
						self.end_headers()
						self.wfile.write(bytes(dumps(cur), "utf8"))
					if (intTele == 1):	# CSV file
						outFile = io.StringIO()
						output = csv.writer(outFile, delimiter=';')
						output.writerow(cur[0].keys())	#Column names
						for x in cur:
							output.writerow(x.values())

						contents = outFile.getvalue()
						outFile.close()
						self.send_header('Content-disposition', 'attachment; filename=myScore.csv')
						self.end_headers()
						self.wfile.write(bytes(contents, "utf8"))
					return False
				else:	# Request for HTML page
					return dumps(cur)

			if is18 == 18:
				qO = {"USER_ID": user, "score_date": {"$lt":intDate}, "T18": { "$exists": True, "$nin": [ 0 ] } }
				#doc = coll.find({"USER_ID": user, "PARCOURS_ID": parc, "score_date": {"$lt":intDate}, "T18": { "$exists": True, "$nin": [ 0 ] } }).sort("score_date",-1).skip(skip).limit(limit)
			else:
				qO = {"USER_ID": user, "score_date": {"$lt":intDate}, "$or":[{"T18":0},{"T18":None}]  }
				#doc = coll.find({"USER_ID": user, "score_date": {"$lt":intDate}, "$or":[{"T18":0},{"T18":None}]  } ).sort("score_date",-1).skip(skip).limit(limit)			

			if parc != 0:
				qO["PARCOURS_ID"] = parc				
			doc = coll.find(qO).sort("score_date",-1).skip(skip).limit(limit)
			return addCur(doc)
			
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def getGameTab(param, self):
	try:
		if param.get("data"):
			
			gID = getID(param["data"][0])

			def getBloc(doc):
				coll = data.blocs
				blocs = coll.find({"PARCOURS_ID": doc['PARCOURS_ID'] })
				for x in blocs:
					if x['Bloc'] == "Normale":
						doc['par'] = x
				return dumps([doc]) 
			
			coll = data.score
			doc = coll.find({"_id":gID})
			if doc.count() > 0:
				doc = cursorTOdict(doc)
				if doc['score_date'] != None:
					ts = doc['score_date'] / 1000
					doc['score_date'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')	
				return(getBloc(doc))
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))		

def endDelGame(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			gID = para[0]
			o_id = getID(gID)
			action = int(para[1])
			resErr = '{"n":0,"ok":0, "message":'
			
			coll = data.score
			if checkSession(self):
				if action == 0:	# Delete game
				   res = coll.remove({"_id":o_id})

				if action == 1:  # End Game
					dateTime = int(millis())
					log_Info("End game: " + gID)
					res = coll.update({"_id":o_id}, { "$set": { "score_date": dateTime} })
				return dumps(res)
			else: 
				resErr += "\"S0061\"}" if action == 0 else "\"S0060\"}"
				return (resErr)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def updateGame(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			user = int(para[0])
			parc = int(para[1])
			hole = int(para[2])
			stroke = int(para[3])
			put = int(para[4])
			lost = int(para[5])
			name = (para[6])
			if stroke == 0:	#Delete score hole
				stroke = None
				put = None
				lost = None
			Tno = "T" + str(hole)
			Pno = "P" + str(hole)
			Lno = "L" + str(hole)
			
			coll = data.score
			if len(para) > 7:
				sData = (para[7])
				sData = loads(sData)
				sField = dict()
				sField["USER_ID"] = user
				sField["PARCOURS_ID"] = parc
				sField["score_date"] = None
				sField["name"] = name
				sField[Tno] = stroke
				sField[Pno] = put
				sField[Lno] = lost
				#pdb.set_trace()
				hn = 1
				for sH in sData:
					if len(sH) > 0:
						Tno = "T" + str(hn)
						Pno = "P" + str(hn)
						Lno = "L" + str(hn)
						sField[Tno] = None if sH["T"] == None else int(sH["T"])
						sField[Pno] = None if sH["P"] == None else int(sH["P"])
						sField[Lno] = None if sH["L"] == None else int(sH["L"])
					hn+= 1
				
				if len(para) > 8:
					oData = (para[8])
					oData = loads(oData)
					others = []
					for oD in oData:
						others.append(oD)
					sField["others"] = others

				res = coll.update({ "USER_ID": user, "PARCOURS_ID": parc, "score_date": None }, { "$set": sField },  upsert=True)
			else:
				res = coll.update({ "USER_ID": user, "PARCOURS_ID": parc, "score_date": None }, { "$set": {"USER_ID": user, "PARCOURS_ID": parc, "score_date": None, "name": name, Tno: stroke, Pno: put, Lno: lost} },  upsert=True)
			
			return getGame(None, self, userID = user, parcID = parc)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def getGolfGPS(param, self):
	try:
		if param.get("data"):
			courseID = int(param["data"][0])
			coll = data.golfGPS
			
			def getBlocGPS(gData):
				coll = data.blocs
				doc = coll.find({"PARCOURS_ID": courseID })
				Pdoc =dumps(gData)
				Pdoc=loads(Pdoc)
				Pdoc[0]['parc'] = doc
				return dumps(Pdoc)

			doc = coll.find({"Parcours_id": courseID }).sort("trou")

			return getBlocGPS(doc)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def getGame(param, self, userID = False, parcID = False):
	try:
		def getG(user, parc):
			coll = data.score
			doc = coll.find({ "USER_ID": user, "PARCOURS_ID": parc, "score_date": None })
			if doc.count() > 0:
				cur = cursorTOdict(doc)
				cur['_id'] = str(cur['_id'])
				return dumps([cur]) 
			else:
				return dumps([]) 
			
		if param:
			if param.get("data"):
				param = param["data"][0]
				para = [x for x in param.split("$")]
				user = int(para[0])
				parc = int(para[1])
				return getG(user, parc)
		else:
			return getG(userID, parcID)
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def saveClub(param, self):
	""" Save Club, courses and blocs data """

	try:
		if param.get("data"):
			
			#pdb.set_trace()
			obj = self.fields_TO_obj()
				
			def saveBlocs(tupC, Bids):
				""" Save blocs data for the courses """
				blocRes = []
				coll = data.blocs
				def getBlocID():
					#pdb.set_trace()
					docID = coll.find({}).sort("_id",-1).limit(1)
					return int(docID[0]["_id"] + 1)
				
				for bloc in oBlocs:
					res=dict()
					
					if len(str(bloc["_id"])) < 9 and int(bloc["_id"]) > 1000000:	# Not ObjectID and new attributed bloc ID 
						res["oldID"] = bloc["_id"]
						bloc["_id"] =  ObjectId()  #getBlocID()
						res["newID"] = str(bloc["_id"])
						for y in tupC:
							if bloc["PARCOURS_ID"] in y:
								bloc["PARCOURS_ID"] = y[1]	# Replace PARCOURS_ID by res["newID"] attributed
					else:
						bloc["_id"] = getID(str(bloc["_id"]))
						if bloc["_id"] in Bids:
							Bids.remove(bloc["_id"])
					print("save id " + str(bloc["_id"]) + "  PARCOURS_ID " + str(bloc["PARCOURS_ID"]))
					doc = coll.update({ '_id': bloc["_id"]}, { '$set': {'PARCOURS_ID': bloc["PARCOURS_ID"], 'Bloc': bloc["Bloc"], 'T1': bloc["T1"], 'T2': bloc["T2"], 'T3': bloc["T3"], 'T4': bloc["T4"], 'T5': bloc["T5"], 'T6': bloc["T6"], 'T7': bloc["T7"], 'T8': bloc["T8"], 'T9': bloc["T9"], 'T10': bloc["T10"], 'T11': bloc["T11"], 'T12': bloc["T12"], 'T13': bloc["T13"], 'T14': bloc["T14"], 'T15': bloc["T15"], 'T16': bloc["T16"], 'T17': bloc["T17"], 'T18': bloc["T18"], 'Aller': bloc["Aller"], 'Retour': bloc["Retour"], 'Total': bloc["Total"], 'Eval': bloc["Eval"], 'Slope': bloc["Slope"] } },  upsert=True )

					res["result"]=doc
					res["result"]["_id"] = bloc["_id"]
					blocRes.append(res)

				docs = coll.remove({"_id": {"$in": Bids } })
				return blocRes, Bids
				
			def saveCourses(clubID, tupC, Pids):
				""" Save courses data for the Club """
				courseRes = []
				coll = data.parcours
				def getCourseID():
					docID = coll.find({}).sort("_id",-1).limit(1)
					return int(docID[0]["_id"] + 1)
				def removeCourse(Pids):
					collB = data.blocs
					docs = coll.remove({"_id": {"$in": Pids } })			# Remove Courses
					docs = collB.remove({"PARCOURS_ID": {"$in": Pids } })	# Remove Bloc Courses
					collG = data.golfGPS
					docs = collG.remove({"Parcours_id": {"$in": Pids } })	# Remove GPS Courses   À TESTER
					return

				for parc in oCourses:
					res=dict()
					if parc["_id"] > 1000000:
						res["oldID"] = parc["_id"]
						parc["_id"] = getCourseID()
						res["newID"] = parc["_id"]
						tupC = tupC,(res["oldID"],res["newID"])
					#removeBloc(parc["_id"])
					print("save courses " + str(parc["_id"]))
					doc = coll.update({ '_id': parc["_id"]}, { '$set': {'CLUB_ID': parc["CLUB_ID"], 'POINTS': parc["POINTS"], 'PARCOURS': parc["PARCOURS"], 'DEPUIS': parc["DEPUIS"], 'TROUS': parc["TROUS"], 'NORMALE': parc["NORMALE"], 'VERGES': parc["VERGES"], 'GPS': parc["GPS"] } },  upsert=True )
					res["result"]=doc
					res["result"]["_id"] = parc["_id"]
					courseRes.append(res)
					if parc["_id"] in Pids:
						Pids.remove(parc["_id"])
				
				if len(Pids) > 0:
					removeCourse(Pids)
				return courseRes, tupC, Pids
				#[{'_id': '39', 'CLUB_ID': 47, 'POINTS': '24', 'PARCOURS': '', 'DEPUIS': '1990', 'TROUS': '18', 'NORMALE': '72', 'VERGES': '6322', 'GPS': True}, {'_id': 61, 'CLUB_ID': 47, 'POINTS': 'E', 'PARCOURS': '', 'DEPUIS': 0, 'TROUS': 9, 'NORMALE': 27, 'VERGES': 815, 'GPS': False}]
			
			""" Save Club data """

			if self.localClient or checkSession(self, role = ['ADM','MEA']):
			#if True:
				coll = data.club
				def getClubID():
					docID = coll.find({}).sort("_id",-1).limit(1)
					return int(docID[0]["_id"] + 1)
				#pdb.set_trace()
				##param = param["data"][0]
				tupC = (0,0),(0,0)	# For new PARCOURS_ID in blocs
				##jsonCur = loads(param)
				##obj = dict(jsonCur)
				oClub = obj["club"]
				oCourses = obj["course"]
				if 'blocs' in obj:
					oBlocs = obj["blocs"]
				#Postal code
				cp = oClub["codp"]
				cp = cp.upper()
				cp = re.sub(r" ", "", cp)
				cps = cp
				matchObj = re.match("^(?!.*[DFIOQU])[A-VXY][0-9][A-Z]●?[0-9][A-Z][0-9]$"  ,cp)
				if (matchObj):
					cps = cp[0:3] + " " + cp[3:6]

				clubID = oClub["ID"]
				if clubID > 1000000:	# New club
					clubID = getClubID()
				
				doc = coll.update({ '_id': clubID}, { '$set': {'nom': oClub["name"], 'prive': oClub["prive"], 'adresse': oClub["addr"], 'municipal': oClub["ville"], 'codepostal': cp, 'codepostal2': cps, 'url_club': oClub["urlc"], 'url_ville': oClub["urlv"], 'telephone': oClub["tel1"], 'telephone2': oClub["tel2"], 'telephone3': oClub["tel3"], 'email': oClub["email"], 'region': oClub["region"], 'latitude': oClub["lat"], 'longitude': oClub["lng"] } },  upsert=True )
				
				Pids = getCourseColl(clubID)
				Bids = getBlocColl(Pids)
				courseRes, tupC, cRem = saveCourses(clubID, tupC, Pids)
				if 'oBlocs' in locals():
					blocRes, bRem = saveBlocs(tupC, Bids)
				else:
					blocRes = []
					bRem = []
				upd=coll.update({'_id':clubID}, {'$set':{"courses": oCourses, "location": {'type': "Point", 'coordinates': [ oClub["lng"], oClub["lat"] ]} }});
				doc["courses"] = courseRes
				doc["blocs"] = blocRes
				doc["removedC"] = cRem
				doc["removedB"] = bRem
				return dumps(doc)
			else: 
				return ('{"n":0,"ok":0, "message": "S0062"}')	# Check Session error
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def getCourseColl(clubID):
	collP = data.parcours
	Pdocs = collP.find({"CLUB_ID": clubID })
	Pids = []
	for x in Pdocs:
		Pids.append(x['_id'])
	return Pids

def getBlocColl(courseColl):
	collB = data.blocs
	Bdocs = collB.find({"PARCOURS_ID":{"$in": courseColl }})
	Bids = []
	for x in Bdocs:
		Bids.append(x['_id'])
	return Bids
	
def delClub(param, self):
	try:
		if param.get("data"):
			clubID = int(param["data"][0])
			
			collC = data.club
			collP = data.parcours
			collB = data.blocs
			
			# Course collection
			Pids = getCourseColl(clubID)
				
			#Remove data
			doc = collB.remove({"PARCOURS_ID":{"$in": Pids }})
			doc = collP.remove({"CLUB_ID":clubID})
			doc = collC.remove({"_id": clubID })
			
			return dumps(doc)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))

def setPosition(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			coll = data.trajet
			#pdb.set_trace()
			userId = getID(para[0])
			timeStart = int(para[1])
			locTime = int(para[2])
			locLat = float(para[3])
			locLng = float(para[4])
			locAcc = int(float(para[5]))
			if (len(para) > 6):
				#print(str(len(para)))
				hotSpot = int(para[6])
				doc = coll.update( { 'USER_ID': userId, 'startTime': timeStart}, {'$push': {'locList': {'time': locTime, 'lat': locLat, 'lng': locLng, 'acc': locAcc, 'hot': hotSpot}}},  upsert=True )
			else:	
				doc = coll.update( { 'USER_ID': userId, 'startTime': timeStart}, {'$push': {'locList': {'time': locTime, 'lat': locLat, 'lng': locLng, 'acc': locAcc}}},  upsert=True )
			#doc = coll.update( { 'USER_ID': userId, 'startTime': { '$gte': timeStart, '$lte': timeEnd }, {'$push': {'locList': {'time': locTime, 'lat': locLat, 'lng': locLng, 'acc': locAcc}}},  upsert=True )
			return dumps(doc)
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
def getPosition(param, self):
	try:
		if param.get("data"):
			param = param["data"][0]
			para = [x for x in param.split("$")]
			userId = getID(para[0])
			timeStart = int(para[1])
			timeEnd = timeStart + 86400000	# + 24hre

			coll = data.trajet
			#doc = coll.find( { 'USER_ID': userId, 'startTime': timeStart})
			if timeStart == 0:
				doc = coll.find( { 'USER_ID': userId}).sort("_id",-1).limit(1)
			else:
				doc = coll.find( { 'USER_ID': userId, 'startTime': { '$gte': timeStart, '$lt': timeEnd } })
				if doc.count() == 0:
					doc = coll.find( { 'USER_ID': userId, 'startTime': { '$gte': timeStart}}).sort("_id").limit(5)
			if doc.count() > 0:
				return dumps(doc)
			else:
				return dumps({'length': 0, 'timeStart': timeStart})
		else:
			return dumps({'ok': 0})	# No param
	except:
		log_Info(self.path + " ERROR: " + sys.exc_info()[0] + " ; " + str(sys.exc_info()[1]))
		
# Manage logs

def log_Info(mess):
	ip = gethostbyname(gethostname()) 
	t = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	mess = re.sub(r"<|>", " ", mess)	# Remplace tags < > by space
	strMess = t + "\t" + ip + "\t" + mess + "\n"
	with open(LOG_FILE,'a') as f:
		f.write(strMess)

def listLog(param):
	""" For typing password """
	if param:
		res = dict(param)
		passw = ""
		if "pass" in res:
			passw = res["pass"]
		if logPass == passw:
			return(listLogs())
		else:
			log_Info('listLog Unauthorized: ' + passw)
			return('<h2>Unauthorized</h2>')
	else:
		htmlCode = '<!DOCTYPE html><html lang="en-CA"><head><meta name="viewport" content="width=device-width" /></head><body><form action="listLog" method="post"><input type="password" name="pass"><input type="submit" name="submit"></form></body></html>'
		return(htmlCode)

def listLogs():
	""" List file in log directory"""
	fileList = os.listdir(LOG_DIR)
	cont = '<h2>Log files</h2>'
	for line in fileList:
		f = os.stat(LOG_DIR + '/' + line)
		t = time.ctime(f.st_ctime)
		s = f.st_size
		cont = cont + '<a target="_blank" href="./showLog?nam=' + line + '">' + line + "\t" + t + "\t" + str(int(s/1024) + 1) + " ko" '</a></br>'
	#print(fileList)
	return(str(cont))
	
def showLog(param):
	""" Display log file"""

	if param.get("nam"):
		fileName = param["nam"][0]
	lines = [line.rstrip('\n') for line in open(LOG_DIR + "/" + fileName)]
	f = os.stat(LOG_DIR + '/' + fileName)
	cont = '<h2>' + fileName + "  " + time.ctime(f.st_ctime) + '</h2>'
	for line in lines:
		cont = cont + line + '</br>'
	return(str(cont))

	

# Send mail
def sendRecupPassMail(eMail, name, passw):
	""" Send email to retreive password"""
	text = ''
	name = name if name != '' else eMail
	html = """\
	<html><body><div style="text-align: center;"><div style="background-color: #3A9D23;height: 34px;"><div style="margin: 3px;float:left;"><img alt="Image Golf du Québec" width="25" height="25" src="https://cdore00.github.io/golf/images/golf.png" /></div><div style="font-size: 22px;font-weight: bold;color: #ccf;padding-top: 5px;">Golfs du Qu&eacute;bec</div></div></br><p style="width: 100; text-align: left;">Bonjour %s,</p><p></p><p style="width: 100; text-align: left;">Votre mot de passe est : %s </p><p></p><p><div id="copyright">Copyright &copy; 2005-2017</div></p></div></body></html>
	"""  % (name, passw)
	fromuser = "Golf du Québec"
	subject = "Golf du Québec - Récupérer mot de passe de " + name 
	log_Info("Récupérer mot de passe de " + name + " : " + eMail)
	send_email(fromuser, eMail, subject, text, html)

def sendConfMail(link, email, name):

	recipient = email
	subject = "Golf du Québec - Confirmer l'inscription de cdore00@yahoo.com"
	
	fromuser = "Golf du Québec"

	# Create the body of the message (a plain-text and an HTML version).
	text = "Hi %s!\nCliquer ce lien pour confirmer l\'inscription de votre compte:\n%s\n\nGolf du Québec" % (name, link)
	html = """\
	<html><body><div style="text-align: center;"><div style="background-color: #3A9D23;height: 34px;"><div style="margin: 3px;float:left;"><img alt="Image Golf du Québec" width="25" height="25" src="https://cdore00.github.io/golf/images/golf.png" /></div><div style="font-size: 22px;font-weight: bold;color: #ccf;padding-top: 5px;">Golfs du Qu&eacute;bec</div></div></br><a href="%s" style="font-size: 20px;font-weight: bold;">Cliquer ce lien pour confirmer l\'inscription de votre compte:<p>%s</p> </a></br></br></br><p><div id="copyright">Copyright &copy; 2005-2018</div></p></div></body></html>
	""" % (link, email)
	send_email(fromuser, recipient, subject, text, html)

def send_email(fromuser, recipient, subject, text, html):
	""" Send email"""
	# Create message container - the correct MIME type is multipart/alternative.
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = fromuser
	msg['To'] = recipient 

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	msg.attach(part2)

	mail = smtplib.SMTP('smtp.gmail.com', 587)
	mail.ehlo()
	mail.starttls()
	mail.login(MAIL_USER, logPass)
	mail.sendmail(fromuser, recipient, msg.as_string())
	mail.quit()


# Start server listening request
def run(server_class=HTTPServer, handler_class=golfHTTPServer, port=8080, domain = ''):
	# Server settings
	server_address = (domain, port)
	httpd = HTTPServer(server_address, handler_class)
	print('running server...(' + domain + ":" + str(port) + ')')
	log_Info('running server...(' + domain + ":" + str(port) + ')')
	httpd.serve_forever()
	return

def build_arg_dict(arg):
	argd = dict()
	def add_dict(item):
		i = 0
		for x in arg:
			if x == item:
			  argd[x] = arg[i+1]
			else:
			  i+= 1

	if "port" in arg:
		add_dict("port")
	if "domain" in arg:
		add_dict("domain")
	if "pass" in arg:
		add_dict("pass")
	if "cors" in arg:
		add_dict("cors")
		
	if (len(arg) / 2) != len(argd):
		return False
	else:
		return argd

if __name__ == "__main__":
	#print(argv[0])
	if len(argv) > 1:
		arg = [x for x in argv]
		del arg[0]
		param = build_arg_dict(arg)
		if param:
			if "cors" in param:
				HOSTcors = param["cors"]
				print("CORS= " + HOSTcors)
			#print(str(len(argv)))
			if "pass" in param:
				#global logPass 
				logPass = param["pass"]
				if len(argv) == 3:
					run()
				if "domain" in param and "port" in param:
					run(domain=(param["domain"]), port=int(param["port"]))
				elif "domain" in param:
					run(domain=(param["domain"]))
				elif "port" in param:
					run(port=int(param["port"]))
			else:
				run()
		else:
			print("[domain VALUE] [port VALUE] [pass VALUE]")
	else:
		run()

