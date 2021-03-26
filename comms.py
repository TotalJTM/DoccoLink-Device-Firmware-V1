"""
This file contains all of the code handling incoming and outgoing wifi,
blutooth, and cellular communications
"""
import network
import urequests
from machine import UART
from time import sleep_ms, ticks_ms, ticks_diff
from config import communication_configuration as commconf
from dev_funcs import printline

#class to handle wifi communications
class Dev_WiFi:
	def __init__(self, wifi_credentials):
		self.stored_networks = wifi_credentials
		self.wifi = None
		self.timeout = 4000

	#function to start the wifi network in station mode
	#use this function to send data to servers
	def start_wifi(self):
		#create network object in station mode
		self.wifi = network.WLAN(network.STA_IF)
		#set wifi network to active
		self.wifi.active(True)
		#scan for local networks
		scanned_networks = self.wifi.scan()
		#move through scanned_networks and stored_networks, looking for a
		#local SSID to match one of the saved network entries
		for scanned_network in scanned_networks:
			printline(scanned_network)
			for stored_network in self.stored_networks:
				#print(stored_network)
				#if the network SSIDs match
				if stored_network["ssid"] == scanned_network[0].decode("UTF-8"):
					#connect to the local network
					self.wifi.connect(stored_network["ssid"], stored_network["password"])
					#set initial time we started waiting for network to connect
					init_time = ticks_ms()
					#wait until network is successfully connected or until timeout reached
					while not self.wifi.isconnected() and (ticks_diff(ticks_ms(),init_time) < self.timeout):
						pass
					#check if connected to the network
					if self.wifi.isconnected():
						#if connected, return true and exit
						return True
		#reset wifi var to none state since the network connection failed
		self.wifi = None
		#return false, indicating a failed connection to wifi
		return False

	#function to start ESP32 access point
	#allows the ESP32 to be accessed by logging into the wifi
	#and accessing a web address
	def start_ap(self):
		return None

	#function to send message to specified URL
	#message should be a JSON string
	def send_message(self, method, url, message = None, json = None):
		#makes request to given URL
		data = urequests.request(method, url, data=message, json=json)
		#try to return json data, if no json exists then continue
		try:
			return "JSON", data.json()
		except:
			#try to return text data, if it doesnt exist continue
			try:
				return "TEXT", data.text
			except:
				#try to return content data, if it doesnt exist, return None
				try:
					return "RAW", data.content
				except:
					return None

	#function to send initial message to server
	def send_initial_post(self, message_obj):
		#assemble url for initial post location
		url = commconf.BASE_URL + commconf.INIT_MESSAGE_PATH
		#post message to the server, return type of message and reply
		message_type, reply = self.send_message("POST", url, json=message_obj.get_json())
		#handle acquired data and check for validity
		success, datetime, appt_data = handle_message_replies(message_type, reply)
		#return result of handling
		return success, datetime, appt_data

	#function to send appointment reply message to server
	def send_appointment_reply_post(self, message_obj):
		#assemble url for appointment reply post location
		url = commconf.BASE_URL + commconf.REPLY_MESSAGE_PATH
		#post message to the server, return type of message and reply
		message_type, reply = self.send_message("POST", url, json=message_obj.get_json())
		#handle acquired data and check for validity
		success, reply, unused_var = handle_message_replies(message_type, reply)
		#return result of handling
		return success, reply

#class to handle blutooth communications
#was not implemented to save time
class Dev_Blutooth:
	def __init__():
		return None

#class to handle cellular communications
class Dev_Cell:
	def __init__():
		return None

#function to handle device message replies
#takes message type argument and string reply
#returns True or false (indicating successful message) and datetime, list of Appointments and/or reply
def handle_message_replies(message_type, reply):
	#check if message type is JSON
	if message_type == "JSON":
		#try to get datetime from reply (in initial message without appt)
		try:
			datetime = reply["server_date_time"]
			return True, datetime, None
		#otherwise try to get datetime from array (in initial message with appt)
		except:
			datetime = reply[0]["server_date_time"]
			#create empty list of appointments
			appointments = []
			#move through the sent appointments starting at index 1
			for i in range(0, (len(reply)-1)):
				#create temp location for current data
				tappt = reply[i+1]["fields"]
				#make new Appointment object from data and append that to the list
				appointments.append(Appointment(tappt["appointment_id"], \
					tappt["answer"], tappt["appointment_start_date_time"], tappt["cancelled"]))
			#return true, datetime and list of Appointment objects
			return True, datetime, appointments

	#check if message type is TEXT
	if message_type == "TEXT":
		#if httpresponse is "", return false
		if reply == "Malformed data!":
			return False, reply, None
		#if httpresponse is "", return false
		if reply == "The device with the given ID does not exist!":
			return False, reply, None
		#if httpresponse is "", return false
		if reply == "Wrong device password!":
			return False, reply, None
		#if httpresponse is "", return true
		if reply == "The device message was successfully sent!":
			return True, reply, None
		#default return of false
		return False, reply, None
		#if reply == "":
		#	return 1

	#check if message type is RAW
	if message_type == "RAW":
		printline("raw content type received: " + str(reply))

