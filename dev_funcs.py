"""
This file is mainly to store functions used on the backend
This includes checking for memory allocation and other info necessary for debugging
"""

import gc, uos, time
from config import extra_params as epconf

#function to cleanup memory (must be used periodically)
#memory is limited on the ESP32 and wifi requests are problematic (ton of ascii data)
def cleanup_mem():
	#cleanup memory using the garbage collector
	gc.collect

#function to see how much memory has been used
#takes true or false arg (print to console or array)
#if false, array of [allocated_memory, free_memory]
def return_used_mem(default_print=True):
	#get allocated memory from garbage collector
	alloc = gc.mem_alloc()
	#get free memory from garbage collector
	free = gc.mem_free()
	#if output is meant to be printed (most cases)
	if default_print:
		#print the data
		print("Allocated Mem: " + str(alloc) + " | Free Mem: " + str(free))
	else:
		#otherwise return it in an array
		return [alloc,free]

def return_used_system_space(default_print=True):
	stats = uos.statvfs("/")
	#if output is meant to be printed (most cases)
	if default_print:
		#print the data
		print("Used System Memory: " + str(stats[3]))
	else:
		#otherwise return it in an array
		return stats[3]

#custom print function so we can disable printing while not in debug mode
def printline(string_to_print):
	if epconf.DEBUG:
		print(string_to_print)
	else:
		pass

