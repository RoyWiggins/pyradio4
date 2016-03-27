import urllib, json, arrow,subprocess,os,sys,schedule,time,pickle
from mutagen.mp4 import MP4

def get_broadcast_data(day):
	url = "http://www.bbc.co.uk/radio4/programmes/schedules/fm/%s.json" % (day,)
	print url
	try:
		response = urllib.urlopen(url)
	except:
		print "Network error."
	try:
		data = json.loads(response.read())
	except:
		print "Invalid JSON returned."

	return data['schedule']['day']['broadcasts']

def parse_broadcasts(data):
	spans = []
	for broadcast in data:
		pid = broadcast['programme']['pid']
		title = broadcast['programme']['display_titles']['title']
		try:
			start = arrow.get(broadcast['start'])
			end = start.replace(seconds=broadcast['duration'])
			spans.append((start,end,pid,title))
		except:
			pass
	spans.sort()
	return spans
def get_shifted_program(spans):
	timeshift = arrow.now().replace(tzinfo="Europe/London")
	for span in spans:
		if span[0] < timeshift and span[1] > timeshift:
			return span

def get_recent_broadcasts(now):
	try:
		with open('data.pkl', 'rb') as pkl_file:
			data = pickle.load(pkl_file)
			return data
	except:
		today = now.format("YYYY/MM/DD")
		yesterday = now.replace(days=-1).format("YYYY/MM/DD")
		data = get_broadcast_data(yesterday)
		data.extend(get_broadcast_data(today))
		with open('data.pkl', 'wb') as output:
			pickle.dump(data, output)
	return data



def subprocess_call(*vars):
	print "calling"
	cmd = vars
	try:
		output = subprocess.check_output(vars)
	except:
		print "call failed", str(vars)

class Program:
	def __init__(self,schedule_info):
		self.pid = schedule_info['programme']['pid']
		self.title = schedule_info['programme']['display_titles']['title']
		self.start = arrow.get(schedule_info['start'])
		self.duration = schedule_info['duration']
		self.end = self.start.replace(seconds=self.duration)
		self.pips_before = False
		self.pips_after = False
		self.actual_length = None
		self._file = None
		self.padded_file = None
		self.trimmed_file = None
	def __repr__(self):
		return str((self.start,self.end,self.pid,self.title,self._file))
	def __cmp__(self, other):
		return cmp(self.start,other.start)

	def play(self, current_time):
		os.chdir(r"C:\Program Files\VideoLAN\VLC")
		proc = subprocess.Popen(['vlc.exe',self._file,
								 '--start-time', str(current_time),
								 '--play-and-stop'])

	def pad(self):
		if not program._file: return
		if program.padded_file: return
		if program.duration > program.actual_length:
			os.chdir(os.path.expanduser("~\Desktop\iPlayer Recordings"))
			program.padded_file = program._file[:-4] + "_pad.m4a"
			if os.path.isfile(program.padded_file):
				return
			proc = subprocess.call(['ffmpeg','-y','-i',program._file,'-map','0:a:0','-c','copy','temp1.m4a'])
			proc = subprocess.call(['ffmpeg','-y','-i','temp1.m4a', '-c','copy','-bsf:v h264_mp4toannexb', '-f', 'temp2.ts'])
			proc = subprocess.call(['ffmpeg','-y','-i','concat:temp2.ts|silence.ts','-t',str(program.duration),
									'-c','copy','-bsf:a', 'aac_adtstoasc',program.padded_file])
			program.actual_length = program.duration

	def trim_to_duration(self):
		if self.trimmed_file: return
		if not self.duration:
			raise Exception("Tried to trim to nonexistent duration")
		self.trimmed_file = self._file[:-4] + "_trim.m4a"
		if os.path.isfile(self.trimmed_file):
			return
		print "Trimming:", self.title
		proc = subprocess.Popen(['ffmpeg','-i',self._file, 
								 '-t',str(self.duration), '-map','0:a:0','-c', 'copy', '-y',
								 self.trimmed_file])
		if proc == 1:
			raise Exception("ffmpeg fail")
		self.actual_length = program.duration
		self.pips_after = False

	def current_file(self):
		if self.trimmed_file:
			return self.trimmed_file
		if self.padded_file:
			return self.trimmed_file
		return self._file

# Download programs from the last eight hours
def fill_in_files(programs):
	pid_to_files = {}
	with open(os.path.expanduser(r'~\.get_iplayer\download_history')) as f:
		for line in f.readlines():
			l = line.split("|")
			pid_to_files[l[0]] = l[6]
	for program in programs:
		if pid_to_files.has_key(program.pid):
			program._file = pid_to_files[program.pid]
			program.actual_length = MP4(program._file).info.length
	return programs


	
