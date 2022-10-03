from classes import catch, htmltxt, config
import sys

configArgs = ["c", "config"]

def main():
	if len(sys.argv) >= 2: # checking if there is a additional arg
		if sys.argv[1] in configArgs: # checking if this arg is a config arg
			config.setIds(input("id: "), input("mdp: ")) # setting new Ids
			return

	result = catch()
	
	code = result.login() # login into ecoledirecte

	if code[0] != 200: # catching error connection
		print("code: " + str(code[0]))
		print("message: " + code[1])
		if code == 505:
			print("Identifiant ou mot de passe invalide, \n reconfigurez les maintenant ou en rajoutant l'option \"config\" à la fin de la ligne de commande.")
			config.setIds(input("id: "), input("mdp: "))
		else:
			print("Unknow connection error")
		return

	result.notes() # fetching notes, agenda, messages, planning excepptions
	result.devoirs()
	result.messages()
	result.planning()

	text = htmltxt(True) # initializating textual output (in terminal)

	text.createTxt(result) # creating text
	print(text.notes, text.planning, text.devoirs, text.messages) # output in terminal
	
	name = "recapEcoleDirecte" # filename to save html output

	html = htmltxt(False) # initializating html output
	a = html.createHtml(result, name) # creating html
	html.openWebPage(name, a) # saving & openning html output

main()
