import requests
from defusedxml import ElementTree as xml
import urllib
import re
import csv
import datetime
from ast import literal_eval


# Dictionaries of states
states = [
	{'name': 'Alabama', 'code': 'AL'},
	{'name': 'Alaska', 'code': 'AK'},
	{'name': 'Arizona', 'code': 'AZ'},
	{'name': 'Arkansas', 'code': 'AR'},
	{'name': 'California', 'code': 'CA'},
	{'name': 'Colorado', 'code': 'CO'},
	{'name': 'Connecticut', 'code': 'CT'},
	{'name': 'Delaware', 'code': 'DE'},
	{'name': 'Florida', 'code': 'FL'},
	{'name': 'Georgia', 'code': 'GA'},
	{'name': 'Hawaii', 'code': 'HI'},
	{'name': 'Idaho', 'code': 'ID'},
	{'name': 'Illinois', 'code': 'IL'},
	{'name': 'Indiana', 'code': 'IN'},
	{'name': 'Iowa', 'code': 'IA'},
	{'name': 'Kansas', 'code': 'KS'},
	{'name': 'Kentucky', 'code': 'KY'},
	{'name': 'Louisiana', 'code': 'LA'},
	{'name': 'Maine', 'code': 'ME'},
	{'name': 'Maryland', 'code': 'MD'},
	{'name': 'Massachusetts', 'code': 'MA'},
	{'name': 'Michigan', 'code': 'MI'},
	{'name': 'Minnesota', 'code': 'MN'},
	{'name': 'Mississippi', 'code': 'MS'},
	{'name': 'Missouri', 'code': 'MO'},
	{'name': 'Montana', 'code': 'MT'},
	{'name': 'Nebraska', 'code': 'NE'},
	{'name': 'Nevada', 'code': 'NV'},
	{'name': 'New Hampshire', 'code': 'NH'},
	{'name': 'New Jersey', 'code': 'NJ'},
	{'name': 'New Mexico', 'code': 'NM'},
	{'name': 'New York', 'code': 'NY'},
	{'name': 'North Carolina', 'code': 'NC'},
	{'name': 'North Dakota', 'code': 'ND'},
	{'name': 'Ohio', 'code': 'OH'},
	{'name': 'Oklahoma', 'code': 'OK'},
	{'name': 'Oregon', 'code': 'OR'},
	{'name': 'Pennsylvania', 'code': 'PA'},
	{'name': 'Rhode Island', 'code': 'RI'},
	{'name': 'South Carolina', 'code': 'SC'},
	{'name': 'South Dakota', 'code': 'SD'},
	{'name': 'Tennessee', 'code': 'TN'},
	{'name': 'Texas', 'code': 'TX'},
	{'name': 'Utah', 'code': 'UT'},
	{'name': 'Vermont', 'code': 'VT'},
	{'name': 'Virginia', 'code': 'VA'},
	{'name': 'Washington', 'code': 'WA'},
	{'name': 'West Virginia', 'code': 'WV'},
	{'name': 'Wisconsin', 'code': 'WI'},
	{'name': 'Wyoming', 'code': 'WY'},
	{'name': 'District of Columbia', 'code': 'DC'},
	{'name': 'Puerto Rico', 'code': 'PR'}
]


# Class to store data entries
class Entry:

	def __init__(self, document_data=''):
		if document_data != '':
			self.document = document_data['id']
			self.congress = document_data['congress']
			self.committee = document_data['comm']
			self.subcommittee = document_data['subcomm']
			self.title = document_data['title']
			self.date = document_data['date']

			self.name = None
			self.state = None
			self.role = None

			self.text = ''

	def participant(self, participant_data):
		self.name = participant_data['name']
		self.state = participant_data['state-code']
		self.role = participant_data['role']

	def participant_manual(self, name, state, role):
		self.name = name
		self.state = state
		self.role = role

	def append_text(self, paragraph):
		self.text += ' ' + paragraph

	def data(self):
		data = {'document': self.document, 'congress': self.congress, 'committee': self.committee, \
				'subcommittee': self.subcommittee, 'title': self.title, 'date': self.date, \
				'name': self.name, 'state': self.state, 'role': self.role, 'text': self.text}
		
		return data
		
	def keys(self):
		return {'document': '', 'congress': '', 'committee': '', \
				'subcommittee': '', 'title': '', 'date': '', \
				'name': '', 'state': '', 'role': '', 'text': ''}.keys()
	
	def blank_participant(self):
		return {'name': '', 'role': '', 'ln': '', 'state': '', 'state-code': ''}