#class to act as a datetime object since it doesnt exist in time module
#takes a string (formatted like "2021-03-25T08:27:30.969")
class Recorded_Time:
	#def __init__(self, year, month, day, hour, minute, second):
	#	self.year = year
	#	self.month = month
	#	self.day = day
	#	self.hour = hour
	#	self.minute = minute
	#	self.second = second
	def __init__(self, datetime_string):
		#split string into time and date sections
		if datetime_string.find('T') >= 0:
			split_data = datetime_string.split('T')
		else:
			split_data = datetime_string.split(' ')
		#split date information
		pdate = split_data[0].split('-')
		#split time information
		ptime = split_data[1].split(':')
		#store all of this info as seperate local vars
		self.year = int(pdate[0])
		self.month = int(pdate[1])
		self.day = int(pdate[2])
		self.hour = int(ptime[0])
		self.minute = int(ptime[1])
		self.second = int(float(ptime[2]))
		#is stored as an array, used to see elapsed sys time 
		#(year, month, day, hour, minute, second, weekday, yearday)
		self.sys_time_at_creation = time.localtime()

	#function to turn Recorded_Time object into datetime string
	def get_datetime_string(self):
		#add year to string to return, add character to seperate year from month
		rstring = str(self.year) + "-"
		#if month is less than 10, add zero to front of month
		if self.month < 10:
			rstring += "0" + str(self.month)
		else:
			rstring += str(self.month)
		#add character to seperate month from day
		rstring += "-"
		#if day is less than 10, add zero to front of day
		if self.day < 10:
			rstring += "0" + str(self.day)
		else:
			rstring += str(self.day)
		#seperate date from time section
		rstring += "T"
		#if hour is less than 10, add zero to front of hour
		if self.hour < 10:
			rstring += "0" + str(self.hour)
		else:
			rstring += str(self.hour)
		#add character to seperate hour from minute
		rstring += ":"
		#if minute is less than 10, add zero to front of minute
		if self.minute < 10:
			rstring += "0" + str(self.minute)
		else:
			rstring += str(self.minute)
		#add character to seperate minute from second
		rstring += ":"
		#if second is less than 10, add zero to front of second
		if self.second < 10:
			rstring += "0" + str(self.second) + ".000"
		else:
			rstring += str(self.second) + ".000"
		#finally, return the combined string
		return rstring

	#function to calculate the time difference between when object was created
	#and current time
	#returns an array formatted like time.localtime() output
	def time_difference(self):
		#get current system time
		current_sys_time = time.localtime()
		#calculate difference between current time and time at creation of object
		second_diff = current_sys_time[5]-self.sys_time_at_creation[5]
		minute_diff = current_sys_time[4]-self.sys_time_at_creation[4]
		hour_diff = current_sys_time[3]-self.sys_time_at_creation[3]
		day_diff = current_sys_time[2]-self.sys_time_at_creation[2]
		month_diff = current_sys_time[1]-self.sys_time_at_creation[1]
		year_diff = current_sys_time[0]-self.sys_time_at_creation[0]

		#if second is negative, add 60 to it and remove one from minute
		if second_diff < 0:
			minute_diff -= 1
			second_diff += 60
		#if minute is negative, add 60 to it and remove one from hour
		if minute_diff < 0:
			hour_diff -= 1
			minute_diff += 60
		#if hour is negative, add 24 to it and remove one from day
		if hour_diff < 0:
			day_diff -= 1
			hour_diff += 24
		#if day is negative, add 365 to it and remove one from year
		if day_diff < 0:
			year_diff -= 1
			day_diff += 365

		#return array object formatted exactly like sys_time_at_creation
		return([year_diff,month_diff,day_diff,hour_diff,minute_diff,second_diff \
			, current_sys_time[6], current_sys_time[7]])

	#function to update this object with the current time, as calculated by time_difference
	def update_time(self):
		#get time difference
		difference = self.time_difference()
		#if second is overflowed, add 1 to minute and correct second
		if (self.second + difference[5]) >= 60:
			self.second = (self.second + difference[5])-60
			self.minute += 1
		else:
			self.second = (self.second + difference[5])
		printline(self.second)
		#if minute is overflowed, add 1 to hour and correct minute
		if (self.minute + difference[4]) >= 60:
			self.minute = (self.minute + difference[4])-60
			self.hour += 1
		else:
			self.minute = (self.minute + difference[4])
		printline(self.minute)
		#if hour is overflowed, add 1 to hour and correct day
		if (self.hour + difference[3]) >= 24:
			self.hour = (self.hour + difference[3])-24
			self.day += 1
		else:
			self.hour = (self.hour + difference[3])
		printline(self.hour)
		#if day is overflowed, add 1 to month and correct day
		if (self.day + difference[2]) > 31:
			self.day = (self.day + difference[2])-31
			self.month += 1
		else:
			self.day = (self.day + difference[2])
		printline(self.day)
		#if month is overflowed, add 1 to minute and correct month
		if (self.month + difference[1]) > 12:
			self.month = (self.month + difference[1])-12
			self.year += 1
		else:
			self.month = (self.month + difference[1])
		printline(self.month)
		#update system time variable with current values
		self.sys_time_at_creation =	time.localtime()

	#function to offset time (minutes arg is only implemented portion)
	def offset_time(self, years=0, months=0, days=0, hours=0, mins=0, seconds=0):
		#check if mins overflows 60 mins
		if mins+self.minute >= 60:
			#correct for this
			self.minute = self.minute + (mins%60)
			self.hour += mins//60
			#check if hours is now overflowed
			if self.hour >= 24:
				self.day += self.hour//24
				self.hour = self.hour%24
		else:
			self.minute += mins

	#function that compares current time to given datetime_string
	#returns a dict of 
	def compare_time(self, datetime_string):
		#split string into time and date sections
		if datetime_string.find('T') >= 0:
			split_data = datetime_string.split('T')
		else:
			split_data = datetime_string.split(' ')
		#split date information
		pdate = split_data[0].split('-')
		#split time information
		ptime = split_data[1].split(':')
		#store all of this info as seperate local vars
		c_year = int(pdate[0])
		c_month = int(pdate[1])
		c_day = int(pdate[2])
		c_hour = int(ptime[0])
		c_minute = int(ptime[1])
		c_second = int(float(ptime[2]))
		#get the difference between current time and datetime_string
		c_year = c_year-self.year
		c_month = c_month-self.month
		c_day = c_day-self.day
		c_hour = c_hour-self.hour
		c_minute = c_minute-self.minute
		c_second = c_second-self.second
		#if any of these values overflow (with a positive num in front)
		#adjust the numbers
		#has to be written this way so negative values persist if time is behind current time
		"""if c_year > 0 and c_month < 0:
			c_year -= 1
			c_month += 12

		if c_month > 0 and c_day < 0:
			c_month -= 1
			c_day += 31

		if c_day > 0 and c_hour < 0:
			c_day -= 1
			c_hour += 24

		if c_hour > 0 and c_minute < 0:
			c_hour -= 1
			c_minute += 60

		if c_minute > 0 and c_second < 0:
			c_minute -= 1
			c_second += 60
		"""
		if c_second < 0:
			c_minute -= 1
			c_second += 60

		if c_minute < 0:
			c_hour -= 1
			c_minute += 60

		if c_hour < 0:
			c_day -= 1
			c_hour += 24
			
		if c_day < 0:
			c_month -= 1
			c_day += 31

		if c_month < 0:
			c_year -= 1
			c_month += 12
		#check if any of the values are negative (indicates appt has past)
		appt_passed = False
		if c_year < 0 or c_month < 0 or c_day < 0 or c_hour < 0 or c_minute < 0 or c_second < 0:
			appt_passed = True
		#printline(str(c_year) + " | " + str(c_month) + " | " + str(c_day) + " T " +\
		#	str(c_hour) + " | " + str(c_minute) + " | " + str(c_second))
		#return a dict of values
		return {
				"year": c_year,
				"month": c_month,
				"day": c_day,
				"hour": c_hour,
				"minute": c_minute,
				"second": c_second,
				"appointment_passed": appt_passed
				}

	def check_if_appt_reminder_necessary(self, appt):
		remind = False
		answer1 = None
		answer2 = None
		answer3 = None
		highest_ans = 0

		for answer in appt.answers:
			if answer["number"] == 1:
				answer1 = answer
			if answer["number"] == 2:
				answer2 = answer
			if answer["number"] == 3:
				answer3 = answer

		if answer1:
			highest_ans = 1
		if answer2:
			highest_ans = 2
		if answer3:
			highest_ans = 3

		appt_diff = self.compare_time(appt.appointment_date_time)
		appt_hour_diff = appt_diff["hour"] + (appt_diff["day"]*24)
		printline(str(appt_hour_diff) + " hours until appt")

		if appt_diff["year"] == 0 and appt_diff["month"] == 0:
			"""if appt_diff["day"] <= 2 and appt_diff["day"] > 1 and answer1 is None:
				return True, 1
			if appt_diff["day"] <= 1 and appt_diff["day"] > 0 and answer2 is None:
				return True, 2
			if appt_diff["day"] == 0 and appt_diff["hour"] <= 5 and answer3 is None:
				return True, 3"""
			if appt_hour_diff <= 48 and appt_hour_diff > 24 and answer1 is None:
				return True, 1
			if appt_hour_diff <= 24 and appt_hour_diff > 5 and answer2 is None:
				return True, 2
			if appt_hour_diff <= 5 and appt_hour_diff >= 0 and answer3 is None:
				return True, 3

		return False, None

#function to turn datetime string into object
#datetime format is 2021-03-25T08:27:30.969
"""
def format_datetime(datetime_string):
	split_data = datetime_string.split('T')
	date = split_data[0].split('-')
	time = split_data[1].split(':')
	time[2] = time[2].split('.')[0]
	datetime_to_ret = Datetime_Obj(date[0],date[1],date[2],time[0],time[1],time[2].sp)
"""