import base64
from bs4 import BeautifulSoup
from datetime import date as dte
from datetime import datetime
import html
import json
import os
import platform
import re
import requests as rq
from simple_term_menu import TerminalMenu
import subprocess

class config():
	def getIds():
		with open("ids.png", encoding="utf8") as fp:
			ids = BeautifulSoup(fp, 'html.parser')
		id_ = ids.find(id="id").string
		mdp = ids.find(id="mdp").string
		if id_ == None:
			id_ = input("id: ")
		else:
			id_ = base64.b64decode(id_).decode("utf-8", "ignore")
		if mdp == None:
			mdp = input("mdp: ")
		else:
			mdp = base64.b64decode(mdp).decode("utf-8", "ignore")
		return [id_, mdp]

	def setIds(id_, mdp):
		with open("ids.png", encoding="utf8") as fp:
			ids = BeautifulSoup(fp, 'html.parser')
		ids.find(id="id").clear()
		ids.find(id="id").insert(0, base64.b64encode(id_.encode("utf-8")).decode("utf-8"))
		ids.find(id="mdp").clear()
		ids.find(id="mdp").insert(0, base64.b64encode(mdp.encode("utf-8")).decode("utf-8"))
		f = open("ids.png", "w", encoding="utf8")
		f.write(str(ids))
		f.close()

