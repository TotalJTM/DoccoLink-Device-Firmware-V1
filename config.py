"""
This is a configuration file for the Doccolink device v1.0
Declare and configurable item within this file
"""

#class to store the device pin configuration
class pin_configuration:
	#fingerprint pins
	FPR_TX 				= const(4)
	FPR_RX 				= const(5)
	FPR_EN 				= const(32)
	#buzzer pin
	BUZZER 				= const(13)
	#button pins
	NO_BTN 				= const(14)
	SELECT_BTN 			= const(15)
	YES_BTN 			= const(34)
	#cellular device pins
	CELL_RX 			= const(16)
	CELL_TX 			= const(17)
	CELL_WAKE 			= const(33)
	#additional SPI bus pins
	SPI_SCK 			= const(18)
	SPI_MISO 			= const(19)
	SPI_MOSI 			= const(23)
	SPI_SS 				= const(25)
	SPI_EN 				= const(26)
	#display pins
	DISP_SDA 			= const(21)
	DISP_SCL 			= const(22)
	DISP_EN 			= const(27)
	#pin for reading battery voltage
	BATT_VAL 			= const(35)

#class to store configuration options for the onboard buzzer
class buzzer_configuration:
	#PWM frequency that creates buzzer tone
	TONE				= const(400)
	#amount of time tone plays for
	TONE_LENGTH 		= const(750)
	#duration between tones
	WAIT				= const(5000)

#class to store information having to do with WiFi and cellular communications
class communication_configuration:
	#base url that device messages will be sent to (is HTTPS)
	#BASE_URL			= const("https://www.doccolink.com")
	BASE_URL			= "http://192.168.1.5"
	#URL path where initial device messages will be sent
	INIT_MESSAGE_PATH	= "/getappointments/alpha/v1/"
	#URL path where appointment reminder replies will be sent
	REPLY_MESSAGE_PATH 	= "/devicemessagehandler/alpha/v1/"

	#access point specific variables
	#access point ssid that is shown when user trys to connect to wifi network
	AP_SSID				= "Doccolink-Device"
	AP_PASSWORD			= ""

#class to store any and all extra parameters
class extra_params:
	#delay (in ms) for time between changing FET state and next command
	ACTIVATION_DELAY 	= const(3)
	#debug setting
	DEBUG 				= True
	#number of fingerprint reads to enroll patient fingerprint
	#MUST BE 1-5, CANNOT EXCEED 5
	NUM_OF_FINGERPRINT_SCANS 	= const(5)
	#Duration device will sleep between use cycles (in minutes, not seconds or ms)
	#conversion to ms handled in main.py
	DEEPSLEEP_DURATION			= const(60)