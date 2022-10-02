from classes import catch, htmltxt, config
import sys

configArgs = ["c", "config"]

def main():
	if len(sys.argv) >= 2:
		if sys.argv[1] in configArgs:
			config.setIds(input("id: "), input("mdp: "))
			return

	result = catch()
	
	code = result.login()

	if code[0] != 200:
		print("code: " + str(code[0]))
		print("message: " + code[1])
		print("Identifiant ou mot de passe invalide, \n reconfigurez les maintenant ou en rajoutant l'option \"config\" à la fin de la ligne de commande.")
		config.setIds(input("id: "), input("mdp: "))
		return

	result.notes()
	result.devoirs()
	result.messages()
	result.planning()

	text = htmltxt(True)

	text.createTxt(result)
	print(text.notes, text.planning, text.devoirs, text.messages) # output in terminal
	
	name = "recapEcoleDirecte"

	html = htmltxt(False)
	a = html.createHtml(result, name)
	html.openWebPage(name, a)

main()
