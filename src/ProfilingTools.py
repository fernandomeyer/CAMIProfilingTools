# This is a collection of scripts that will allow manipulation of CAMI profiling files
import sys
import copy


class Profile(object):
	def __init__(self, input_file_name=None):
		# Initialize file name (if appropriate)
		self.input_file_name = input_file_name
		self._data = dict()
		# Stick in the root node just to make sure everything is consistent
		self._data["-1"] = dict()
		self._data["-1"]["rank"] = None
		self._data["-1"]["tax_path"] = list()
		self._data["-1"]["tax_path_sn"] = list()
		self._data["-1"]["abundance"] = 0
		self._data["-1"]["descendants"] = list()
		self._header = list()
		self._tax_id_pos = None
		self._rank_pos = None
		self._tax_path_pos = None
		self._tax_path_sn_pos = None
		self._abundance_pos = None
		self._eps = .0000000000000001  # This is to act like zero, ignore any lines with abundance below this quantity

		if self.input_file_name:
			self.parse_file()

	def parse_file(self):
		input_file_name = self.input_file_name
		_data = self._data
		_header = self._header
		with open(input_file_name, 'r') as read_handler:
			for line in read_handler:
				line = line.rstrip()
				if len(line) == 0:
					continue  # skip blank lines
				if line[0] == '@' and line[1] == '@':
					headers = line.strip().split()
					for header_iter in range(len(headers)):
						header = headers[header_iter]
						header = header.replace('@', '')
						if header == 'TAXID':
							tax_id_pos = header_iter
							self._tax_id_pos = tax_id_pos
						elif header == 'RANK':
							rank_pos = header_iter
							self._rank_pos = rank_pos
						elif header == 'TAXPATH':
							tax_path_pos = header_iter
							self._tax_path_pos = tax_path_pos
						elif header == 'TAXPATHSN':
							tax_path_sn_pos = header_iter
							self._tax_path_sn_pos = tax_path_sn_pos
						elif header == 'PERCENTAGE':
							abundance_pos = header_iter
							self._abundance_pos = abundance_pos
				if line[0] in ['@', '#']:
					_header.append(line)  # store data and move on
					continue
				if not all([isinstance(x, int) for x in [tax_id_pos, tax_path_pos, abundance_pos]]):
					print(
					"Appears the headers TAXID, TAXPATH, and PERCENTAGE are missing from the header (should start with line @@)")
					sys.exit(2)
				temp_split = line.split('\t')
				tax_id = temp_split[tax_id_pos].strip()
				tax_path = temp_split[tax_path_pos].strip().split("|")  # this will be a list, join up late
				abundance = float(temp_split[abundance_pos].strip())
				if isinstance(rank_pos, int):  # might not be present
					rank = temp_split[rank_pos].strip()
				if isinstance(tax_path_sn_pos, int):  # might not be present
					tax_path_sn = temp_split[tax_path_sn_pos].strip().split("|")  # this will be a list, join up later
				if tax_id in _data:  # If this tax_id is already present, add the abundance. NOT CHECKING FOR CONSISTENCY WITH PATH
					_data[tax_id]["abundance"] += abundance
					_data[tax_id]["tax_path"] = tax_path
					if isinstance(rank_pos, int):  # might not be present
						_data[tax_id]["rank"] = rank
					if isinstance(tax_path_sn_pos, int):  # might not be present
						_data[tax_id]["tax_path_sn"] = tax_path_sn
					# Find the ancestor
					if len(tax_path) <= 1:
						_data[tax_id]["ancestor"] = "-1"  # no ancestor, it's a root
						ancestor = "-1"
					else:
						ancestor = tax_path[-2]
						i = -3
						while ancestor is "" or ancestor == tax_id:  # if it's a blank or repeated, go up until finding ancestor
							ancestor = tax_path[i]
							i -= 1
						_data[tax_id]["ancestor"] = ancestor
				else:  # Otherwise populate the data
					_data[tax_id] = dict()
					_data[tax_id]["abundance"] = abundance
					_data[tax_id]["tax_path"] = tax_path
					if isinstance(rank_pos, int):  # might not be present
						_data[tax_id]["rank"] = rank
					if isinstance(tax_path_sn_pos, int):  # might not be present
						_data[tax_id]["tax_path_sn"] = tax_path_sn
					# Find the ancestor
					if len(tax_path) <= 1:
						_data[tax_id]["ancestor"] = "-1"  # no ancestor, it's a root
						ancestor = "-1"
					else:
						ancestor = tax_path[-2]
						i = -3
						while ancestor is "" or ancestor == tax_id:  # if it's a blank or repeated, go up until finding ancestor
							ancestor = tax_path[i]
							i -= 1
						_data[tax_id]["ancestor"] = ancestor
				# Create a placeholder descendant key initialized to [], just so each tax_id has a descendant key associated to it
				if "descendants" not in _data[tax_id]:  # if this tax_id doesn't have a descendant list,
					_data[tax_id]["descendants"] = list()  # initialize to empty list
				# add the descendants
				if ancestor in _data:  # see if the ancestor is in the data so we can add this entry as a descendant
					if "descendants" not in _data[ancestor]:  # if it's not present, create the descendant list
						_data[ancestor]["descendants"] = list()
					_data[ancestor]["descendants"].append(tax_id)  # since ancestor is an ancestor, add this descendant to it
				else:  # if it's not already in the data, create the entry
					_data[ancestor] = dict()
					_data[ancestor]["descendants"] = list()
					_data[ancestor]["descendants"].append(tax_id)
		return

	def write_file(self, out_file_name=None):
		if out_file_name is None:
			raise Exception
		_data = self._data
		keys = _data.keys()
		# This will be annoying to keep things in order...
		# Let's iterate on the length of the tax_path since we know that will be in there
		tax_path_lengths = max([len(_data[key]["tax_path"]) for key in keys])
		fid = open(out_file_name, 'w')
		# Write the header
		for head in self._header:
			fid.write("%s\n" % head)

		# Loop over length of tax_path and write data
		# always make the output tax_id, rank, tax_path, tax_path_sn, abundance in that order
		for path_length in xrange(1, tax_path_lengths + 1):
			for key in keys:
				if len(_data[key]["tax_path"]) == path_length and _data[key]["abundance"] > self._eps:
					line_data = _data[key]
					fid.write("%s\t" % key)
					if self._rank_pos is not None:
						fid.write("%s\t" % line_data["rank"])
					fid.write("%s\t" % "|".join(line_data["tax_path"]))
					if self._tax_path_sn_pos is not None:
						fid.write("%s\t" % "|".join(line_data["tax_path_sn"]))
					fid.write("%f\n" % line_data["abundance"])
		fid.close()
		return

	def threshold(self, threshold=None):
		if threshold is None:
			raise Exception
		_data = self._data
		keys = _data.keys()
		for key in keys:
			if _data[key]["abundance"] < threshold:
				_data[key]["abundance"] = 0
		return

	def _subtract_down(self):
		# helper function to push all the weights up by subtracting
		# NOTE: when subtracting, need to start at root and go down
		# NOTE: when adding, need to start at leaves and go up
		_data = self._data
		keys = _data.keys()
		# This will be annoying to keep things in order...
		# Let's iterate on the length of the tax_path since we know that will be in there
		tax_path_lengths = max([len(_data[key]["tax_path"]) for key in keys])
		for path_length in range(1, tax_path_lengths):  # eg tax_path_lengths = 5, use 1,2,3,4 since we stop at leaves
			for key in keys:
				if len(_data[key]["tax_path"]) == path_length:
					descendants = _data[key]["descendants"]  # get all descendants
					for descendant in descendants:
						_data[key]["abundance"] -= _data[descendant]["abundance"]  # subtract the descendants abundance

	def _add_up(self):
		# helper function to push all the weights up by subtracting
		# NOTE: when subtracting, need to start at root and go down
		# NOTE: when adding, need to start at leaves and go up
		_data = self._data
		keys = _data.keys()
		# This will be annoying to keep things in order...
		# Let's iterate on the length of the tax_path since we know that will be in there
		tax_path_lengths = max([len(_data[key]["tax_path"]) for key in keys])
		for path_length in range(tax_path_lengths, 1, -1):  # eg tax_path_lengths = 5, use 5,4,3,2, since we stop at roots
			for key in keys:
				if len(_data[key]["tax_path"]) == path_length:
					ancestor = _data[key]["ancestor"]
					if ancestor in _data:  # don't do anything if this is a/the root node
						_data[ancestor]["abundance"] += _data[key]["abundance"]  # add the descendants abundance

	def normalize(self):
		# Need to really push it up while subtracting, then normalize, then push up wile adding
		#self._push_up(operation="subtract")
		self._subtract_down()
		_data = self._data
		keys = _data.keys()
		total_abundance = 0
		for key in keys:
			total_abundance += _data[key]["abundance"]
		print(total_abundance)
		for key in keys:
			_data[key]["abundance"] /= total_abundance
			_data[key]["abundance"] *= 100  # make back into a percentage
		#self._push_up(operation="add")
		self._add_up()
		return

	def merge(self, other):
		# Warning: not checking for taxonomic consistency
		if not isinstance(other, Profile):
			print("Only works with other Profiles")
			raise Exception
		self._header.insert(0, "# This is a merged file, ignore files in headers below")
		_data = self._data
		_other_data = other._data
		other_keys = _other_data.keys()
		for key in other_keys:
			if key in _data:
				_data[key]["abundance"] += _other_data[key]["abundance"]  # if already in there, add abundances
			else:
				_data[key] = copy.copy(_other_data[key])  # otherwise use the whole thing