class catch():
	def __init__(self):
		self.name = "Lorem Ipsum"
		self.token = ["token", "tokenData"]
		self.notesJson = "notes"
		self.devoirsJson = "devoirs"
		self.messagesJson = "messages"
		self.planningJson = "emploi du temps"
		myid, pwd = config.getIds()
		self.myid = myid
		self.pwd = pwd

	def login(self):
		data = 'data={"identifiant": "' + self.myid + '","motdepasse": "' + self.pwd + '"}'
		url = 'https://api.ecoledirecte.com/v3/login.awp?v=4.18.3'
		login = post(url, data)
		if login["code"] != 200:
			return [login["code"], login["message"]]
		self.name = login["data"]["accounts"][0]["prenom"] + " " + login["data"]["accounts"][0]["nom"]
		setId(self, login)
		setToken(self, login)
		config.setIds(self.myid, self.pwd)
		return [login["code"], login["message"]]

	def notes(self):
		url = 'https://api.ecoledirecte.com/v3/eleves/'+self.id+'/notes.awp?v=4.18.3&verbe=get&'
		data = self.token[1]
		notesJs = post(url, data)
		setToken(self, notesJs)
		self.notesJson = notesJs["data"]["periodes"][0]

	def devoirs(self):
		url = 'https://api.ecoledirecte.com/v3/Eleves/'+self.id+'/cahierdetexte.awp?v=4.18.3&verbe=get&'
		data = self.token[1]
		dates_json = post(url, data)
		dates = list(dates_json['data'].keys())
		setToken(self, dates_json)
		devoirs = {}
		for date in dates:
			url = 'https://api.ecoledirecte.com/v3/Eleves/'+self.id+'/cahierdetexte/' + date + '.awp?v=4.18.3&verbe=get&'
			data = self.token[1]
			homework_json = post(url, data)
			setToken(self, homework_json)
			matieres = homework_json['data']['matieres']
			devoirs[date] = {}
			for homework in matieres:
				if "aFaire" in homework:
					homeworkText = homework['aFaire']['contenu']
					homeworkText = html.unescape(base64.b64decode(homeworkText).decode("utf-8", "ignore"))
					homeworkText = re.sub('<[^<]+?>', '', homeworkText)
					devoirs[date][homework["matiere"].lower()] = homeworkText
		self.devoirsJson = devoirs

	def messages(self):
		url = "https://api.ecoledirecte.com/v3/eleves/"+self.id+"/messages.awp?v=4.18.3&verbe=getall&typeCours=received&orerBy=date&order=desc&page=0&itemsPerPage=20&onlyRead=&query=&idClasseur=0"
		data = self.token[1]
		msgJson = post(url, data)
		setToken(self, msgJson)
		if msgJson["data"]["pagination"]["messagesRecusNotReadCount"] != 0:
			messages = msgJson["data"]["messages"]["received"]
			idsMsg = []
			for message in messages:
				if not message["read"]:
					idsMsg.append(str(message["id"]))

			contenuMsg = []
			for idMsg in idsMsg:
				url = "https://api.ecoledirecte.com/v3/eleves/"+self.id+"/messages/" + idMsg + ".awp?v=4.18.3&verbe=get&mode=destinataire"
				data = self.token[1]
				contenuMsg.append(post(url, data))
				setToken(self, contenuMsg[len(contenuMsg)-1])
				contenuMsg[len(contenuMsg)-1] = contenuMsg[len(contenuMsg)-1]["data"]
				contenuMsg[len(contenuMsg)-1]["content"] =  re.sub('<[^<]+?>', '', html.unescape(base64.b64decode(contenuMsg[len(contenuMsg)-1]["content"]).decode("utf-8", "ignore")))
				url	= "https://api.ecoledirecte.com/v3/eleves/"+self.id+"/messages.awp?v=4.18.3&verbe=put&"
				data = 'data={"action": "marquerCommeNonLu","ids": [' + idMsg + '],"token": "' + self.token[0] + '"}'
				markAsNotRead = post(url, data)
				setToken(self, markAsNotRead)
			self.messagesJson = contenuMsg
		else :
			self.messagesJson = 0

	def planning(self):
		today = dte.today()
		if today.weekday() == 0:
			toweek = dte(1,1,1) - dte(1,1,1)
			firstDate = today
		else:
			toweek = today - dte(today.year, today.month, today.weekday())
			if toweek.days <= 0:
				if today.month == 1:
					firstDate = dte(today.year - 1, 12, 31+toweek.days)
				else:
					firstDate = dte(today.year, today.month - 1, ((dte(today.year, today.month, 1) - dte(today.year, today.month-1, 1)).days)+toweek.days)
			else:
				firstDate = dte(today.year, today.month, toweek.days)

		if firstDate.day + 14 > (dte(firstDate.year, firstDate.month + 1, 1) - dte(firstDate.year, firstDate.month, 1)).days: # must fix the bug in december : 12 + 1 = 13 (out of range (1..12))
			if firstDate.month == 12:
				lastDate = dte(firstDate.year + 1, 1, 14-(31-firstDate.day))
			else:
				lastDate = dte(firstDate.year, firstDate.month + 1, (firstDate.day + 14) - (dte(today.year, today.month + 1, 1) - dte(today.year, today.month, 1)).days) # must fix the bug in december : 12 + 1 = 13 (out of range (1..12))
		else:
			lastDate = dte(firstDate.year, firstDate.month, firstDate.day + 14)


		if today.month < 10:
			firstDateString = str(today.year)+"-0"+str(today.month)
		else:
			firstDateString = str(today.year)+"-"+str(today.month)

		if today.day < 10:
			firstDateString += "-0"+str(today.day)
		else:
			firstDateString += "-"+str(today.day)

		if lastDate.month < 10:
			lastDateString = str(lastDate.year)+"-0"+str(lastDate.month)
		else:
			lastDateString = str(lastDate.year)+"-"+str(lastDate.month)
		
		if lastDate.day < 10:
			lastDateString += "-0"+str(lastDate.day)
		else:
			lastDateString += "-"+str(lastDate.day)

		url = "https://api.ecoledirecte.com/v3/E/"+self.id+"/emploidutemps.awp?v=4.18.3&verbe=get&"
		data = 'data={"dateDebut": "' + firstDateString + '", "dateFin": "' + lastDateString + '","avecTrous": false, "token": "' + self.token[0] + '"}'
		planningJson = post(url, data)
		self.planningJson = planningJson

