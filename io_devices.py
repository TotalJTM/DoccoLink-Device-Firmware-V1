"""
This file stores the classes and functions pertaining to the input output devices
"""
from config import pin_configuration as pconf
from config import extra_params as params
from config import buzzer_configuration as buzzconf
from dev_funcs import printline
from machine import Pin, PWM, ADC, SPI, UART
from time import sleep_ms, ticks_ms, ticks_diff
import uasyncio
import pyfingerprint

#class to define the buzzer onboard
#create the buzzer object and call short_buzz (as func) or buzz (in uasyncio event loop)
class Buzzer:

	def __init__(self):
		#define buzzer pin object
		self.buzz_pin = Pin(pconf.BUZZER, Pin.OUT)
		#set initial state of buzzer to off
		self.buzz_pin.off()
		#buzzer object to store PWM object for buzzer pin
		self.buzzer = None

	#activates the buzzer object by definind a PWM on buzzer
	def activate(self):
		#create PWM object for buzzer
		self.buzzer = PWM(self.buzz_pin)

	#deactivate the buzzer by deinitializing PWM, making none and turning pin off
	def deactivate(self):
		#deactivate PWM object, make None instead
		if self.buzzer is not None:
			self.buzzer.deinit()
			self.buzzer = None
			#turn buzzer pin off
			self.buzz_pin.off()

	"""#buzz the buzzer at given tone, tone duration and time between buzzing
	async def buzz(self):
		#run forever until task is destroyed
		while True:
			#activate buzzer
			self.activate()
			#set PWM freq (buzzer tone)
			self.buzzer.freq(buzzconf.TONE)
			#wait for TONE_LENGTH duration (while buzzer active)
			await uasyncio.sleep_ms(buzzconf.TONE_LENGTH)
			#stop buzzer by removing PWM
			self.deactivate()
			#wait for WAIT duration (while buzzer off)
			await uasyncio.sleep_ms(buzzconf.WAIT)
	"""
	#function to start buzzer timer and define initial state
	#must be called before update_buzz
	def start_buzz(self):
		#record current time
		self.last_time = ticks_ms()
		self.on = False

	#function to handle turning on and off the buzzer at regular intervals
	def update_buzz(self):
		if self.on:
			if (ticks_diff(ticks_ms(),self.last_time) > (buzzconf.TONE_LENGTH)):
				self.on = False
				self.last_time = ticks_ms()
				self.deactivate()
		else:
			if (ticks_diff(ticks_ms(),self.last_time) > (buzzconf.WAIT)):
				self.on = True
				self.last_time = ticks_ms()
				self.activate()

	#buzz the buzzer for duration (in ms)
	def short_buzz(self, duration):
		#activate buzzer
		self.activate()
		#set PWM freq (buzzer tone)
		self.buzzer.freq(buzzconf.TONE)
		#buzz buzzer for specified duration
		sleep_ms(duration)


#class to define the 3 tactile buttons on the device
class Buttons:
	def __init__(self):
		self.no_pin = Pin(pconf.NO_BTN, Pin.IN)
		self.yes_pin = Pin(pconf.YES_BTN, Pin.IN)
		self.sel_pin = Pin(pconf.SELECT_BTN, Pin.IN)

	#function to read in state of buttons
	#True if pressed, False if not pressed (pin default high state when not pressed)
	def read_buttons(self):
		#create dict of values to return
		ret_arr = {'yes': False, 'no': False, 'select': False}
		#check if yes pin is LOW
		if self.yes_pin.value() == 0:
			#change yes reply to True
			ret_arr['yes'] = True
		#check if no pin is LOW
		if self.no_pin.value() == 0:
			#change no reply to True
			ret_arr['no'] = True
		#check if select pin is LOW
		if self.sel_pin.value() == 0:
			#change select reply to True
			ret_arr['select'] = True
		#send back ret_arr
		return ret_arr

#class to setup and communicate with SPI bus devices using SPI rail
class SPI_Bus:
	def __init__(self):
		#define pins for VSPI rail
		self.sck = Pin(pconf.SPI_SCK)
		self.miso = Pin(pconf.SPI_MISO)
		self.mosi = Pin(pconf.SPI_MOSI)
		self.ss = Pin(pconf.SPI_SS)
		self.en = Pin(pconf.SPI_EN)
		#disable power going to SPI device
		self.disable()
		#create var for SPI object
		self.dev = None

	#function to activate the SPI bus by enabling device and creating SPI obj
	def activate(self):
		self.enable()
		dev = SPI(2, baudrate=8000000, polarity=0, phase=0, bits=8, firstbit=0, sck=self.sck, mosi=self.mosi, miso=self.miso)

	#enables power going into SPI rail (turns on FET)
	def enable(self):
		self.en.off()		#turn FET on by going LOW
		sleep_ms(params.ACTIVATION_DELAY)	#very short delay to allow power to flow into device
	#disables power going to SPI rail (turns off FET)
	def disable(self):
		self.en.on()		#turn FET off by going HIGH

