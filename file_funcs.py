"""
File input and output functions
"""
import ujson as json
from dev_funcs import printline, Recorded_Time
from comms import Appointment

#class to store data imported from local json config file
class FileIO:
	def __init__(self):
		#build all of the variables from data.json file
		self.load_local_vars()
		#print the device data after import
		self.print_dev_data()

	def load_local_vars(self):
		#read in unparsed json data
		unparsed_data = self.read_in_file()
		#parse json data into dict objects
		pdata = json.loads(unparsed_data)
		#assign parsed json data to local variables
		self.dev_id = pdata["device_info"]["dev_id"]
		self.server_pass = pdata["device_info"]["server_pass"]
		self.firm_version = pdata["device_info"]["firm_version"]
		self.wifi_networks = pdata["wifi_params"]
		self.appointments = pdata["appointments"]
		self.last_known_time = pdata["device_info"]["last_known_time"]
		self.quiet_hours = pdata["device_info"]["quiet_hours"]

	#function to print basic device info
	def print_dev_data(self):
		#construct a string with all the device info to be displayed
		ts = "Device " + str(self.dev_id) + " | Firmware version: " + \
		str(self.firm_version)
		#print constructed string
		print(ts)

	#function to update time in json file with current time
	#takes a Recorded_Time instance (preferred) or a string (not as good)
	#no formatting, if time is rewritten incorrectly it could cause a failure
	def update_last_known_time(self, current_time):
		#make new string to store the new time
		#new_time = ""
		#check if current_time is a Recorded_Time object
		if isinstance(current_time, Recorded_Time):
			#get the time as a datetime formatted string
			new_time = current_time.get_datetime_string()
		else:
			#otherwise write new_time with current_time object or string
			#this is where failure could happen, use cautiously
			new_time = current_time

		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#rewrite last_known_time
		read_in_data["device_info"]["last_known_time"] = new_time
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	def update_quiet_hours(self, start=None, end=None):
		#define new quiet hours json
		quiet_hours = 	{
								"start_time": start,
								"end_time": end
							}
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#rewrite old unmodified quiet hours entry (preserves all data)
		read_in_data["device_info"]["quiet_hours"] = quiet_hours
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#function takes an Appointment object and adds appointment to appointments object
	def add_appointment(self, new_appt):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#create new JSON of new appt to add
		appt_to_add = 	{
							"appointment_id": int(new_appt.appointment_id),
							"appointment_date_time": new_appt.appointment_date_time,
							"answers" : [],
							"cancelled" : False
						}
		#append new appointment onto appointment JSON obj
		appointments.append(appt_to_add)
		#rewrite old unmodified appointment entry (preserves all data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#function to remove an appointment from the json file
	#takes an appointment id as an arg, does not return anything
	def remove_appointment(self, appointment_id):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#make empty dict of appointments that can be filled by loop
		remaining_appts = []
		#search through appointments for matching id
		for appt in appointments:
			if appt["appointment_id"] != appointment_id:
				remaining_appts.append(appt)
		#rewrite old unmodified appointment entry (preserves all other data)
		read_in_data["appointments"] = remaining_appts
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#function to get appoint data stored in data.json
	#returns None (if no appts) or an array of Appointment objects
	def get_appointments(self, appt_id=None):
		if appt_id:
			for appt in self.appointments:
				if appt["appointment_id"] == appt_id:
					return Appointment(appt["appointment_id"],appt["answers"],appt["appointment_date_time"], appt["cancelled"])
			return None
		else:
			#create new array for resulting objects
			appts_arr = []
			#go through appointments json
			for appt in self.appointments:
				#create new appointment with json data
				new_appt = Appointment(appt["appointment_id"],appt["answers"],appt["appointment_date_time"], appt["cancelled"])
				#add newly created Appointment obj to list to return
				appts_arr.append(new_appt)
			#return the array
			return appts_arr

	def get_cancelled_appointments(self):
		#create new array for resulting objects
		appts_arr = []
		#go through appointments json
		for appt in self.appointments:
			if appt.cancelled:
				#create new appointment with json data
				new_appt = Appointment(appt["appointment_id"],appt["answers"],appt["appointment_date_time"], appt["cancelled"])
				#add newly created Appointment obj to list to return
				appts_arr.append(new_appt)
		#return the array
		return appts_arr

	def get_unsent_appointment_answers(self):
		appts_arr = []
		#go through appointments json
		for appt in self.appointments:
			for answer in appt["answers"]:
				if answer["sent"] == False:
					#create new appointment with json data
					new_appt = Appointment(appt["appointment_id"],appt["answers"],appt["appointment_date_time"], appt["cancelled"])
					highest_answer = 0
					for i in appt["answers"]:
						if i["number"] > highest_answer:
							highest_answer = i["number"]
					#add newly created Appointment obj to list to return
					appts_arr.append([new_appt,highest_answer])
		#return the array
		return appts_arr

	#function adds an appointment answer to the specified appt
	#takes an appt id (int), an answer (True,False,None), and a Recorded_Time object
	def new_appointment_answer(self, appointment_id, answer, currtime, answer_number):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#search through appointments for matching id
		for appt in appointments:
			if appt["appointment_id"] == appointment_id:
				currtime.update_time()
				new_answer = 	{
								"answer": answer,
								"time_answered": currtime.get_datetime_string(),
								"number": answer_number,
								"sent": False
								}
				appt["answers"].append(new_answer)
		#rewrite old unmodified appointment entry (preserves all other data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	def cancel_appointment(self, appointment_id):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#search through appointments for matching id
		for appt in appointments:
			if appt["appointment_id"] == appointment_id:
				appt["cancelled"] = True
		#rewrite old unmodified appointment entry (preserves all other data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	def remove_appointment_answer(self, appointment_id):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#search through appointments for matching id
		for appt in appointments:
			if appt["appointment_id"] == appointment_id:
				appt["answers"] = []
		#rewrite old unmodified appointment entry (preserves all other data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#updates answer status (change sent status from false to true)
	def update_appointment_answer_status(self, appointment_id, status, number):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#search through appointments for matching id
		for appt in appointments:
			if appt["appointment_id"] == appointment_id:
				for answer in appt["answers"]:
					if number == answer["number"]:
						answer["sent"] = status
						
		#rewrite old unmodified appointment entry (preserves all other data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()


		#function takes an ssid, password, adds wifi network to wifi params
	def add_wifi_network(self, ssid, password):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the "wifi_params" section of json data
		wifi_networks = read_in_data["wifi_params"]
		#create new JSON of new wifi network to add
		network_to_add ={
							"ssid": ssid,
							"password" : password
						}
		#append new network onto wifi_networks JSON obj
		wifi_networks.append(network_to_add)
		#rewrite old unmodified wifi_params entry (preserves all other data)
		read_in_data["wifi_params"] = wifi_networks
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#function to remove a wifi network entry from the json file
	#takes a wifi ssid an arg, does not return anything
	def remove_wifi_network(self, ssid):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the "wifi_params" section of json data
		wifi_networks = read_in_data["wifi_params"]
		#make empty dict of remaining networks that can be filled by loop
		remaining_networks = []
		#search through wifi_networks for matching ssid
		for wifi_network in wifi_networks:
			if wifi_network["ssid"] != ssid:
				remaining_networks.append(wifi_network)
		#rewrite old unmodified appointment entry (preserves all data)
		read_in_data["wifi_params"] = remaining_networks
		#dump the json data to the file saver func, reload local vars from json file
		self.write_to_file(json.dumps(read_in_data))
		self.load_local_vars()

	#function reads in data.json file and returns unmodified string
	def read_in_file(self):
		#create file object pointing to json config file
		loc_file = open('data.json', 'r')
		#read in unparsed json data, close file
		unparsed_data = loc_file.read()
		loc_file.close()
		#return resulting unparsed data
		return unparsed_data

	#function to rewrite json file
	#WILL OVERWRITE ALL JSON DATA, READ DATA, MODIFY, THEN WRITE
	def write_to_file(self, new_file_text):
		#create file object pointing to json config file
		loc_file = open('data.json', 'w')
		#write data to file
		loc_file.write(new_file_text)
		#close file
		loc_file.close()