# Class to track all data entries
class Entries:

	def __init__(self):
		self.list = []
		self.discard = True

	def add_new_speaker(self, speaker, data, paragraph=''):
		self.discard = False
		entry = Entry(data)
		entry.participant(speaker)
		if paragraph != '':
			entry.append_text(paragraph)
		self.list.append(entry)
	
	def append_paragraph(self, paragraph):
		if not self.discard:
			self.list[-1].append_text(paragraph)

	def discard(self):
		self.discard = True

	def get(self):
		return self.list
	
	def clean(self):
		for entry in self.list:
			if entry.text == '' or entry.text.isspace():
				del entry


# Reads the API key from a txt file
def get_api_key():
	with open('API Key.txt', mode='r') as f:
		api_key = f.read()

	return api_key


# Creates a url returning a list of documents for the specified Congress
def create_list_url(congress, offset_mark='%2A'):
	api_key = get_api_key()

	url = "https://api.govinfo.gov/collections/CHRG/2017-01-01T00%3A00%3A00Z?pageSize=1000&congress={}\
		&docClass=hhrg&offsetMark={}&api_key={}".format(congress, offset_mark, api_key)

	return url


# Makes a request to a given URL and returns the result
def make_request(url):
	response = requests.get(url)

	print(response.status_code)
	if response.status_code != 200:
		raise Exception(
			"Request returned an error: {} {}".format(response.status_code, response.text)
		)
	else:
		return response.json()


# Requests a list of document IDs and returns it
def get_list(congress):
	documents = list()

	url = create_list_url(congress)
	json = make_request(url)
	
	for package in json['packages']:
		documents.append(package['packageId'])

	api_key = get_api_key()
	while json['nextPage'] != None:
		url = "{}&api_key={}".format(json['nextPage'], api_key)
		json = make_request(url)

		for package in json['packages']:
			documents.append(package['packageId'])

	return documents


# Returns the corresponding document for the given ID and document type
def get_page(document_id, type='html'):
	congress = document_id[5:8]
	id = "{}-{}".format(document_id[-5:-3], document_id[-3:])

	url = "https://www.govinfo.gov/link/chrg/{}/{}?link-type={}".format(congress, id, type)

	response = requests.get(url, allow_redirects=True, stream=True)

	if response.status_code != 200:
		print('Response status code: ' + str(response.status_code))
		print("Couldn't read document {}".format(document_id))
		return None
	else:
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) \
					AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"}
		req = urllib.request.Request(response.url, headers=headers)
		with urllib.request.urlopen(req) as f:
			data = f.read()

		return data
	

# Extracts data from XML files corresponding to the given document ID
def process_xml_file(document_id):
	PREFIX = '{http://www.loc.gov/mods/v3}'

	congress = title = committee = subcommittee = ''
	participants = []
	dates = []
	data = []

	page = get_page(document_id, type='mods')
	root = xml.fromstring(page)

	for child in root:

		# Get title of document
		if child.tag == PREFIX + 'titleInfo' and len(child) > 0:
			title = child[0].text

		elif child.tag == PREFIX + 'extension':
			for detail in child:

				name = role = last_name = state = state_code = ''

				# Get congress
				if detail.tag == PREFIX + 'congress':
					congress = detail.text

				# Get date
				if detail.tag == PREFIX + 'heldDate':
					dates.append(detail.text)

				# Get committee data
				elif detail.tag == PREFIX + 'congCommittee':
					for comm in detail:
						if comm.tag == PREFIX + 'name' and \
							comm.attrib['type'] == 'authority-standard':
							committee = comm.text
						elif comm.tag == PREFIX + 'subCommittee':
							subcommittee = comm[0].text

				# Get witnesses
				elif detail.tag == PREFIX + 'witness':
					name = detail.text
					role = 'witness'
					last_name = name[:name.find(',')]
					names = last_name.split()
					if len(names) > 1:
						last_name = names[-1]

					participants.append({'name': name, 'role': role, \
										 'ln': last_name, 'state': state, 'state-code': state_code})

				# Get Congresspersons
				elif detail.tag == PREFIX + 'congMember':
					role = 'member'
					state_code = detail.attrib['state']
					for st in states:
						if st['code'] == state_code:
							state = st['name']
					for nametag in detail:
						if nametag.attrib['type'] == 'authority-lnf':
							name = nametag.text
							last_name = nametag.text[:nametag.text.find(',')]

					participants.append({'name': name, 'role': role, \
										 'ln': last_name, 'state': state, 'state-code': state_code})

	for date in dates:
		data.append({'id': document_id, 'congress': congress, 'title': title, 'date': date, \
				'comm': committee, 'subcomm': subcommittee})

	return data, participants