"""
Device message JSON format
Initial Appt request (via "/getappointments/alpha/v1" path):
	{
		"device_id": "838458",
		"device_password": "heyaedin",
		"battery_level": 80.4
	}

JSON response without appt:
	{
		'Empty queryset': 'No appointment requests were made for this patient during this time interval.', 
		'server_date_time': '2021-03-25T08:58:29.270'
	}

JSON response with appt:
	[
	    {
	        "server_date_time": "2021-03-25 13:58:21.743389"
	    },
	    {
	        "fields": {
	            "appointment_ID": 111111,
	            "appointment_start_date_time": "2021-03-30T12:00:00",
	            "appointment_end_date_time": "2021-03-30T12:30:00",
	            "doctor": 2,
	            "patient": 1,
	            "purpose": "General",
	            "date_time_of_request": "2021-03-25T12:36:17",
	            "date_time_of_response": "2021-03-25T12:36:18",
	            "answer": null,
	            "cancelled": false
	        }
	    }
	]

Appointment update (via "devicemessagehandler/alpha/v1/" path):
	{
    	"device_id": "838458",
    	"device_password": "heyaedin",
    	"appointment_id": "86179341",
    	"answer": 1,
    	"response_date_time": "2020-12-24 17:00:00",
    	"device_battery_level": 80.4
	}
"""
class Dev_Message:
	#all messages need a device id, device password, and battery level value
	def __init__(self, dev_id, server_pass, batt_level):
		#define initial variables
		self.device_id = dev_id
		self.device_password = server_pass
		self.battery_level = batt_level
		#set appointments to none for now, will be added with function
		self.appointment = None

	#compile device message data into json obj
	def get_json(self):
		#if there is an appointment object
		if self.appointment is not None:
			#include appointment information in formatted JSON message (appt update format)
			formatted_json ={ 	
								"device_id": self.device_id,
								"device_password": self.device_password,
								"appointment_id": self.appointment.appointment_id,
								"answer": self.appointment.answer,
								"response_date_time": self.appointment.appointment_date_time,
								"device_battery_level": self.battery_level
							}
		else:
			#if there is no appointment object
			#create regular JSON message (initial message format)
			formatted_json ={ 	
								"device_id": self.device_id,
								"device_password": self.device_password,
								"device_battery_level": self.battery_level
							}
		return formatted_json

	#function to add appointment information to this message
	def include_appointment(self, appointment_obj):
		self.appointment = appointment_obj

#class to store appointment information in a cleanly formatted way
class Appointment:
	def __init__(self, appointment_id, answer, appointment_date_time, cancelled=False):
		self.appointment_id = appointment_id
		self.answer = answer
		self.appointment_date_time = appointment_date_time
		self.cancelled = cancelled

#class to handle serial communications input and output
class Computer_Comms:
	def __init__(self):
		#try to create UART object that will communicate with the computer (serial port 0)
		try:
			self.uart = UART(0,115200)
		except:
			printline("Tried to start UART with REPL active, no UART obj created")

	#function that waits (in a while loop) for specific USB commands
	#takes a time (in ms) to wait for and returns a message (if received) or None
	def wait_for_message(self, wait_time):
		#set initial time with current tick count
		init_time = ticks_ms()
		#read from UART, will most likely return None here
		message = self.uart.readline()
		#wait until message reveived or until timeout reached
		while message is None and \
		(ticks_diff(ticks_ms(),init_time) < self.timeout):
			#read from UART
			message = self.uart.readline()

		#if there was a message
		if message:
			#return the message
			return message
		else:
			#otherwise return nothing
			return None