import threading
import time

def f():
    print("HHHHH")
    # call f() again in 60 seconds
    threading.Timer(3, f).start()

# start calling f now and every 60 sec thereafter

if __name__ == '__main__':
    f()