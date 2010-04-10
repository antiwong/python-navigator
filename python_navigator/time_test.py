# time_test.py

import time

last = time.time()
print (time.time() - last) * 1000

for i in range(10):
    now = time.time()
    if now != last:
        print (now - last) * 1000
        last = now