#class to store fingerprint functions
class Fingerprint:
	#create variables for CHARBUFFER1 and CHARBUFFER2
	BUFF1 = pyfingerprint.FINGERPRINT_CHARBUFFER1
	BUFF2 = pyfingerprint.FINGERPRINT_CHARBUFFER2

	def __init__(self):
		#define pins for fingerprint sensor
		#self.rx = Pin(pconf.FPR_RX)
		#self.tx = Pin(pconf.FPR_TX)
		self.en = Pin(pconf.FPR_EN)
		#turn sensor off until its time to use
		self.disable()
		#variable to store UART object
		self.uart = None
		#variable to store fingerprint device object
		self.dev = None
		
	#starts communicating with the fingerprint sensor
	def activate(self):
		try:
			self.enable()
			#start UART on 3rd serial port
			self.uart = UART(2, tx=pconf.FPR_TX, rx=pconf.FPR_RX)
			#init UART with AS108M sensor settings
			self.uart.init(57600, bits=8, parity=None, stop=2)
			#create fingerprint object from UART
			self.dev = pyfingerprint.PyFingerprint(self.uart)
			#return true if objects are successfully created
			return True
		except:
			#return false otherwise
			return False

	#function to scan a fingerprint that lasts a specific duration
	#argument is time to run within loop (in ms)
	def scan_fingerprint(self, timeout, charbuffer=BUFF1):
		#create success var to track progress in loop
		success = False
		#set initial time we started looking for a fingerprint scan
		init_time = ticks_ms()
		#loop while success is false and timeout not reached
		while success is False and (ticks_diff(ticks_ms(),init_time)<timeout):
			#try to read in an image
			if self.dev.readImage():
				#if successful read, set success to true
				success = True
				#convert image to characteristics and store in charbuffer1
				try:
					self.dev.convertImage(charbuffer)
				except:
					printline("convertimage failure")
			else:
				#otherwise do nothing
				pass
		if success:
			#successful fingerprint scan within time limit
			return True
		else:
			#unsuccessful fingerprint scan
			return False

	#function to check if scanned fingerprint has a match
	#assumes scan_fingerprint was successful
	def match_fingerprint(self):
		#search sensor for matching fingerprint
		#returns position (index 0) and accuracy (index 1) if matched
		result = self.dev.searchTemplate()
		#check if result is -1 (indicating no match)
		if result[0] != -1:
			#return accuracy if valid match
			return result[1]
		else:
			#return nothing if not valid match
			return None

	#function to remove a fingerprint at the location "position"
	#takes arg for index of template to remove, returns true if successful, false if failed or DNE
	def remove_fingerprint(self, position):
		try:
			#try to delete template
			self.dev.deleteTemplate(position)
			#return true if successful
			return True
		except:
			#if unsuccessful removal or no template, return false
			return False

	#function that removes all stored templates from the fingerprint database
	#function takes no arguments, returns true or false depending on success
	def remove_all_fingerprints(self):
		#clear the fingerprint database
		if self.dev.clearDatabase():
			#return true if successful 
			return True
		else:
			#return false if unsuccessful
			return False

	#function enrolls a fingerprint into the AS108M sensor
	#takes a location as argument, can be 0-99
	def enroll_fingerprint(self, fp_location=-1, fp_scan_timeout=10e3):
		#create loop to scan fingerprint N number of times (as defined in config)
		for i in range(1,params.NUM_OF_FINGERPRINT_SCANS+1):
			printline("scanning fingerprint into buffer " + str(i))
			#scan fingerprint, store in buffer i (1-5 max)
			self.scan_fingerprint(fp_scan_timeout, i)
			#sleep for a little bit so new fingerprint can be set on scanner
			sleep_ms(1000)
		#create new template from scanned fingerprint
		self.dev.createTemplate()
		#store this newly created fingerprint
		self.dev.storeTemplate(positionNumber=fp_location, charBufferNumber=self.BUFF1)
		return True

		#old code that didnt work well
		"""
		if self.scan_fingerprint(10e3, self.BUFF1):
			#see if fingerprint is already enrolled in device
			#if self.match_fingerprint():
			#	printline("fingerprint already enrolled")
			#	return 1
			#if not enrolled
			#else:
			#wait 1 second
			sleep_ms(1000)
			#scan the same fingerprint again and store in buffer 2
			if self.scan_fingerprint(10e3, self.BUFF2):
				#compare the two buffers
				if self.dev.compareCharacteristics() == 0:
					printline("fingerprints dont match")
					return 0
				else:
					#create new template from scanned fingerprint
					self.dev.createTemplate()
					#store this newly created fingerprint
					self.dev.storeTemplate(positionNumber=fp_location, charBufferNumber=self.BUFF1)
					return True
			else:
				printline("scan failed")
				return None
		else:
			printline("scan failed")
			return None
		"""

	#enables power going into fingerprint sensor (turns oon FET)
	def enable(self):
		self.en.off()
		sleep_ms(params.ACTIVATION_DELAY)	#very short delay to allow power to flow into sensor

	#disables power going to fingerprint sensor (turns off FET)
	def disable(self):
		self.en.on() 

#class to hold batt level monitoring functionality
class Batt_Level:
	def __init__(self):
		self.val_pin = Pin(pconf.BATT_VAL)
		self.batt = ADC(self.val_pin)

	#function to calculate battery level from voltage divider read by ADC input
	def get_batt_level(self):
		#define resistances r1 and r2 (used to reduce analog input voltage)
		r1 = 1e6
		r2 = 1e5
		#read in batt ADC val
		adc_val = self.batt.read()
		level = adc_val*(1/4096)
		#calculate real voltage from voltage divider circuit, return result
		return (level/(r2/(r1+r2)))