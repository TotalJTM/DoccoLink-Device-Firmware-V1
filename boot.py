import esp
esp.osdebug(None)
#import webrepl
#webrepl.start()
import uos, machine
#import micropython garbage collector (reduces used mem)
import gc
#collect the garbage
gc.collect()
#set the allocation threshold to 100,000 (about 10/11 of allocated memory)
gc.threshold(100000)