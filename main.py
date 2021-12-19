# fnf-to-sm.py
# FNF to SM converter
# Copyright (C) 2021 shockdude

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <https://www.gnu.org/licenses/>.

# Built from the original chart-to-sm.js by Paturages, released under GPL3 with his permission

import re
import json
import math
import sys
import os

VERSION = "v0.1.2"

SM_EXT = ".sm"
SSC_EXT = ".ssc"
FNF_EXT = ".json"

DIFF_LIST = ["Easy", "Hard"]

# stepmania editor's default note precision is 1/192
MEASURE_TICKS = 192
BEAT_TICKS = 48
# fnf step = 1/16 note
STEP_TICKS = 12

NUM_COLUMNS = 8

SM_DIFFS = ["Beginner", "Easy", "Medium", "Hard", "Insane", "Challenge", "Edit"]

# borrowed from my Sharktooth code
class TempoMarker:
	def __init__(self, bpm, tick_pos, time_pos):
		self.bpm = float(bpm)
		self.tick_pos = tick_pos
		self.time_pos = time_pos

	def getBPM(self):
		return self.bpm

	def getTick(self):
		return self.tick_pos
		
	def getTime(self):
		return self.time_pos
	
	def timeToTick(self, note_time):
		return int(round(self.tick_pos + (float(note_time) - self.time_pos) * MEASURE_TICKS * self.bpm / 240000))
		
	def tickToTime(self, note_tick):
		return self.time_pos + (float(note_tick) - self.tick_pos) / MEASURE_TICKS * 240000 / self.bpm

# compute the maximum note index step per measure
def measure_gcd(num_set, MEASURE_TICKS):
	d = MEASURE_TICKS
	for x in num_set:
		d = math.gcd(d, x)
		if d == 1:
			return d
	return d;

tempomarkers = []

# helper functions for handling global tempomarkers 
def timeToTick(timestamp):
	for i in range(len(tempomarkers)):
		if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTime() > timestamp:
			return tempomarkers[i].timeToTick(timestamp)
	return 0
			
def tickToTime(tick):
	for i in range(len(tempomarkers)):
		if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTick() > tick:
			return tempomarkers[i].tickToTime(tick)
	return 0.0

def tickToBPM(tick):
	for i in range(len(tempomarkers)):
		if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTick() > tick:
			return tempomarkers[i].getBPM()
	return 0.0

def get_songname(infile):
	with open(infile, "r") as chart:
		chart_json = json.loads(chart.read().strip('\0'))
		return chart_json["song"]["song"]

def fnf_to_sm(infile, outfile=None):
	chart_jsons = []
	
	# given a normal difficulty .json,
	# try to detect all 3 FNF difficulties if possible
	infile_name, infile_ext = os.path.splitext(infile)
	
	def loadDiff(name, diff):
		if os.path.isfile(name):
			with open(name, "r") as chartfile:
				chart_json = json.loads(chartfile.read().strip('\0'))
				chart_json["diff"] = diff
				chart_jsons.append(chart_json)

	loadDiff(infile, "Medium")
		
	for i in DIFF_LIST:
		filename = infile_name + "-" + i.lower() + FNF_EXT
		loadDiff(filename, i)

	# for each fnf difficulty
	sm_header = ''
	sm_notes = ''
	for chart_json in chart_jsons:
