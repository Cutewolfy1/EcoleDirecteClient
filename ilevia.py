import requests as rq
from bs4 import BeautifulSoup as bs
from datetime import timedelta

# Logging
import logger
from logger import *
logger.MAINPREFIX = "[Ilevia]"

logger.INFO  = True
logger.DEBUG = False
logger.WARN  = True
logger.ERROR = True

# Constants
DEFAULTFRESHNESS = timedelta(minutes = 5)
FILEPATH = "data.json"

encodeUrl = rq.utils.quote # Tool to escape special chars like "&+=?" etc.

def search(query: str, resultNum: int = 5) -> dict | int:
	"""TODO Docstring"""
	query = encodeUrl(query) # Prevent url to broke if there are chars like "&+=?" etc.
	url = f"https://pnp-ihm-lille-prod.canaltp.fr/full/ws/v1/places?q={query}&origin=schedule&group=stop_area_and_lines"
	json = get(url) # Get query's result
	
	if "pt_objects" not in json: # If no result, return
		warn(f"No result found for the query : {query}")
		return 1

	result = {}
	for stop in json["pt_objects"][:resultNum]: # Keep only <resultNum> result(s)
		if stop["embedded_type"] == "line": # Sort lines and stops
			if "lines" not in result: result["lines"] = {} # Create "lines" dict if it is not already in.
			result["lines"][stop["line"]["code"]] = stop["id"] # Keep only name and id of stops {"stops": {"name1": "id1"}}
		else:
			if "stops" not in result: result["stops"] = {}	
			result["stops"][stop["name"]] = stop["id"]

	return result


def select(query: str, data: dict, resultNum: int = 52) -> dict | int:
	"""TODO Docstring + Multiple schedules"""
	matches = {}
	if "lines" in data:
		for stop in data["lines"]: # Get matches from query (unsensitive case)
			if query.lower() in stop.lower():
				matches[stop] = "lines"
	if "stops" in data:
		for stop in data["stops"]:
			if query.lower() in stop.lower():
				matches[stop] = "stops"

	if len(matches) == 0: # Return if no results
		info(f"No result matched with the query : {query}")
		return 1
	elif len(matches) >= 2: # Take the first if there more than one 
		info(f"Many results matched : {' '.join(matches)}, with the query : {query}, taking the first.")

	stop = list(matches)[0]
	type_ = matches[stop]
	del matches

	if type_ == "lines":
		return 0

	# Get lines passing by the selected stop
	url = f"https://pnp-ihm-lille-prod.canaltp.fr/full/ws/v1/stop_areas/{data[type_][stop]}/lines?count={resultNum}"
	lines = get(url)

	if "lines" not in lines: # Return if no lines passing by the selected stop (I dont know how it happens... We never know...)
		warn(f"No lines found for the stop : {stop}, id : {data[type_][stop]}")
		return 2


	lines = lines["lines"] # Get lines as array
	schedules = []
	result = {}

	for line in lines:
		result[line["code"]] = {} # Setup json result {"line1": {"direction1": ["1stArrival", "2nd"]}}  -- Note now, there is only 1 arrival available

		# Get the schedules
		url = f"https://pnp-ihm-lille-prod.canaltp.fr/fr/full/schedule/next_time/?stop_area_id={data[type_][stop]}&line_id={line['id']}&network_id=network:TRANSPOLE&from_datetime=now&data_freshness=realtime"
		time = get(url)

		directions = time["direction_type"] # Get which direction goes forward and backward
		for direction in directions: # Get directions
			name = line["routes"][0 if directions[direction] == "forward" else 1]["direction"]["name"] # Get display name of direction
			result[line["code"]][name] = []#bs(time["schedule"][direction][0], 'lxml').text # Setup json with display name
			
			for sched in time["schedule"][direction]: # Get time
				result[line["code"]][name] += [bs(sched, 'lxml').text] # Sub the useless html tags"""

	return result


def selectpos(pos: int, data: dict, resultNum: int = 52) -> dict | int:
	"""TODO Docstring. Maybe this function is useless... Nevermind :)"""
	totalLen = (len(data["lines"]) if "lines" in data else 0) + (len(data["stops"]) if "stops" in data else 0)
	if pos > totalLen or pos <= 0: # Return if invalid index
		error(f"Index out of range, index : {pos}, length of results : {totalLen}")
		return 3

	if "lines" in data:
		if pos <= len(data["lines"]):
			index = list(data["lines"])[pos - 1]
			return select(index, data, resultNum)
		else:
			index = list(data["stops"])[pos - len(data["lines"]) - 1]
			return select(index, data, resultNum)
	else:
		index = list(data["stops"])[pos - 1]
		return select(index, data, resultNum)

	return 4 # That wont be executed but...
	indexes = list(data) # Get keys
	debug(data, indexes, len(indexes), pos)


	return select(data[index], data, resultNum) # Calling select()


def get(url: str, json: bool = True, *args):
	"""TODO Docstring"""
	data = rq.get(url, *args) # Send request

	if json: # Return json or request object
		return data.json()
	else:
		return data

# Json management
def writeJson(data: dict, filePath: str = FILEPATH) -> None:
	"""Write json in data in file (at filePath)"""
	file = open(filePath, "w") # Write out to the file
	json.dump(data, file, indent=4, ensure_ascii=False) # indent=4 In order to format json
	file.close()

def readJson(filePath: str = FILEPATH) -> dict:
	"""Return json in file (at filePath) as a dict"""
	file = open(filePath, "r")

	try:
		data = json.load(file) # Extract json from file
	except json.decoder.JSONDecodeError:
		data = {} # If json isn't valid return empty dict
		error(f"Json in {filePath} contains error(s)")

	file.close()

	return data

def storeJson(data: any, name: str, filePath: str = FILEPATH) -> None | int:
	if type(data) == int:
		error("You cannot save int type in json due future errors")
		return 1

	mainData = readJson(filePath)
	encId = b64out(self.username)

	if encId not in mainData["ed"]["data"]: mainData["ed"]["data"][encId] = {}
	mainData["ed"]["data"][encId][name] = {}
	mainData["ed"]["data"][encId][name]["lastUpdated"] = datetime.today().isoformat()
	mainData["ed"]["data"][encId][name]["data"] = data

	writeJson(mainData, filePath)

def getJson(name: str, dataFreshness: timedelta = None, filePath: str = FILEPATH) -> any:
	mainData = readJson(filePath)
	encId = b64out(self.username)

	if encId not in mainData["ed"]["data"]:
		error(f"\"{self.username}\" has no saved data")
		return 1

	if name not in mainData["ed"]["data"][encId]:
		error(f"Requested data has not been saved early. Data key: {name}")
		return 1

	now = datetime.today()
	lastUpdate = datetime.fromisoformat(mainData["ed"]["data"][encId][name]["lastUpdated"])
	data = mainData["ed"]["data"][encId][name]["data"]
	
	if dataFreshness == None:
		return data

	if lastUpdate + dataFreshness < now:
		return 2

	return data


if __name__ == '__main__':
	print("This is a lib, it is not supposed to run as main.")
	logger.MAINPREFIX = ""
	logger.INFO = True

	# Doing tests here...
	pass
