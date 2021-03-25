"""
File input and output functions
"""
import ujson as json
from dev_funcs import printline
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

	#function to print basic device info
	def print_dev_data(self):
		#construct a string with all the device info to be displayed
		ts = "Device " + str(self.dev_id) + " | Firmware version: " + \
		str(self.firm_version)
		#print constructed string
		printline(ts)

	#function takes an Appointment object and adds appointment to appointments object
	def add_appointment(self, new_appt):
		#read in data from file
		read_in_data = json.loads(self.read_in_file())
		#isolate the appointment data
		appointments = read_in_data["appointments"]
		#create new JSON of new appt to add
		appt_to_add = 	{
							"appointment_id": new_appt.appointment_id,
							"appointment_date_time": new_appt.appointment_date_time,
							"answer" : new_appt.answer
						}
		#append new appointment onto appointment JSON obj
		appointments.append(appt_to_add)
		#rewrite old unmodified appointment entry (preserves all data)
		read_in_data["appointments"] = appointments
		#dump the json data to the file saver func
		self.write_to_file(json.dumps(read_in_data))

	#function to get appoint data stored in data.json
	#returns None (if no appts) or an array of Appointment objects
	def get_appointments(self):
		#create new array for resulting objects
		aptts_arr = []
		#go through appointments json
		for appt in self.appointments:
			#create new appointment with json data
			new_appt = Appointment(appt["appointment_id"],appt["answer"],appt["appointment_date_time"])
			#add newly created Appointment obj to list to return
			appts_arr.append(new_appt)
		#if the list has items in it, return the arr
		if len(aptts_arr) > 0:
			return aptts_arr
		#otherwise return None so program can properly handle that
		else:
			return None

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
		loc_file.write()
		#close file
		loc_file.close()