# 		song = chart_json["song"]
# 		song_name = song["song"]
# 		try:
# 			song_notes = chart_json["notes"]
# 			song_bpm = chart_json["bpm"]
# 		except KeyError:
# 			song_notes = song["notes"]
# 			song_bpm = song["bpm"]
# 		num_sections = len(song_notes)
# 		# build sm header if it doesn't already exist
# 		if len(sm_header) == 0:
		song_notes = chart_json["song"]["notes"]
		num_sections = len(song_notes)
		# build sm header if it doesn't already exist
		if len(sm_header) == 0:
			song_name = chart_json["song"]["song"]
			song_bpm = chart_json["song"]["bpm"]
			
			fart = outfile if outfile is not None else song_name

			print("Converting {} to {}.sm".format(infile, fart))
			# build tempomap
			bpms = "#BPMS:"
			current_bpm = None
			current_tick = 0
			current_time = 0.0
			for i in range(num_sections):
				section = song_notes[i]
					
				if section.get("changeBPM", 0) != 0:
					section_bpm = float(section["bpm"])
				elif current_bpm == None:
					section_bpm = song_bpm
				else:
					section_bpm = current_bpm
				if section_bpm != current_bpm:
					tempomarkers.append(TempoMarker(section_bpm, current_tick, current_time))
					bpms += "{}={},".format(i*4, section_bpm)
					current_bpm = section_bpm

				# each step is 1/16
				section_num_steps = section["lengthInSteps"]
				# default measure length = 192
				section_length = STEP_TICKS * section_num_steps
				time_in_section = 15000.0 * section_num_steps / current_bpm

				current_time += time_in_section
				current_tick += section_length

			# add semicolon to end of BPM header entry
			bpms = bpms[:-1] + ";\n"

			# write .sm header
			sm_header = "#TITLE:{}\n".format(song_name)
			sm_header += "#MUSIC:{}.ogg;\n".format(song_name)
			sm_header += bpms

		notes = {}
		last_note = 0
		diff_value = 1
		dance_single = True
		# convert note timestamps to ticks
		if dance_single is True:
			NUM_COLUMNS = 4
		else:
			NUM_COLUMNS = 8
		for i in range(num_sections):
			section = song_notes[i]
			section_notes = section["sectionNotes"]
			#0 1 2 3, 4 5 6 7
			# seen = set()
			# ticks = [x[0] for x in section_notes]
			# dupticks = [x for x in ticks if x in seen or seen.add(x)]
			#print(f"duet or jump at {list(dupticks)}\n{ticks}")
			for section_note in section_notes:
				tick = timeToTick(section_note[0])
				note = section_note[1]
				note = int(note)

				# hasDuetOrJump = (section_note[0] in dupticks)

				# tricky compability
				ismine = False
				if note > 7:
					ismine = True
				note = note % 8

				if section["mustHitSection"]:
						note = (note + 4) % 8

				if dance_single is True:
					notes_arr = [x[1] % 8 for x in section_notes]
					val_arr = [x >= 4 for x in notes_arr]
					if len(val_arr) <= 0:
						score = 100
					else:
						score = (val_arr.count(True)/len(val_arr))*100
					# print(f"{val_arr.count(True)} out of {len(val_arr)} ({score}%)")
					if score > 0:
						continue
					note = note%4

				length = section_note[2]
				
				# Initialize a note for this tick position
				if tick not in notes:
					notes[tick] = [0]*NUM_COLUMNS

				if ismine:
					notes[tick][note] = "M"
				else:
					if length == 0:
						notes[tick][note] = 1
					else:
						notes[tick][note] = 2
						# 3 is "long note toggle off", so we need to set it after a 2
						long_end = timeToTick(section_note[0] + section_note[2])
						if long_end not in notes:
							notes[long_end] = [0]*NUM_COLUMNS
						notes[long_end][note] = 3
						if last_note < long_end:
							last_note = long_end
				if last_note <= tick:
					last_note = tick + 1

		if len(notes) > 0:
			# write chart & difficulty info
			sm_notes += "\n"
			sm_notes += "#NOTES:\n"
			if dance_single:
				sm_notes += "	  dance-single:\n"
			else:
				sm_notes += "	  dance-double:\n"
			sm_notes += "	  :\n"
			sm_notes += "	  {}:\n".format(chart_json["diff"]) # e.g. Challenge:
			sm_notes += "	  {}:\n".format(diff_value)
			sm_notes += "	  :\n" # empty groove radar

			# ensure the last measure has the correct number of lines
			if last_note % MEASURE_TICKS != 0:
				last_note += MEASURE_TICKS - (last_note % MEASURE_TICKS)

			# add notes for each measure
			for measureStart in range(0, last_note, MEASURE_TICKS):
				measureEnd = measureStart + MEASURE_TICKS
				valid_indexes = set()
				for i in range(measureStart, measureEnd):
					if i in notes:
						valid_indexes.add(i - measureStart)
				
				noteStep = measure_gcd(valid_indexes, MEASURE_TICKS)

				for i in range(measureStart, measureEnd, noteStep):
					if i not in notes:
						sm_notes += '0'*NUM_COLUMNS + '\n'
					else:
						for digit in notes[i]:
							sm_notes += str(digit)
						sm_notes += '\n'

				if measureStart + MEASURE_TICKS == last_note:
					sm_notes += ";\n"
				else:
					sm_notes += ',\n'

	# output simfile
	with open("{}.sm".format(fart), "w") as outfile:
		outfile.write(sm_header)
		if len(sm_notes) > 0:
			outfile.write(sm_notes)

