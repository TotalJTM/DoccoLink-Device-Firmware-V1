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
from time import sleep_ms, sleep, ticks_ms, ticks_diff

button = Buttons()
sleep_ms(50) 	#handle debounce after wake (if buttons woke device)
button_state = button.read_buttons()
printline(button_state)

from display import Display
ssd = Display()		#create object for OLED display
ssd.activate()		#activate display

from file_funcs import FileIO
from config import extra_params as params
import dev_funcs
#create some objects for use within the program
dev_info = FileIO()	#get all of the device info from data.json
dev_time = dev_funcs.Recorded_Time(dev_info.last_known_time)	#create time object from last known time

#put something on display if device was woken with interrupt
if button_state["yes"] and button_state["no"] and not button_state["select"]:
	ssd.clear()
	ssd.print_center_text_line("DoccoLink Device", 16)
	ssd.print_center_text_line("Firmware V"+str(dev_info.firm_version),32)
	ssd.update()
	sleep(2)

#do imports (they may take a few 100 ms to load so thats why they are imported after button read)
import comms, io_devices
import machine, esp32

batt = io_devices.Batt_Level()	#create battery monitor object
"""
Upon device wakeup, check the button state.
if the yes and no buttons are both pressed, this indicates the device should go into AP mode
if the yes, no and sel buttons are pressed, device should boot into UART mode
if yes, no and sel buttons are not pressed, device was awoken from deepsleep after timeout
if yes, no or sel button pressed, device was woken by user
"""


