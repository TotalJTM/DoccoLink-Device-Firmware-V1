"""
holds code having to do with the SSD1306 display
"""

from config import pin_configuration as pconf
from config import extra_params as params
from dev_funcs import printline
from machine import Pin, I2C
import ssd1306
from time import sleep_ms

#display class handles the SSD1306 on the device
#to use this class, create the display object and "activate" the display
class Display:
	def __init__(self):
		#create pin objects for SDA, SCL and enable pin for the SSD1306 interface
		#pullups are necessary as the board has no SDA or SCL pullup
		self.SDA_pin = Pin(pconf.DISP_SDA, Pin.OUT, Pin.PULL_UP)
		self.SCL_pin = Pin(pconf.DISP_SCL, Pin.OUT, Pin.PULL_UP)
		self.EN_pin = Pin(pconf.DISP_EN, Pin.OUT)

		#create initial object to store display object (when its active)
		self.display = None

		#set enable to HIGH state so display is 'off'
		self.disable()

	def activate(self):
		#try to create the I2C object with defined Pins
		try:
			#enable display (supply display with power)
			self.enable()
			#create I2C object to communicate with SSD1306
			i2c = I2C(scl=self.SCL_pin, sda=self.SDA_pin)
			#create display object defining SSD1306
			self.display = ssd1306.SSD1306_I2C(128, 64, i2c)
			#return true since display is successfully activated
			return True
		except:
			#if I2C creation has failed, print a message
			#print("I2C display not set up")
			#ensure display var is set to None
			self.display = None
			#return false since display is not started
			return False

	#function to deactivae display after use
	#turns OLED off and destroys display object
	def deactivate(self):
		self.disable()
		self.display = None

	#function to enable display by providing power through FET
	def enable(self):
		self.EN_pin.off()	#set fet low to turn on FET
		sleep_ms(params.ACTIVATION_DELAY)	#very short delay to allow power to flow into display

	#function to disable display by removing power through FET
	def disable(self):
		self.EN_pin.on()	#set fet high to turn off FET

	#function to clear display of all data
	#takes a true or false arg, will update display if yes
	def clear(self, show=True):
		self.display.fill(0)
		if show:
			self.update()

	#update display with current buffered info
	def update(self):
		self.display.show()

	def print_center_text_line(self, text, yloc):
		#display text but make text centered (manipulate x coord)
		#each ASCII char is 8 pixel in height and width, max 16 chars
		self.display.text(text, (64-(len(text)*4)), yloc)

	def print_text_line(self, text, xloc, yloc):
		#display text according to x and y locations defined
		#max 16 chars
		self.display.text(text, xloc, yloc)

	def print_text(self, text, centered, start_line=0):
		#split the string into words (without spaces)
		split_text = text.split(' ')
		#create new array to store combined words
		new_display_text = [""]
		#move through the split text array
		for seg in split_text:
			#if the current index+new word is greater than 16 (max char per line)
			if (len(new_display_text[-1])+len(seg)+1) <= 16:
				#add word to current index
				new_display_text[-1] = new_display_text[-1] + ' ' + seg
			else:
				#otherwise, make a new index and fill it with word
				new_display_text.append(seg)
		#move through display text array with an index number
		for i, text in enumerate(new_display_text):
			#if we are under 9 rows (max 8 rows on SSD1306)
			if (i+start_line) <= 8:
				#if the text is supposed to be centered
				if centered:
					#print centered text to OLED
					self.print_center_text_line(text, ((i+start_line)*8))
				else:
					#print non-centered text to OLED
					self.print_text_line(text, 0, ((i+start_line)*8))
			else:
				#print overflow text if more than 8 rows
				printline("OLED exceeded: " + text)
		#update display
		self.update()