def generate_empty(programs):
	for program in remaining_programs:
		if program._file == None and (program.end - program.start).seconds < 60 * 5: 
			os.chdir(os.path.expanduser("~\Desktop\iPlayer Recordings"))
			program._file = os.path.expanduser("~\Desktop\iPlayer Recordings") + "\\"+ program.title + " " +program.pid+".m4a"
			program.actual_length = (program.end - program.start).seconds
			proc = subprocess.call(['ffmpeg','-filter_complex', 'aevalsrc=0', '-t',
									str(program.actual_length),program._file])
			print program
	return programs

def get_current_shifted(programs):
	timeshift = arrow.now().replace(tzinfo="Europe/London")
	ret = []
	for program in programs:
		if program.end > timeshift and program.start < timeshift:
			current_time = timeshift-program.start
			return program, str(int(current_time.total_seconds()))

def play(program, current_time):
	os.chdir(r"C:\Program Files\VideoLAN\VLC")
	proc = subprocess.Popen(['vlc.exe',program._file,
							 '--start-time', str(current_time),
							 '--play-and-stop'])

def schedule_play(program_file):
	def play_me():
		play(program_file,"0")
		return schedule.CancelJob
	return play_me


def pad_short_programs(programs):
	for prev,program in zip(programs,programs[1:]):
		program.padded_file = None
		if not prev.pips_after and not program.pips_after:
			print "Padding", program.title
			pad(program)
		else:
			print "Not padding", program.title
		   
	print "Done."
def trim_programs(programs):
	for program,next_ in zip(programs,programs[1:]):
		if program.pips_after and next_.pips_before or program.title == "The Archers" \
		or (program.actual_length > program.duration and next_.actual_length >= next_.duration):
			print program.title,""
			proc = subprocess.Popen(['ffmpeg','-i',program._file, 
									 '-t',str(program.duration), '-map','0:a:0','-c', 'copy', '-y',
									 program._file[:-4] + "_trim.m4a"])
			program._file = program._file[:-4] + "_trim.m4a"
			program.actual_length = program.duration
			program.pips_after = False

def build_playlist(programs):
	with open(os.path.expanduser("~\Desktop\iPlayer Recordings\playlist.m3u"),"w") as f:
		for program in programs:
			if program.padded_file:
				f.write(program.padded_file.split("\\")[-1]+'\n')
				continue
			if program._file:
				f.write(program._file.split("\\")[-1]+'\n')

def burn(programs):
	with open(os.path.expanduser("~\Desktop\iPlayer Recordings\concat"),"w") as f:
		for program in remaining_programs:
			if program.padded_file:
				f.write("file '"+program.padded_file+"'\n")
				continue
			if program._file:
				f.write("file '"+program._file+"'\n")
	os.chdir(os.path.expanduser("~\Desktop\iPlayer Recordings"))
	print "Burning..."
	file_ = 'BBC Radio 4 %s %s.m4a' % (remaining_programs[0].start.format("YY-MM-DD HHmm"),
										  remaining_programs[-1].end.format("YY-MM-DD HHmm"),)
	print file_
	sys.stdout.flush()
	proc = subprocess.call(['ffmpeg','-y','-f','concat','-i','concat', '-map','0:a:0','-c', 'copy',file_])
	print "Done."


