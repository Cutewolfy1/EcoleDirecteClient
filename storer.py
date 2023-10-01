import json

file = "data.json"

def readJson():
	f = open(file, "r")
	result = json.load(f)
	f.close()
	return result

def writeJson(data: any):
	f = open(file, "w")
	json.dump(data, f, indent = 4, ensure_ascii = False)
	f.close()

class Storer():
	def __init__(self, name: str):
		self.name = name
		self.pull()

	def __getitem__(self, key: str): return self.data[key]
	def __setitem__(self, key: str, item: any): self.data[key] = item
	def __repr__(self): return json.dumps(self.data, indent = 4, ensure_ascii = False)

	def push(self):
		globalData = readJson()
		globalData[self.name] = self.data
		writeJson(globalData)

	def pull(self):
		globalData = readJson()
		if self.name in globalData:
			self.data = globalData[self.name]
		else:
			self.data = {}

	def delete(self):
		globalData = readJson()
		if self.name in globalData:
			del globalData[self.name]
			writeJson(globalData)
