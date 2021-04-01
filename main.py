"""
Main program to run on device using all functions from premade classes
Must run in try, except loop in case of a crash. 
"""
from dev_funcs import printline
printline("device started")

#start try loop where main program runs
#try:
#create button object and check button state (wont be used immediately but we want the state ASAP)
from io_devices import Buttons
from time import sleep_ms, sleep
button = Buttons()
#sleep_ms(50) 	#handle debounce after wake (if buttons woke device)
button_state = button.read_buttons()

#do imports (they may take a few 100 ms to load so thats why they are imported after button read)
from file_funcs import FileIO
from display import Display
from config import extra_params as params
import dev_funcs, comms, io_devices
import machine, esp32

"""
Upon device wakeup, check the button state.
if the yes and no buttons are both pressed, this indicates the device should go into AP mode
if the yes, no and sel buttons are pressed, device should boot into UART mode
if yes, no and sel buttons are not pressed, device was awoken from deepsleep after timeout
if yes, no or sel button pressed, device was woken by user
"""
#create some objects for use within the program
dev_info = FileIO()	#get all of the device info from data.json
dev_time = dev_funcs.Recorded_Time(dev_info.last_known_time)	#create time object from last known time
ssd = Display()		#create object for OLED display
ssd.activate()		#activate display
batt = io_devices.Batt_Level()	#create battery monitor object

#put something on display
ssd.clear()
ssd.print_center_text_line("DoccoLink Device", 16)
ssd.print_center_text_line("Firmware V"+str(dev_info.firm_version),32)
ssd.update()
sleep(2)

#----- program begins to branch into different directions -----
#if yes and no buttons are pressed
#this leads to AP mode
printline(button_state)
if button_state["yes"] and button_state["no"] and not button_state["select"]:
	ssd.clear()
	ssd.print_text("Access Point Mode \n \n Connect to the device wifi, navigate to 192.168.4.1", True, 0)
	ssd.update()
	printline("AP Mode selected")
	sleep(10)

#if yes, no and select buttons are pressed
#this leads to UART control
elif button_state["yes"] and button_state["no"] and button_state["select"]:
	ssd.clear()
	ssd.print_text("UART Mode Set \n \n Connect the device to a computer to reprogram", True, 0)
	ssd.update()
	printline("UART Control selected")
	sleep(10)

#default case for program
#this should execute in a normal device cycle
else:
	#check if device was woken by deepsleep timer
	if not button_state["yes"] and not button_state["no"] and not button_state["select"]:
		#offset time by deepsleep duration (to keep accurate time)
		dev_time.offset_time(mins=params.DEEPSLEEP_DURATION)

	#boolean to show whether network, server had successful connections
	connected_to_network = False
	connected_to_server = False

	#connect to cellular network by constructing cellular comms object
	network_interface = comms.Dev_Cell()
	#check if cellular services have been successfully started
	if network_interface.start_cellular():
		connected_to_network = True
		printline("cellular started successfully")

	#if the cellular device doesnt start, we need to connect with WiFi
	else:
		#start wifi object
		network_interface = comms.Dev_WiFi(dev_info.wifi_networks)
		#check if wifi services have been successfully started
		if network_interface.start_wifi():
			connected_to_network = True
			printline("WiFi started successfully")

	#check if we connected to either cellular or wifi (have the same functionality)
	if connected_to_network:
		#construct initial device message to be sent to server
		mess = comms.Dev_Message(dev_info.dev_id, dev_info.server_pass, batt.get_batt_level())
		#get new appointment data by sendinging initial post
		success, datetime, appt_data = network_interface.send_initial_post(mess)
		printline(str(success) + " connection| " + str(datetime))

		#if the message was successfully transmitted and received, handle that new data
		if success:
			connected_to_server = True
			#remake device time object with new datetime from server 
			dev_time = dev_funcs.Recorded_Time(datetime)
			#check if we need to update appointment data (only if we have a new appt)
			if appt_data is not None:
				#iter through new appointments and add them to file system
				for appt in appt_data:
					printline("new appt " + appt.appointment_id + " added to system")
					dev_info.add_appointment(appt)


"""
Prepare for sleepmode
"""
#clear display before sleepmode
ssd.clear()
#save current time
dev_time.update_time()
dev_file.update_last_known_time()

printline("set wake and go to sleep")
#set the esp32 to wake if select button is pressed or yes/no pressed together
esp32.wake_on_ext0(pin = button.sel_pin, level = esp32.WAKEUP_ALL_LOW)
esp32.wake_on_ext1(pins = (button.yes_pin, button.no_pin), level = esp32.WAKEUP_ALL_LOW)
#deepsleep for time as specified in config.py, convert minutes to ms (60,000 ms in 1 min)
machine.deepsleep(int(params.DEEPSLEEP_DURATION*60e3))
#end of main loop, device is in sleep mode until pin interrupt (sel button) or wakeup
"""except KeyboardInterrupt:
    raise Exception('keyboard exit')
except Exception:
    #log your error and restart
    printline("runtime error")
    import time
    #delay for a short time
    time.sleep(5)
    #do a hard reset (like performing a power cycle)
    printline("resetting device")
    machine.reset()"""