def setToken(self, token):
	token = token["token"]
	self.token[0] = token
	self.token[1] = 'data={"token": "' + token + '"}'

def setId(self, loginData):
	self.id = str(loginData["data"]["accounts"][0]["id"])

def post(url, data):
	return json.loads(rq.post(url, data=data, headers={"user-agent":"a"}).text)

class htmltxt():
	def __init__(self, TXT):
		self.TXT = TXT
		if self.TXT:
			self.notes = "notes"
			self.devoirs = "devoirs"
			self.messages = "messages"
			self.planning = "emploi du temps"
		else :
			self.notesHtml = "notes"
			self.devoirsHtml = "devoirs"
			self.messagesHtml = "messages"
			self.planningHtml = "emploi du temps"
		soup = ""
		
	def createNotes(self, notesJson):
		if self.TXT:
			notesTxt = "\n"
			notesTxt += "Moyenne Générale : " + notesJson["ensembleMatieres"]["moyenneGenerale"] + "\n"
			notesTxt += "Moyenne de Classe : " + notesJson["ensembleMatieres"]["moyenneClasse"] + "\n"
			notesTxt += "Moyenne Maximale : " + notesJson["ensembleMatieres"]["moyenneMax"] + "\n"
			notesTxt += "Moyenne Minimale : " + notesJson["ensembleMatieres"]["moyenneMin"] + "\n"
			self.notes = notesTxt
		else :
			notesHtmlPart = ""
			notesHtmlPart += "<li>Moyenne Générale : " + notesJson["ensembleMatieres"]["moyenneGenerale"] + "</li>"
			notesHtmlPart += "<li>Moyenne de Classe : " + notesJson["ensembleMatieres"]["moyenneClasse"] + "</li>"
			notesHtmlPart += "<li>Moyenne Maximale : " + notesJson["ensembleMatieres"]["moyenneMax"] + "</li>"
			notesHtmlPart += "<li>Moyenne Minimale : " + notesJson["ensembleMatieres"]["moyenneMin"] + "</li>"
			notesHtmlPart = BeautifulSoup(notesHtmlPart, "html.parser")
			self.notesHtml = notesHtmlPart

	def createDevoirs(self, devoirsJson):
		if self.TXT:
			devoirsTxt = ""
			nbDates = list(devoirsJson.keys())

			for date in nbDates:
				self.date = date
				devoirsTxt += "\n \nPour " + self.dateEditor() + ",\n"
				for matiere in devoirsJson[date]:
					devoirsTxt += "\n\t" + matiere + " :\n"
					if devoirsJson[date][matiere].find("\n") != -1:
						contenu = devoirsJson[date][matiere]
						contenu = contenu.split("\n")
						finalString = ""
						for part in contenu:
							finalString += "\t\t" + part + "\n"
						devoirsTxt += finalString.rstrip("\n\t") + "\n"
					else :
						devoirsTxt += "\t\t" + devoirsJson[date][matiere].rstrip("\n\t") + "\n"

			self.devoirs = devoirsTxt
		else :
			devoirsHtmlPart = ""
			dates = list(devoirsJson.keys())

			for date in dates:
				self.date = date
				devoirsHtmlPart += "<li><span style=\"font-weight: bold; color: red;\">Pour " + self.dateEditor() + ",</span><ul>"
				for matiere in devoirsJson[date]:
					devoirsHtmlPart += "<li><span style=\"font-weight: bolder; color: #0f0;\">" + matiere + " :</span><ul>"
					if devoirsJson[date][matiere].find("\n") != -1:
						htmlBr = devoirsJson[date][matiere]
						htmlBr = htmlBr.split("\n")
						finalString = ""
						for part in htmlBr:
							finalString += part + "<br>"
						devoirsHtmlPart += "<li>" + finalString.rstrip("\n\t") + "</li>"
					else :
						devoirsHtmlPart += "<li>" + devoirsJson[date][matiere].rstrip("\n\t") + "</li>"
					devoirsHtmlPart += "</ul></li>"
				devoirsHtmlPart += "</ul></li>"


			devoirsList = devoirsHtmlPart.split("\n")

			devoirsHtmlPart = ""
			for part in devoirsList:
				devoirsHtmlPart += part + "<br>"

			devoirsList = devoirsHtmlPart
			devoirsList = devoirsList.split("\t")

			devoirsHtmlPart = ""
			for part in devoirsList:
				devoirsHtmlPart += part + "&emsp;&emsp;"
			self.devoirsHtml = BeautifulSoup(devoirsHtmlPart, "html.parser")

	def createMessages(self, messagesJson):
		if self.TXT:
			pass
			messagesTxt = "\n"
			if messagesJson == 0:
				messagesTxt += "Vous n'avez aucun message non-lu"
			else :
				messagesTxt += "Vous avez "+str(len(messagesJson))+" message(s) non-lu(s) : \n"
				for message in messagesJson:
					messagesTxt += "\n--------------------------------------------------------------"
					messagesTxt += "\nDe : " + message["from"]["name"] + ", Objet : " + message["subject"]
					if len(message["files"]) != 0:
						messagesTxt += ", il y a " + str(len(message["files"])) + " pièce(s) jointe(s) : "
						for PJ in message["files"]:
							messagesTxt += PJ["libelle"] + ", "
					messagesTxt += "\n \n" + message["content"]
			self.messages = messagesTxt
		else :
			messagesTxt = ""
			if messagesJson == 0:
				messagesTxt += "<p>Vous n'avez aucun message non-lu</p>"
			else :
				messagesTxt += "Vous avez <span style=\"font-weight: bold;\">"+str(len(messagesJson))+"</span> message(s) non-lu(s) :<ul class=\"unindent\">"
				for message in messagesJson:
					messagesTxt += "<br/><li>--------------------------------------------------------------</li><br/>"
					messagesTxt += "<li>De : <span style=\"font-weight: bold; color: #00ff00;\">" + message["from"]["name"] + "</span>, Objet : <span style=\"font-weight: bold; color: #00ff00;\">" + message["subject"] + "</span>"
					if len(message["files"]) != 0:
						messagesTxt += ", il y a " + str(len(message["files"])) + " pièce(s) jointe(s) : "
						for PJ in message["files"]:
							messagesTxt += PJ["libelle"] + ", "
					messagesTxt += "</li><br/>"
					messagesTxt += "<li>" + message["content"] + "</li>"
				

				messagesList = messagesTxt.split("\n")

				messagesFinal = ""
				for part in messagesList:
					messagesFinal += part + "<br>"

				messagesTxt = messagesFinal
				messagesList = messagesTxt.split("\t")

				messagesFinal = ""
				for part in messagesList:
					messagesFinal += part + "&emsp;&emsp;"

			self.messagesHtml = BeautifulSoup(messagesTxt, "html.parser")

	def createPlanning(self, planningJson):
		if self.TXT:
			exceptions = []
			for cours in planningJson["data"]:
				if cours["isAnnule"] or cours["matiere"] == "Classe libérée":
					dayTime = [cours["start_date"], cours["end_date"]]
					date = dayTime[0].split(" ")[0]
					time = [dayTime[0].split(" ")[1], dayTime[1].split(" ")[1]]
					exceptions.append([date, time, "classeLibérée"])
				elif cours["typeCours"] == "CONGE":
					dayTime = cours["start_date"]
					exceptions.append([dayTime.split(" ")[0], 0, "congés"])

			planningString = ""
			if len(exceptions) == 0:
				planningString = "Vous n'avez aucun changements d'emploi du temps futur."
			else:
				for changement in exceptions:
					if changement[2] == "congés":
						self.date = changement[0]
						date = self.dateEditor()
						planningString += "\n" + date + ", il n'y a pas cours."
					else:
						self.date = changement[0]
						date = self.dateEditor()
						planningString += "\n" + date + ", de " + changement[1][0] + " à " + changement[1][1] + ", vous n'avez pas cours."
			self.planning = planningString
		else:
			exceptions = []
			for cours in planningJson["data"]:
				if cours["isAnnule"] or cours["matiere"] == "Classe libérée":
					dayTime = [cours["start_date"], cours["end_date"]]
					date = dayTime[0].split(" ")[0]
					time = [dayTime[0].split(" ")[1], dayTime[1].split(" ")[1]]
					exceptions.append([date, time, "classeLibérée"])
				elif cours["typeCours"] == "CONGE":
					dayTime = cours["start_date"]
					exceptions.append([dayTime.split(" ")[0], 0, "congés"])

			planningString = ""
			if len(exceptions) == 0:
				planningString = "<p>Vous n'avez aucun changement d'emploi du temps futur.</p>"
			else:
				for changement in exceptions:
					if changement[2] == "congés":
						self.date = changement[0]
						date = self.dateEditor()
						planningString += "<li>" + date + ", il n'y a pas cours.</li>"
					else:
						self.date = changement[0]
						date = self.dateEditor()
						planningString += "<li>" + date + ", de " + changement[1][0] + " à " + changement[1][1] + ", vous n'avez pas cours.</li>"
			self.planningHtml = BeautifulSoup(planningString, "html.parser")

	def createTxt(self, catchObject):
		self.createNotes(catchObject.notesJson)
		self.createDevoirs(catchObject.devoirsJson)
		self.createMessages(catchObject.messagesJson)
		self.createPlanning(catchObject.planningJson)

	def createHtml(self, catchObject, fileName):
		self.createNotes(catchObject.notesJson)
		self.createDevoirs(catchObject.devoirsJson)
		self.createMessages(catchObject.messagesJson)
		self.createPlanning(catchObject.planningJson)
		self.name = catchObject.name

		with open(fileName + ".html", encoding="utf8") as fp:
			soup = BeautifulSoup(fp, 'html.parser')
		soup.find(id="name").clear()
		soup.find(id="name").insert(0, self.name)
		soup.find(id="notes").clear()
		soup.find(id="notes").insert(0, self.notesHtml)
		soup.find(id="planning").clear()
		soup.find(id="planning").insert(0, self.planningHtml)
		soup.find(id="devoirs").clear()
		soup.find(id="devoirs").insert(0, self.devoirsHtml)
		soup.find(id="messages").clear()
		soup.find(id="messages").insert(0, self.messagesHtml)
		return soup

	def writeHtml(self, fileName, soup):
		file = open(fileName + ".html", mode="w", encoding="utf-8")
		file.write(soup.prettify())
		file.close()

	def openWebPage(self, name, soup):
		self.writeHtml(name, soup)
		if platform.system() == "Windows":
			path = subprocess.check_output("echo %%cd%%", shell=True).decode('UTF-8')[1:-3]
			os.system("explorer \"file://"+path+"\\"+name+".html\"")
		else: 
			path = subprocess.check_output("pwd", shell=True).decode('UTF-8')
			cmd = "xdg-open " + path[0:len(path)-1] + "/" + name + ".html &"
			os.system(cmd)

	def dateEditor(self):
		date = datetime.strptime(self.date, "%Y-%m-%d").date()
		today = dte.today()
		diff = (date - today).days

		dateString = ""
		
		weekdays = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
		
		if diff < 8:
			if diff == 0:
				dateString = "aujourd'hui"
			elif diff == 1:
				dateString = "demain"
			else :
				dateString = weekdays[date.weekday()]
		else :
			dateString = "le " + weekdays[date.weekday()] + " " + str(date.day)
			months = [" Janvier ", " Février ", " Mars ", " Avril ", " Mai ", " Juin ", " Juillet ", " Aout ", " Septembre ", " Octobre ", " Novembre ", " Décembre "]
			dateString += months[date.month] + str(date.year)

		return dateString
