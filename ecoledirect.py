# Start (End: 26)

from classes import catch, htmltxt

def main():
	result = catch()

	# result.login("", "")
	result.login(input("id : "), input("mdp : "))

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

# End