# get simple header tag value
def get_tag_value(line, tag):
	tag_re = re.compile("#{}:(.+)\\s*;".format(tag))
	re_match = tag_re.match(line)
	if re_match != None:
		value = re_match.group(1)
		return value
	# try again without a trailing semicolon
	tag_re = re.compile("#{}:(.+)\\s*".format(tag))
	re_match = tag_re.match(line)
	if re_match != None:
		value = re_match.group(1)
		return value
	return None

# parse the BPMS out of a simfile
def parse_sm_bpms(bpm_string):
	sm_bpms = bpm_string.split(",")
	bpm_re = re.compile("(.+)=(.+)")
	for sm_bpm in sm_bpms:
		re_match = bpm_re.match(sm_bpm)
		if re_match != None and re_match.start() == 0:
			current_tick = int(round(float(re_match.group(1)) * BEAT_TICKS))
			current_bpm = float(re_match.group(2))
			current_time = tickToTime(current_tick)
			tempomarkers.append(TempoMarker(current_bpm, current_tick, current_time))

def sm_to_fnf(infile, diff="challenge", duet=False):
	title = "Simfile"
	fnf_notes = []
	section_number = 0
	offset = 0
	with open(infile, "r") as chartfile:
		line = chartfile.readline()
		while len(line) > 0:
			value = get_tag_value(line, "TITLE")
			if value != None:
				title = value
				line = chartfile.readline()
				continue
			value = get_tag_value(line, "OFFSET")
			if value != None:
				offset = float(value) * 1000
				line = chartfile.readline()
				continue
			value = get_tag_value(line, "BPMS")
			if value != None:
				parse_sm_bpms(value)
				line = chartfile.readline()
				continue

			# regex for a sm note row
			notes_re = re.compile("^[\\dM][\\dM][\\dM][\\dM]$")
			# TODO support SSC
			if line.strip() == "#NOTES:":
				line = chartfile.readline()
				isDouble = (line.strip() == "dance-double:")
				notes_re = re.compile("^[\\dM][\\dM][\\dM][\\dM][\\dM][\\dM][\\dM][\\dM]$") if isDouble else re.compile("^[\\dM][\\dM][\\dM][\\dM]$") 
				if (line.strip() != "dance-single:") and (not isDouble):
					line = chartfile.readline()
					continue

				chartfile.readline()
				line = chartfile.readline()
				
				# TODO support difficulties other than Challenge
				if line.strip().lower() != "{}:".format(diff):
				#if line.strip() != "Hard:":
					line = chartfile.readline()
					continue
				chartfile.readline()
				chartfile.readline()
				line = chartfile.readline()
				tracked_holds = {} # for tracking hold notes, need to add tails later
				while line.strip()[0] != ";":
					measure_notes = []
					while line.strip()[0] not in (",",";"):
						if notes_re.match(line.strip()) != None:
							measure_notes.append(line.strip())
						line = chartfile.readline()
					
					# for ticks-to-time, ticks don't have to be integer :)
					ticks_per_row = float(MEASURE_TICKS) / len(measure_notes)
					fnf_section = {}
					fnf_section["lengthInSteps"] = 16
					fnf_section["bpm"] = tickToBPM(section_number * MEASURE_TICKS)
					if len(fnf_notes) > 0:
						fnf_section["changeBPM"] = fnf_section["bpm"] != fnf_notes[-1]["bpm"]
					else:
						fnf_section["changeBPM"] = False
					fnf_section["mustHitSection"] = True
					fnf_section["typeOfSection"] = 0
					
					if isDouble:
						sectionRequired = False
						opponentNotes = 0
						playerNotes = 0
						for i in measure_notes:
							opponentNotes += len(i[:4].replace("0", ""))
							playerNotes += len(i[4:].replace("0", ""))
						if opponentNotes != 0:
							percentage = (playerNotes/opponentNotes)
							if percentage > 0.5:
								sectionRequired = True
						else:
							sectionRequired = True
						fnf_section["mustHitSection"] = sectionRequired
						if sectionRequired: # If sectionRequired that means player1 is now on the left side instead of the right. Reverse measure_notes
							for i in range(len(measure_notes)):
								leftSide = measure_notes[i][:4]
								rightSide = measure_notes[i][4:]
								measure_notes[i] = rightSide + leftSide

					if duet is True and isDouble is False:
						for i in range(len(measure_notes)):
							measure_notes[i] = measure_notes[i] + measure_notes[i]

					section_notes = []
					for i in range(len(measure_notes)):
						notes_row = measure_notes[i]
						for j in range(len(notes_row)):
							if notes_row[j] in ("1","2","4"):
								note = [tickToTime(MEASURE_TICKS * section_number + i * ticks_per_row) - offset, j, 0]
								section_notes.append(note)
								if notes_row[j] in ("2","4"):
									tracked_holds[j] = note
							# hold tails
							elif notes_row[j] == "3":
								if j in tracked_holds:
									note = tracked_holds[j]
									del tracked_holds[j]
									note[2] = tickToTime(MEASURE_TICKS * section_number + i * ticks_per_row) - offset - note[0]
					
					fnf_section["sectionNotes"] = section_notes
					
					section_number += 1
					fnf_notes.append(fnf_section)
					
					# don't skip the ending semicolon
					if line.strip()[0] != ";":
						line = chartfile.readline()
			
			line = chartfile.readline()
			
	# assemble the fnf json
	cool = title if title is not None else "Blammed"
	chart_json = {}
	chart_json["song"] = {}
	chart_json["song"]["song"] = cool
	# chart_json["song"]["song"] = "Blammed"
	chart_json["song"]["notes"] = fnf_notes
	chart_json["song"]["bpm"] = tempomarkers[0].getBPM()
	chart_json["song"]["sections"] = 0
	chart_json["song"]["needsVoices"] = False
	chart_json["song"]["player1"] = "bf"
	chart_json["song"]["player2"] = "pico"
	chart_json["song"]["sectionLengths"] = []
	chart_json["song"]["speed"] = 2.0
	
	#with open("{}.json".format(title), "w") as outfile:
	with open("{}.json".format(cool), "w") as outfile:
		json.dump(chart_json, outfile)
	print("Converted {} to {}.json".format(infile, cool))

def usage():
	print("FNF SM converter")
	print("Usage: {} [chart_file]".format(sys.argv[0]))
	print("where [chart_file] is a .json FNF chart or a .sm simfile")
	sys.exit(1)

def main():
	if len(sys.argv) < 2:
		print("Error: not enough arguments")
		usage()
	
	infile = sys.argv[1]
	if len(sys.argv) < 3:
		diff = None
	else:
		diff = sys.argv[2]
	infile_name, infile_ext = os.path.splitext(os.path.basename(infile))
	if infile_ext == FNF_EXT:
		fnf_to_sm(infile)
	elif infile_ext == SM_EXT:
		sm_to_fnf(infile, diff, True)
	else:
		print("Error: unsupported file {}".format(infile))
		usage()

if __name__ == "__main__":
	main()