#----- program begins to branch into different directions -----
#if yes and no buttons are pressed
#this leads to AP mode
if button_state["yes"] and button_state["no"] and not button_state["select"]:
	ssd.clear()
	ssd.print_text("Access Point Mode \n \n Connect to the device wifi, navigate to 192.168.4.1", True, 0)
	ssd.update()
	printline("AP Mode selected")
	update
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
					if appt.cancelled:
						printline("appt " + str(appt.appointment_id) + " is cancelled, updating system")
						dev_info.cancel_appointment(appt.appointment_id)
					else:
						printline("new appt " + str(appt.appointment_id) + " added to system")
						dev_info.add_appointment(appt)

	#check appointments and see if any reminders need to be made
	curr_appointments = dev_info.get_appointments()
	#var to store state of whether user has used device while awake
	user_answered = True
	for appt in curr_appointments:
		#continue if the user has answered, will be set to False after yes/no button not pressed in wake cycle
		if user_answered:
			printline("appt: "+str(appt.appointment_id)+" | date: "+str(appt.appointment_date_time))
			time_difference = dev_time.compare_time(appt.appointment_date_time)
			printline(time_difference)
			#if the appointment time is past due, remove the appointment from the system
			if time_difference["appointment_passed"] is True:
				dev_info.remove_appointment(appt.appointment_id)
				printline("appointment removed for being outdated")

			#if the appointment was cancelled, display that to the user and get acknowledgment from user
			elif appt.cancelled:
				#display prompt to OLED screen
					ssd.clear()
					appt_date, appt_time = appt.get_formatted_date_and_time()
					text_to_display = "The appointment on " + appt_date + " at " + appt_time + " has been cancelled. Press any button to continue"
					ssd.print_text(text_to_display, True, 0)
					ssd.update()
					#set initial time for timeout counter
					init_time = ticks_ms()
					#create response variable
					response = None
					#create buzzer and start the buzzer timer
					buzzer = io_devices.Buzzer()
					buzzer.start_buzz()
					#while loop to look for patient response, will result in True, false answer or timeout (None)
					while (ticks_diff(ticks_ms(),init_time) < (params.ACTIVE_RESPONSE_WINDOW)) and response is None:
						#check if buzzer needs to be updated
						buzzer.update_buzz()
						#read button states
						button_state = button.read_buttons()
						#check if yes or no button pressed
						if button_state["yes"]:
							response = True
						if button_state["no"]:
							response = True
						if button_state["select"]:
							response = True
					#deactivate buzzer (if not already done)
					buzzer.deactivate()
					#if no response received, update user_answered state and go back to sleep
					if response is None:
						user_answered = False
					#otherwise, remove the appointment because its not necessary to hold onto anymore
					else:
						printline("user acknowledged appt cancellation, removing appt")
						dev_info.remove_appointment(appt.appointment_id)

			#remind patient of upcoming appointments (default case)
			else:
				#otherwise check if the appointment meets one of the appointment request intervals (hardcoded in dev_funcs)
				needs_reminder, answer_num = dev_time.check_if_appt_reminder_necessary(appt)
				#if a reminder is needed, execute this logic
				if needs_reminder:
					#display prompt to OLED screen
					ssd.clear()
					appt_date, appt_time = appt.get_formatted_date_and_time()
					text_to_display = "Will you attend the appointment on \n " + appt_date + " \n at \n " + appt_time
					ssd.print_text(text_to_display, True, 0)
					ssd.update()
					#set initial time for timeout counter
					init_time = ticks_ms()
					#create response variable
					response = None
					#create buzzer and start the buzzer timer
					buzzer = io_devices.Buzzer()
					buzzer.start_buzz()
					#while loop to look for patient response, will result in True, false answer or timeout (None)
					while (ticks_diff(ticks_ms(),init_time) < (params.ACTIVE_RESPONSE_WINDOW)) and response is None:
						#check if buzzer needs to be updated
						buzzer.update_buzz()
						#read button states
						button_state = button.read_buttons()
						#check if yes or no button pressed
						if button_state["yes"]:
							response = True
						if button_state["no"]:
							response = False
					#deactivate buzzer (if not already done)
					buzzer.deactivate()
					#handle a yes or no message
					if response is not None:
						if response is True:
							text_to_display = "You have selected \n \n 'Yes'"
						else:
							text_to_display = "You have selected \n \n 'No'"
						ssd.clear()
						ssd.print_text(text_to_display, True, 0)
						ssd.update()
						sleep(4)

						confirmed = False
						fp = io_devices.Fingerprint()
						fp.activate()
						update_text = True
						while confirmed is False:
							if update_text:
								ssd.clear()
								ssd.print_text("Please confirm your identity with the fingerprint scanner", True, 0)
								ssd.update()
								update_text = False

							if fp.scan_fingerprint(50) == True:
								match_accuracy = fp.match_fingerprint()
								if match_accuracy is not None:
									if match_accuracy > params.FP_MATCH_THRESHOLD:
										#matched fingerprint, new appt answer can be sent to server
										dev_info.new_appointment_answer(appt.appointment_id, response, dev_time, answer_num)
										mess = comms.Dev_Message(dev_info.dev_id, dev_info.server_pass, batt.get_batt_level())
										updated_appt = dev_info.get_appointments(appt.appointment_id)
										mess.include_appointment_answer(updated_appt)
										success, reply = network_interface.send_appointment_reply_post(mess)
										printline("reply: " + str(success))
										printline(reply)
										if success:
											dev_info.update_appointment_answer_status(appt.appointment_id, True, answer_num)
											ssd.clear()
											ssd.print_text("Message has been sent, thank you for using DoccoLink", True, 0)
											ssd.update()
											sleep(3)
											confirmed = True
										else:
											dev_info.update_appointment_answer_status(appt.appointment_id, False, answer_num)
											ssd.clear()
											ssd.print_text("Message has not been sent \n message will be sent when device reconnects to network", True, 0)
											ssd.update()
											sleep(3)
											confirmed = True

								else:
									#handle a failed match
									ssd.clear()
									ssd.print_text("No matched fingerprint, please try again", True, 0)
									ssd.update()
									sleep(3)
									update_text = True

							#read in buttons
							button_state = button.read_buttons()
							#if select button is pressed, cancel fingerprint read
							if button_state["select"]:
								ssd.clear()
								ssd.print_text("Fingerprint scan cancelled by user", True, 0)
								ssd.update()
								sleep(3)
								break
						else:
							user_answered = False

	#if the user answered a message or interacted with device
	#if user_answered:

	#check for any appointment answers that have not been sent yet
	unsent_appts = dev_info.get_unsent_appointment_answers()
	for appt in unsent_appts:
		mess = comms.Dev_Message(dev_info.dev_id, dev_info.server_pass, batt.get_batt_level())
		mess.include_appointment_answer(appt[0])
		success, reply = network_interface.send_appointment_reply_post(mess)

		if success:
			printline("unsent message sent to server was successful " + str(appt[0].appointment_id))
			dev_info.update_appointment_answer_status(appt[0].appointment_id, True, appt[1])
		else:
			printline("unsent message sent to server was unsuccessful: " + str(appt[0].appointment_id))

"""
Prepare for sleepmode
"""
#clear display before sleepmode
ssd.clear()
ssd.deactivate()
#save current time
dev_time.update_time()
dev_info.update_last_known_time(dev_time)

printline("set wake and go to sleep")
#set the esp32 to wake if select button is pressed or yes/no pressed together
esp32.wake_on_ext0(pin = button.sel_pin, level = esp32.WAKEUP_ALL_LOW)
esp32.wake_on_ext1(pins = (button.yes_pin, button.no_pin), level = esp32.WAKEUP_ALL_LOW)
#deepsleep for time as specified in config.py, convert minutes to ms (60,000 ms in 1 min)
machine.deepsleep(int(params.DEEPSLEEP_DURATION*60e3))
#end of main loop, device is in sleep mode until pin interrupt (sel button) or wakeup

#except errno 113 ehostunreach
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