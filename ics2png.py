import arrow
import random

import ics
from PIL import Image, ImageDraw, ImageFont


# Constants
## Image size
cellWidth = 200
cellHeight = 120

firstHour = 8
columns = 14 # Number of day (starting by Monday)
rows = 10 # Number of hour (starting by firstHour)

topMargin = 50
leftMargin = 100

## Colors
backgroundColor = "#313338"  # Discord background
headerColor = "#fff"  # White
textColor = "#000"  # Black

## Fonts
fontName = "firacode.ttf"

headerSize = 32
headerFont = ImageFont.truetype(fontName, size=headerSize)

eventSize = round(headerSize / 2)
eventFont = ImageFont.truetype(fontName, size=eventSize)

descriptionSize = round(headerSize / 8 * 3)
descriptionFont = ImageFont.truetype(fontName, size=descriptionSize)

# temporary
colors={'MATHEMATIQUES': (123, 181, 70), 'ANGLAIS LV1': (230, 77, 209), 'Permanence': (72, 158, 183), 'PASTORALE': (180, 204, 40), 'ED.PHYSIQUE & SPORT.': (242, 253, 15), 'SCIENCES PHYSIQUES': (6, 24, 94), 'HIST-GEO/ED.MOR.CIV.': (152, 20, 46), 'FRANCAIS': (225, 255, 153), 'TECHNOLOGIE': (27, 62, 242), 'Classe libérée': (28, 157, 210), 'ARTS PLASTIQUES': (87, 192, 222), 'SCIENCES VIE & TERRE': (169, 121, 196), 'EDUCATION MUSICALE': (4, 121, 73), 'ALLEMAND LV1': (90, 96, 245), 'Heure de vie de classe': (28, 216, 20)}


# Functions
def drawGrid(draw: ImageDraw, onlyImportant: bool = False) -> None:
	"""Draw the grid
	if onlyImportant is set to True, it wont draw horizontal lines"""
	# Vertical lines
	draw.line([(leftMargin, 0), (leftMargin, height)], fill = "#fff", width = 3)
	for column in range(1, columns):
		draw.line([(leftMargin + cellWidth * column, 0), (leftMargin + cellWidth * column, height)], fill = "#7f7f7f", width = 3)

	# Horizontal lines
	draw.line([(0, topMargin), (width, topMargin)], fill = "#fff", width = 3)
	if not onlyImportant:
		for row in range(1, rows):
			draw.line([(0, topMargin + cellHeight * row),  (width, topMargin + cellHeight * row)], fill = "#7f7f7f", width = 3)

def drawHeaders(draw: ImageDraw, day: arrow.Arrow) -> None:
	"""Draw the headers like days and hours
	day determine the week to use (starting by Monday)"""
	# Top headers (Mon 1 Jan)
	date = getWeekSchedule(day)[0]
	for column in range(columns):
		header = date.format("ddd D MMM")
		length = draw.textlength(header, font=headerFont)

		# Compute offset
		xOffset = cellWidth * column + leftMargin
		yOffset = 0

		# Center text
		x = xOffset + (200 - length) // 2
		y = yOffset + (topMargin - headerSize) // 2

		draw.text((x, y), header, fill=headerColor, font=headerFont)

		date = date.shift(days = 1)

	# Left headers (12h00)
	for row in range(rows):
		draw.text((0, topMargin + cellHeight * row), f"{firstHour + row}h00", fill=headerColor, font=headerFont)

def getWeekSchedule(date: arrow.Arrow) -> tuple:
	"""Return the begin of the week of given date (Monday) and the end of the planning (determined by column number)"""
	begin_week = date.shift(days = -date.weekday())
	end_week = begin_week.shift(days = columns, seconds = -1)

	return (begin_week, end_week)

def getWeekEvents(date: arrow.Arrow, inputx: str = "2nde.ics") -> list:
	"""Store every event in the planning period in an array
	date: date of the planning
	inputx: ics input file"""

	# Parse the .ics file
	calendar_file = open(inputx, "r")
	calendar = ics.Calendar(calendar_file.read())
	calendar_file.close()

	# Determine week dates
	begin_week, end_week = getWeekSchedule(date)

	eventsSorted = sorted(list(calendar.events))
	weekEvents = []
	for event in eventsSorted: # Keep only event in week
		if event.begin > begin_week and event.end < end_week: # Check if event ENTIRELY in week
			index = (event.begin - begin_week).days

			if len(weekEvents) <= index: [weekEvents.append([]) for x in range(index - len(weekEvents) + 1)] # weekEvents += (index - len(weekEvents) + 1) * [[]] # Doesnt work idk why...

			event.begin = event.begin.to("Europe/Paris")
			event.end = event.end.to("Europe/Paris")

			weekEvents[index] += [event] # Sort event by day

	return weekEvents

def drawPlanning(draw: ImageDraw, events: list, day: arrow.Arrow) -> None:
	"""Draw events from list given by getWeekEvents() with draw draw and day day"""
	for i in range(len(events)): # Day after day
		begin_week = getWeekSchedule(day)[0]
		xOffset = cellWidth * i + leftMargin
		for event in events[i]: # Event after event

			if (event.begin.hour < 7) or (event.end.hour > 19): # Skip event that wont be rendered right
				continue

			# temporary (debug)
			if event.name not in colors: colors[event.name] = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
			
			scale = (height - topMargin) / rows / 60

			startY = ((event.begin.hour - 8) * 60 + event.begin.minute) * scale + topMargin
			endY = ((event.end.hour - 8) * 60 + event.end.minute) * scale + topMargin-1
			eventMargin = 3 # Dont make the event stick to the lines

			# Good luck understanding this line :)   Thats not very difficult but long... sorry ^^'
			draw.rounded_rectangle([(xOffset + eventMargin + 2, startY), (xOffset + cellWidth - eventMargin - 2, endY)], fill=colors[event.name], radius=10)

			textPadding = 3
			desc = event.description + "\n" + event.location # Give a thing like : "Meet someone\nsomewhere"
			draw.text((xOffset + eventMargin + textPadding, startY + textPadding), event.name, fill=textColor, font=eventFont)
			draw.text((xOffset + eventMargin + textPadding, startY + textPadding + eventSize), desc, fill=textColor, font=descriptionFont)

def drawImage(day, outputPath: str = "output") -> str:
	"""Draw entire planning"""
	if day == None:
		day = arrow.now()
	else:
		day = arrow.get(day)

	computeValues()
	# Create an image
	image = Image.new('RGB', (width, height), backgroundColor)
	draw = ImageDraw.Draw(image)

	drawGrid(draw)
	drawPlanning(draw, getWeekEvents(day), day)
	drawGrid(draw, onlyImportant = True)
	drawHeaders(draw, day)

	# Save the image
	if not outputPath.endswith(".png"):
		outputPath += ".png"

	image.save(outputPath)
	return outputPath

def computeValues():
	global columns, firstHour, rows, width, leftMargin, cellWidth, height, topMargin, cellHeight
	# Checkup
	columns = min(columns, 21) # Set your custom limit
	firstHour = min(max(0, firstHour), 24)
	if rows + firstHour > 24: rows = 24 - firstHour

	# Last setup
	width = leftMargin + cellWidth * columns
	height = topMargin + cellHeight * rows

if __name__ == '__main__':
	today = arrow.get(2022, 11, 30) # temporary
	drawImage(today)