# Helper function to prompt the user to manually enter a participant
def participant_prompt(participants, document_id):
	correct = False
	while not correct:

		congress = document_id[5:8]
		id = "{}-{}".format(document_id[-5:-3], document_id[-3:])

		url = "https://www.govinfo.gov/link/chrg/{}/{}?link-type={}".format(congress, id, 'html')

		print("Document url: {}".format(url))

		ln_in = input("Enter last name: ")
		state_code_in = input("Enter state code (e.g. TX): ")

		# Check for matches
		for participant in participants:
			if ln_in.casefold() == participant['ln'].split()[-1].casefold() and \
				state_code_in == participant['state-code']:
				print("Found potential match: {}".format(participant))
				# TODO: Add loop to check for invalid input
				confirmation = ''
				while confirmation != 'y' and confirmation != 'n':
					confirmation = input("Is this correct? (y/n) ")
				if confirmation == 'y': # Found participant
					return participant
		
		# Input first name
		name_in = input("Enter first name: ")
		full_name = ln_in + ', ' + name_in

		# Input role
		if state_code_in == '':
			role_in = 'witness'
		else:
			role_in = 'member'

		# Find full state name
		state_name = ''
		for state in states:
			if state['code'] == state_code_in:
				state_name = state['name']

		# Confirm information
		print("Confirm the following information:")
		if role_in == 'member':
			print("Representative " + full_name + " of " + state_name)
		else:
			print(full_name + ", role: " + role_in)
		
		confirmed = False
		while not confirmed:
			confirmation = input("y/n: ")
			if confirmation == 'y':
				correct = True
				confirmed = True
			elif confirmation == 'n':
				confirmed = True
				
	participant = {'name': full_name, 'role': role_in, 'ln': ln_in, \
		'state': state_name, 'state-code': state_code_in}

	return participant


# Prompts the user to confirm if a potential match found is correct
def potential_match_prompt(speaker, paragraph):
	print("Possible match found: {}".format(speaker))
	print("for potential next speech: {}".format(paragraph[:200]))
	confirmation = ''
	while confirmation != 'y' and confirmation != 'n':
		confirmation = input("Is this the correct speaker? (y/n) ")
	if confirmation == 'y':
		return True
	else:
		return False
	