class Programs():
	def __init__(self, data):
		self.list = []
		if len(data) and not isinstance(data[0],Program):
			self.list = [Program(info) for info in data]
			self.dict = {}
			self.list.sort()
			self.dedup()
			for program in self.list:
				self.dict[program.pid] = program
		else:
			self.list = data
			self.dict = {}
			for program in self.list:
				self.dict[program.pid] = program
	def dedup(self):
		self.list = [prg for i,prg in enumerate(self.list) if prg.pid != self.list[i-1].pid]

	def filter_only_remaining(self,now):
		"""
		Returns the programs remaining to play
		"""
		timeshift = now.replace(tzinfo="Europe/London")
		return Programs([program for program in self.list if program.end > timeshift  and program.end < now])

	def __repr__(self):
		return self.list.__repr__()
	def __len__(self):
		return self.list.__len__()

	def fill_in_files(self):
		with open(os.path.expanduser(r'~\.get_iplayer\download_history')) as f:
			for line in f.readlines():
				l = line.split("|")
				try:
					self.dict[l[0]]._file = l[6]
					self.dict[l[0]].actual_length = MP4(l[6]).info.length
				except KeyError:
					pass

	def generate_empty(self):
		for program in self.list:
			if program._file == None and (program.end - program.start).seconds < 60 * 5: 
				os.chdir(os.path.expanduser("~\Desktop\iPlayer Recordings"))
				program._file = os.path.expanduser("~\Desktop\iPlayer Recordings") + "\\"+ program.title + " " +program.pid+".m4a"
				if os.path.isfile(program._file):
					continue
				program.actual_length = (program.end - program.start).seconds
				proc = subprocess.call(['ffmpeg','-filter_complex', 'aevalsrc=0', '-t',
										str(program.actual_length),program._file])
				print program._file

	def download(self):
		os.chdir(r'C:\Program Files (x86)\get_iplayer')
		self.fill_in_files()
		for program in self.list:
			if program._file == None:
				print "Downloading...", program
				proc = subprocess_call(r'get_iplayer.cmd', '--type', 'radio', '--versions','original,shortened',
										 '--pid', program.pid, 
										 '--modes=flashaacstd,flashaaclow,hlsaaclow')
		print "Done."
		self.fill_in_files()
		self.calculate_pips()

	def get_current_shifted(self,now):
		timeshift = now.replace(tzinfo="Europe/London")
		ret = []
		for program in self.list:
			if program.end > timeshift and program.start < timeshift:
				current_time = timeshift-program.start
				return program, str(int(current_time.total_seconds()))

	def play_current_program(self):
		program, time = self.get_current_shifted()
		program.play(time)

	def calculate_pips(self):
		for program1,program2 in zip(self.list,self.list[1:]):
			if not program1._file or not program2._file:
				continue
			if program1.end.minute == 0: # Ends on the hour
				if (program1.actual_length - program1.duration > 0): 
					if program1.actual_length - program1.duration < 240: # But it lasts longer
						program1.pips_after = True
					if program2.actual_length >= program2.duration:
						program2.pips_before = True
			if program1.start.minute == 0 and program1.actual_length > program1.duration and \
				program1.actual_length - program1.duration:
					program1.pips_before = True
			if program1.start.minute == 0 and program1.actual_length >= 3600:
				program1.pips_before = True
	def __str__(self):
		ret = ""
		for program in self.list:
			if program.pips_before:
				ret  = "{P %d:00} " % program.start.hour
			ret  = ret + program.title
			if program.pips_after:
				ret  = ret + " {P %d:00}"% program.end.hour
			if program._file == None:
				ret  = ret + " N"
			ret  = ret + "\r\n"
		return ret
	def trim(self):
		print "trimming"
		for program,next_ in zip(self.list,self.list[1:]):
			if program.pips_after and next_.pips_before or program.title == "The Archers" \
			or (program.actual_length > program.duration and next_.actual_length >= next_.duration):
				program.trim_to_duration()

	def burn(self):
		with open(os.path.expanduser("~\Desktop\iPlayer Recordings\concat"),"w") as f:
			for program in self.list:
				if program.current_file():
					f.write("file '"+program.current_file()+"'\n")
		os.chdir(os.path.expanduser("~\Desktop\iPlayer Recordings"))
		print "Burning..."
		file_ = 'BBC Radio 4 %s %s.m4a' % (self.list[0].start.format("YY-MM-DD HHmm"),self.list[-1].end.format("YY-MM-DD HHmm"),)
		print file_
		sys.stdout.flush()
		proc = subprocess.call(['ffmpeg','-y','-f','concat','-i','concat', '-map','0:a:0','-c', 'copy',file_])
		if proc == 1:
			raise Exception("ffmpeg fail")

		print "Done."

	def build_playlist(self):
		with open(os.path.expanduser("~\Desktop\iPlayer Recordings\playlist.m3u"),"w") as f:
			for program in self.list:
				if program.current_file():
					f.write(program.current_file().split("\\")[-1]+'\n')

	def debug(self):
		current_time = self.list[0].start
		for program,next_program in zip(self.list,self.list[1:]):
			if program.padded_file:
				f = program.padded_file
			elif program._file:
				f = program._file
			
			if current_time  and program._file:
				print current_time,
				if current_time > program.start:
					print current_time - program.start,
				else:
					print "-%s" % (program.start - current_time),
				print program.title
				current_time=current_time.replace(seconds=MP4(f).info.length)

now = arrow.now().replace(hours=-12)
data = get_recent_broadcasts(now)
programs = Programs(data)
programs = programs.filter_only_remaining(now)
print len(programs)
programs.download()
programs.generate_empty()
programs.trim()
programs.build_playlist()
#programs.burn()
programs.debug()
programs.play_current_program(now)

print programs
def main():
	data = get_recent_broadcasts()
	programs = [Program(info) for info in data]
	programs.sort()
	programs = [prg for prg,i in zip(programs,range(len(programs))) # There are overlaps between "today" and "yesterday"'s schedules
				   if prg.pid != programs[i-1].pid] # So we can remove adjacent duplicates


	remaining_programs = get_remaining_programs(programs) 
	download(remaining_programs)
	remaining_programs = fill_in_files(remaining_programs)
	remaining_programs = generate_empty(remaining_programs)
	schedule.clear()
	for program in remaining_programs:
		hour = program.start.format("HH:mm")
		schedule.every().day.at(hour).do(schedule_play(program._file))
	current_program, current_time = get_current_shifted(remaining_programs)
	play(current_program, current_time) 

	pad_short_programs(remaining_programs)
	trim_programs(remaining_programs)
	build_playlist(remaining_programs)
	burn(remaining_programs)

