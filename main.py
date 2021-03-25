

try:
    #your code here
except KeyboardInterrupt:
    raise Exception('keyboard exit')
except Exception:
    #log your error and restart
    print('error')
    import time
    time.delay(5)
    print('reset')