# Helper function to check a phrase for a participant and return the participant
# start_of_string is a flag to make the function only check the form <title>. <last-name>.
def get_participant(paragraph, participants, document_id, possible_speakers, start_of_string=False):

	words = paragraph.split()
	
	# Check for names
	last_name = ''
	matches = []

	# If not a statement
	if len(words) <= 3 or (words[1][-1] != '.' and words[2][-1] != '.' and words[3][-1] != '.'):
		return ('', -1) # Signal not a statement

	# Check for typical speaker string form (i.e. "Mr. Gosar. Statement...")
	if start_of_string:
		
		# Two word match
		if words[1][-1] == '.' or (words[2][-2:] == '].' and words[2][0] == '['):
			if words[1][-1] == '.':
				last_name = words[1][:-1]
			else:
				last_name = words[1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold():
					matches.append(participant)
				if len(participant['ln'].split()) > 1 and \
					participant['ln'].split()[-1].casefold() == last_name.casefold():
					matches.append(participant)

		# Three word match
		elif words[2][-1] == '.':
			last_name = words[1] + ' ' + words[2][:-1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold():
					matches.append(participant)

			# If no matches found, check just last word
			if len(matches) == 0:
				for participant in participants:
					if participant['ln'].casefold() == words[2][-1].casefold():
						matches.append(participant)

		# <Last name> of <state>
		elif len(words) > 3 and words[2] == 'of':
			last_name = words[1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold() and \
					participant['state'].casefold() == words[3].casefold():
					matches.append(participant)

		# If no matches found, check potential speakers file
		if len(matches) == 0:
			for speaker in possible_speakers:
				if speaker['ln'].casefold() == last_name.casefold():
					if potential_match_prompt(speaker, paragraph):
						participants.append(speaker)
						return (speaker, len(speaker['ln'].split())+1)

	# Other types of statements
	else:
		for word in words:

			# Remove commas at the end of words
			if word[-1] == ',':
				word = word[:-1]

			# Check all participants
			for participant in participants:
				if word.casefold() == participant['ln'].split()[-1].casefold():
					matches.append(participant)

			# If no matches found, check potential speakers file
			if len(matches) == 0:
				for speaker in possible_speakers:
					if speaker['ln'].split()[-1].casefold() == word.casefold():
						if potential_match_prompt(speaker, paragraph):
							participants.append(speaker)
							return (speaker, len(words)-1)

	# Problems with recognizing speakers
	if len(matches) == 0: # No matches found
		
		print()
		print("WARNING: No match found for potential new speaker: {}".format(paragraph[:200]))
		confirmation = ''
		while confirmation != 'y' and confirmation != 'n':
			confirmation = input("Is this actually a new speaker? (y/n) ")
			
		# New speaker found
		if confirmation == 'y':
			speaker = participant_prompt(participants, document_id)
			exists = False
			
			# Compare manual data against existing participants
			for participant in participants:
				if participant['name'] == speaker['name']:
					exists = True
			if not exists:
				possible_speakers.append(speaker)
				participants.append(speaker)
			
			if start_of_string:
				match_len = len(speaker['ln'].split()) + 1
			else:
				match_len = len(words) - 1
			return (speaker, match_len)
		
		# Not a new speaker, add phrase to invalid speaker strings
		elif confirmation == 'n':
			return ' '.join([words[0], words[1]])
			
	elif len(matches) == 1: # One match found
		speaker = matches[0]
		if start_of_string:
			match_len = len(speaker['ln'].split()) + 1
		else:
			match_len = len(words) - 1
		return (speaker, match_len)
				
	else: # Multiple matches found
		
		print()
		print("WARNING: Multiple matches found for potential new speaker: {}".format(paragraph))
		
		# Print list of possible matches
		i = 1
		for match in matches:
			print("{} - {}".format(i, match))
			i += 1
		
		# Prompt user to select a match    
		index = -1
		while index < 0 or index >= len(matches):
			index = input("Enter the number of the correct participant: ")
			index = int(index)
		speaker = matches[index-1]
		if start_of_string:
			match_len = len(speaker['ln'].split()) + 1
		else:
			match_len = len(words) - 1
		return (speaker, match_len)


# Processes a single paragraph and returns an updated data_entry
def process_paragraph(paragraph, data, participants, chairperson, entries, possible_speakers, \
		      invalid_speaker_strings):
	new_speaker = False
	paragraph = paragraph.strip()
	words = paragraph.split()

	# Skip blank lines
	if paragraph == '':
		return entries
	
	# Skip lines without uppercase letter
	if paragraph[0].islower():
		entries.append_paragraph(paragraph)
		return entries
	
	# Make sure that the possible speaker phrase is valid
	valid = True
	for string in invalid_speaker_strings:
		if len(words) > 1 and words[0] == string[0] and words[1] == string[1]:
			if len(string) > 2 and len(words) > 2:
				if words[2] == string[2]:
					valid = False
			else:
				valid = False

	# Make a list of the possible other strings which indicate who is speaking
	chair_ids = ['The Chairman.', 'The Chairwoman.', 'The Chairperson.', 'The Chair.']
	alt_ids = ['The Clerk.']

	# Look for other chair ids
	for id in chair_ids:
		if paragraph[:len(id)].casefold() == id.casefold():

			new_speaker = True

			# If no chairperson detected
			if chairperson == {}:

				chairs = []
				with open('chairs.csv', 'r') as chairs_file:
					reader = csv.DictReader(chairs_file)
					for line in reader:
						chairs.append(line)

				for chair in chairs:
					if chair['id'] == data['id']:
						chairperson = literal_eval(chair['chair'])

				if chairperson == {}:
					print("WARNING: No chairperson found. Please manually enter the chairperson.")
					chairperson = participant_prompt(participants, data['id'])
					chairs.append({'id': data['id'], 'chair': chairperson})

					with open('chairs.csv', 'w', newline='') as chairs_file:
						writer = csv.DictWriter(chairs_file, chairs[0].keys())
						writer.writeheader()
						for chair in chairs:
							writer.writerow(chair)


			# Create a new data entry for the next speech
			entries.add_new_speaker(chairperson, data, ' '.join(words[2:]))

	# Look for alternate ids
	for id in alt_ids:
		if paragraph[:len(id)].casefold() == id.casefold():

			# Dispose of following text
			entries.discard()
			new_speaker = True

	append_paragraph = False
	# If invalid statement
	if not valid:
		pass

	# Look for statement
	elif len(words) > 1 and (words[0].casefold() == 'statement'.casefold() or \
		words[1].casefold() == 'statement'.casefold()):
		speaker = get_participant(paragraph, participants, data['id'], possible_speakers)
		"""
		matches = []
		for i in range(2, len(words)):
			word = words[i]
			if word[-1] == ',':
				word = word[:-1]

			for participant in participants:
				if word.casefold() == participant['ln'].split()[-1].casefold():
					matches.append(participant)
			
			# If no matches found, check potential speakers file
			if len(matches) == 0:
				for speaker in possible_speakers:
					if word.casefold() == speaker['ln'].split()[-1].casefold():
						print("Possible match found: {}".format(speaker))
						print("for potential statement: {}".format(paragraph))
						confirmation = ''
						while confirmation != 'y' and confirmation != 'n':
							confirmation = input("Is this the correct speaker? (y/n) ")
						if confirmation == 'y':
							matches.append(speaker)
							participants.append(speaker)
							break

		# Problems with recognizing statements
		if len(matches) == 0: # No matches found

			print()
			print("WARNING: No match found for potential statement: {}".format(paragraph))
			confirmation = ''
			while confirmation != 'y' and confirmation != 'n':
				confirmation = input("Is this actually the start of a statement? (y/n) ")

			# New speaker found
			if confirmation == 'y':
				speaker = participant_prompt(participants, data['id'])
				new_speaker = True
				exists = False
				for participant in participants:
					if participant['name'] == speaker['name']:
						exists = True
				if not exists:
					possible_speakers.append(speaker)
					participants.append(speaker)

		elif len(matches) > 1: # Multiple matches found

			print()
			print("WARNING: Multiple matches found for statement: {}".format(paragraph))

			congress = data['congress']
			id = data['id']
			url = "https://www.govinfo.gov/link/chrg/{}/{}?link-type={}".format(congress, id, 'html')
			
			# Print a list of all potential matches
			i = 1
			for match in matches:
				print("{} - {}".format(i, match))
				i += 1
			index = -1

			# User inputs correct match
			while index < 0 or index >= len(matches):
				index = input("Enter the number of the correct participant: ")
				index = int(index)
			speaker = matches[index - 1]
			new_speaker = True

		else: # One match found
			speaker = matches[0]
			new_speaker = True
		"""

	# Look for new speaker
	else:
		speaker = get_participant(paragraph, participants, data['id'], possible_speakers, True)
		append_paragraph = True	
		
		"""# Check for names
		speaker = ''
		matches = []
		potential_match = False
		match_len = 0

		# One last name
		if (len(words) > 1 and words[1][-1] == '.') or \
			(len(words) > 2 and words[2][-2:] == '].' and words[2][0] == '['):
			potential_match = True
			match_len = 2
			matches = []
			if words[1][-1] == '.':
				last_name = words[1][:-1]
			else:
				last_name = words[1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold():
					matches.append(participant)
				if len(participant['ln'].split()) > 1 and \
					participant['ln'].split()[-1].casefold() == last_name.casefold():
					matches.append(participant)

			# If no matches found, check potential speakers file
			if len(matches) == 0:
				for speaker in possible_speakers:
					if speaker['ln'].casefold() == last_name.casefold():
						print("Possible match found: {}".format(speaker))
						print("for potential next speech: {}".format(paragraph[:200]))
						confirmation = ''
						while confirmation != 'y' and confirmation != 'n':
							confirmation = input("Is this the correct speaker? (y/n) ")
						if confirmation == 'y':
							matches.append(speaker)
							participants.append(speaker)
							break

		# Two last names
		elif len(words) > 2 and words[2][-1] == '.':
			potential_match = True
			match_len = 3
			matches = []
			last_name = words[1] + ' ' + words[2][:-1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold():
					matches.append(participant)

			# If no matches found, check just last word
			for participant in participants:
				if participant['ln'].casefold() == words[2][-1].casefold():
					matches.append(participant)

			# If no matches found, check potential speakers file
			if len(matches) == 0:
				for speaker in possible_speakers:
					if speaker['ln'].casefold() == last_name.casefold():
						print("Possible match found: {}".format(speaker))
						print("for potential next speech: {}".format(paragraph))
						confirmation = ''
						while confirmation != 'y' and confirmation != 'n':
							confirmation = input("Is this the correct speaker? (y/n) ")
						if confirmation == 'y':
							matches.append(speaker)
							participants.append(speaker)
							break

			# <Last name> of <state>
		elif len(words) > 3 and words[2] == 'of':
			match_len = 4

			# Check for state match
			for state in states:
				if words[3].casefold() == state['name'].casefold():
					potential_match = True
			matches = []
			last_name = words[1]

			# Compare against all participants
			for participant in participants:
				if participant['ln'].casefold() == last_name.casefold() and \
					participant['state'].casefold() == words[3].casefold():
					matches.append(participant)

			# If no matches found, check potential speakers file
			if len(matches) == 0:
				for speaker in possible_speakers:
					if speaker['ln'].casefold() == last_name.casefold() and \
						speaker['state'].casefold() == words[3].casefold():
						print("Possible match found: {}".format(speaker))
						print("for potential next speech: {}".format(paragraph))
						confirmation = ''
						while confirmation != 'y' and confirmation != 'n':
							confirmation = input("Is this the correct speaker? (y/n) ")
						if confirmation == 'y':
							matches.append(speaker)
							participants.append(speaker)
							break

		# Problems with recognizing speakers
		if valid and len(matches) == 0 and potential_match: # No matches found
			
			print()
			print("WARNING: No match found for potential new speaker: {}".format(paragraph[:200]))
			confirmation = ''
			while confirmation != 'y' and confirmation != 'n':
				confirmation = input("Is this actually a new speaker? (y/n) ")
				
			# New speaker found
			if confirmation == 'y':
				speaker = participant_prompt(participants, data['id'])
				exists = False
				
				# Compare manual data against existing participants
				for participant in participants:
					if participant['name'] == speaker['name']:
						exists = True
				if not exists:
					possible_speakers.append(speaker)
					participants.append(speaker)
				new_speaker = True
			
			# Not a new speaker, add phrase to invalid speaker strings
			elif confirmation == 'n':
				if match_len == 2:
					invalid_speaker_strings.append([words[0], words[1]])
				else:
					invalid_speaker_strings.append([words[0], words[1], words[2]])
					
		elif len(matches) > 1: # Multiple matches found
			
			print()
			print("WARNING: Multiple matches found for potential new speaker: {}".format(paragraph))
			
			# Print list of possible matches
			i = 1
			for match in matches:
				print("{} - {}".format(i, match))
				i += 1
			
			# Prompt user to select a match    
			index = -1
			while index < 0 or index >= len(matches):
				index = input("Enter the number of the correct participant: ")
				index = int(index)
			speaker = matches[index - 1]
			new_speaker = True
			
		elif len(matches) == 1: # One match found
			speaker = matches[0]
			new_speaker = True"""

	# New speaker
	if valid and type(speaker) is not str and speaker[1] != -1:
		if append_paragraph:
			entries.add_new_speaker(speaker[0], data, ' '.join(words[speaker[1]:]))
		else:
			entries.add_new_speaker(speaker[0], data)

	# Add paragraph onto existing speaker
	else:

		# Invalid speaker phrase
		if valid and speaker[0] is str:
			invalid_speaker_strings.append(speaker)
		
		# Remove extraneous text
		while True:
			start_brace = paragraph.find('[')
			end_brace = paragraph.find(']')
			if start_brace == -1 and end_brace == -1:
				break
			elif start_brace == -1:
				paragraph = paragraph[end_brace+1:]
			elif end_brace == -1:
				paragraph = paragraph[:start_brace]
			else:
				paragraph = paragraph[:start_brace] + ' ' + paragraph[end_brace+1:]
		while True:
			start_brace = paragraph.find('<')
			end_brace = paragraph.find('>')
			if start_brace == -1 or end_brace == -1:
				break
			else:
				paragraph = paragraph[:start_brace] + ' ' + paragraph[end_brace+1:]

		if not paragraph.isupper():
			entries.append_paragraph(paragraph)

	return entries


# Given a single hearing, processes each line of the hearing and returns the list of entries
def process_hearing(content, data, participants, chairperson):

	# Look for appendicies and other unnecessary information
	re_str = re.compile(r"\n\s*(Submitted [^ ]+ by|APPENDIX|Appendix|A P P E N D I X)")
	re_match = re.search(re_str, content)
	if re_match is not None:
		appendix = content[re_match.end():]
		content = content[:re_match.start()]
	else:
		appendix = ''

	# Split the body of the text by paragraph
	paragraphs = content.split('\n')

	# Read invalid speaker strings from file
	invalid_speaker_strings = []
	with open('invalid-speaker-strings.txt', 'r') as invalid_file:
		for line in invalid_file:
			invalid_speaker_strings.append(line.split())

	# Read possible speakers from file
	possible_speakers = []
	with open('possible-speakers.csv', 'r') as speakers_file:
		reader = csv.DictReader(speakers_file)
		for line in reader:
			possible_speakers.append(line)

	entries = Entries()

	# Loop through all of the paragraphs, creating a data entry for each speech
	source = False
	report = False
	questions = False
	skip = False
	questions_from = Entry().blank_participant()
	questions_to = Entry().blank_participant()
	for paragraph in paragraphs:

		# Skip single line functionality
		if skip:
			skip = False
		
		# Look for sources
		if len(paragraph) > 20 and paragraph[:19] == '--------------------' \
			or paragraph[-20:] == '--------------------':
			if source:
				source = False
				skip = True
			else:
				source = True

		# Detect missing source end
		if source and len(paragraph) > 2 and (paragraph[:2] != r'\\' and paragraph[:2] != '--'):
			source = False

		# Look for reports or other information
		if "[The information follows:]" in paragraph:
			report = True
		
		# Detect end of report
		if "______" in paragraph:
			if report:
				report = False
			if questions:
				questions = False

		# If not a source or report, process the paragraph
		if not source and not report and not skip:

			words = paragraph.strip().split()
			words = list(map(lambda x : x[:-1] if x[-1] == ',' else x, words))

			# Look for Q&A inside the text
			if len(words) > 1 and words[0] == "Questions" and \
				words[1].casefold() == "Submitted".casefold():
				questions = True
				if words.count("to") == 0 and words.count("by") == 0:
					report = True
				elif words.count("to") > 0:
					to_flag = True
				elif words.count("by") > 0:
					to_flag = False
				
				# Check for participants
				matches = []
				for participant in participants:
					if ' ' not in participant['ln'] and participant['ln'] in words:
						matches.append(participant)
					elif ' ' in participant['ln'] and participant['ln'].split()[0] in words and \
						participant['ln'].split()[1] in words:
						matches.append(participant)
				
				# If no matches found
				if len(matches) == 0:
					print()
					print("WARNING: Cannot detect participant in: {}".format(paragraph))
					confirmation = ''
					while confirmation != 'y' and confirmation != 'n':
						confirmation = input("Is this the start of a Q&A? (y/n) ")
					if confirmation == 'n':
						questions = False
						report = True
					else:
						temp = participant_prompt(participants, data['id'])
						if to_flag:
							questions_to = temp
						else:
							questions_from = temp
				
				# If one match found
				elif len(matches) == 1:
					if to_flag:
						questions_to = matches[0]
					else:
						questions_from = matches[0]
				
				# If multiple matches found
				else:
					print()
					print("WARNING: Multiple matches found for participant: {}".format(paragraph))
					i = 1
					for match in matches:
						print("{} - {}".format(i, match))
						i += 1
					index = -1
					while index < 0 or index >= len(matches):
						index = input("Enter the number of the correct participant: ")
						index = int(index)
					if to_flag:
						questions_to = matches[index - 1]	
					else:
						questions_from = matches[index - 1]

			# Process Q&A
			if questions:
				if len(words) > 0 and (words[0] == "Question." or \
					(words[0] == "Question" and words[1][-1] == '.')):
					if words[0] == "Question.":
						prompt_len = 1
					else:
						prompt_len = 2
					entries.add_new_speaker(questions_from, data, ' '.join(words[prompt_len:]))
				elif len(words) > 0 and words[0] == "Answer.":
					entries.add_new_speaker(questions_to, data, ' '.join(words[1:]))
				else:
					entries.append_paragraph(paragraph)

			else:
				entries = process_paragraph(paragraph, data, participants, chairperson, entries, \
				   	possible_speakers, invalid_speaker_strings)
			
	# Look for Q&A in appendix
	for paragraph in appendix.split('\n'):
		pass

	# Save all invalid speaker strings
	with open('invalid-speaker-strings.txt', 'w') as invalid_file:
		for string in invalid_speaker_strings:
			line = ' '.join(string)
			invalid_file.write(line + '\n')

	# Save all possible speakers
	with open('possible-speakers.csv', 'w', newline='') as possible_speakers_file:
		writer = csv.DictWriter(possible_speakers_file, possible_speakers[0].keys())
		writer.writeheader()
		for speaker in possible_speakers:
			writer.writerow(speaker)

	entries.clean()

	return entries.get()


# Processes the text of the HTML file corresponding to the given document ID
def process_html_file(document_id, data, participants):

	raw_content = get_page(document_id)
	content = str(raw_content)

	# Fix paragraph breaks
	content = content.replace(r'\n    ', '\n')
	content = content.replace(r'\n\n', '\n')

	# Generate date strings from the dates found
	date_strings = []
	for hearing in data:
		date_list = hearing['date'].split('-')
		date_list = list(map(int, date_list))
		date = datetime.date(*date_list)
		date_string = date.strftime("%A, %B {}, %Y".format(date.day))
		date_strings.append({'str': date_string, 'data': hearing})

	# Find the first date string and separate the header of the document from the body
	first_date_re = re.compile(date_strings[0]['str'], re.IGNORECASE)
	first_date_iter = first_date_re.finditer(content)
	first_date_locations = [x for x in first_date_iter]
	if len(first_date_locations) == 0:
		print("WARNING: Unable to find start of text in document {}\n".format(document_id))
		return []
	start = first_date_locations[-1]
	heading = content[:start.start()]
	content = content[start.start():]

	# Remove '\n's
	content = content.replace(r'\n--', '\n')
	content = content.replace(r'\n', '')
	heading = heading.replace(r'\n', '\n')

	# Split document by meeting days
	if len(date_strings) > 0:
		hearings = []
		rest = content
		for date in date_strings:
			date_re = re.compile(date['str'], re.IGNORECASE)
			date_iter = date_re.finditer(content)
			date_locations = [x for x in date_iter]
			start = date_locations[-1]
			hearings.append({'data': data, 'content': '', 'location': start})
		for i in range(len(hearings)-1):
			hearings[i]['content'] = \
				content[hearings[i]['location'].end():hearings[i+1]['location'].start()]
		hearings[-1]['content'] = content[hearings[-1]['location'].end():]

	# Find the name of the chairperson of the committee
	chair_name = ''
	chair_state = ''
	lines = heading.split('\n')
	index = 0
	line_count = 0
	for line in lines:
		if len(line.split()) > 1 and (line.split()[0] == 'COMMITTEE' or ((line.split()[0] == 'HOUSE' or \
    		line.split()[0] == 'SELECT') and line.split()[1] == 'COMMITTEE')):
			line_count = 4

		if line_count > 0:
			line_count -= 1
			line = line.strip()
			line = line.split(', ')
			if len(line) > 1 and (line[1] == 'Jr.' or line[1] == 'Sr.'): # Handle 'Jr.'
				del line[1]
			if len(line) == 3:
				if line[2][:5] == 'Chair':
					chair_state = line[1]
					name_list = line[0].split()
					chair_name = name_list[-1]
					break
			elif len(line) == 2:
				if lines[index + 1].strip()[:5] == 'Chair':
					chair_state = line[1]
					name_list = line[0].split()
					chair_name = name_list[-1]
					break
		
		index += 1

	# Find the info for the chairperson of the committee
	chairperson = {}
	for participant in participants:
		if participant['state'] == chair_state and \
			participant['ln'].split()[-1].casefold() == chair_name.casefold():
			chairperson = participant

	i = 0
	entries = []
	for hearing in hearings:
		entries += process_hearing(hearing['content'], data[i], participants, chairperson)
		i += 1

	return entries


# Processes documents given a list of document IDs
def process_documents(ids, output_file):

	with open(output_file, 'w+', encoding='utf-8', newline='') as f:
		csv_writer = csv.DictWriter(f, Entry().keys())
		csv_writer.writeheader()

	for id in ids:
		congress = id[5:8]
		id_number = "{}-{}".format(id[-5:-3], id[-3:])
		url = "https://www.govinfo.gov/link/chrg/{}/{}?link-type=html".format(congress, id_number)
		print("\n\nProcessing document: {}\nUrl: {}\n".format(id, url))

		data, participants = process_xml_file(id)
		entries = process_html_file(id, data, participants)

		with open(output_file, 'a', encoding='utf-8', newline='') as f:
			csv_writer = csv.DictWriter(f, Entry().keys())

			for entry in entries:
				csv_writer.writerow(entry.data())


def main():
	# ids = get_list('115')
	id1 = 'CHRG-115hhrg33477'
	id2 = 'CHRG-117hhrg45006'
	id3 = 'CHRG-117hhrg46542' # Includes multiple hearings
	id4 = 'CHRG-115hhrg31359' # Doesn't have text
	id5 = 'CHRG-117hhrg46928' # Features sources in text
	id6 = 'CHRG-117hhrg44243' # Includes reports inside the text
	id7 = 'CHRG-117hhrg44244' # Includes questions inside the text

	process_documents([id7], 'hearing-data.csv')


if __name__ == "__main__":
	main()