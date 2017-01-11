#!/usr/bin/env python
# encoding: utf-8


"""
@version: 1.0
@author: libaofan
@contact: myway611@gmail.com
@software: PyCharm
@file: lock_util.py
@time: 2017/1/10 11:27
"""

from redlock import RedLock
import time
import threading
import os
import multiprocessing


process_lock = RedLock(
                'test_redlock',
                connection_details=[
                     {'host': 'redis1.host', 'port': 6379, 'db': 0, 'password': None},  # normal
                     {'host': 'redis2.host', 'port': 6379, 'db': 0, 'password': None},  # normal
                     {'host': 'redis3.host', 'port': 6379, 'db': 0, 'password': ''},  # error
                ],
                ttl=10000,  # 10 seconds
                retry_times=1,
                retry_delay=2,
                refresh=True,  # refresh ttl if have got the lock
                refresh_granularity='process')  # granularity : host(same mac) / process / thread


def _maintain_lock():
    print 'maintain lock begin . pid:%s tid:%s ' % (os.getpid(), threading.current_thread().ident)
    while True:
        time.sleep(5)
        locked = process_lock.acquire()
        print 'maintain lock success . pid:%s tid:%s locked:%s' \
              % (os.getpid(), threading.current_thread().ident, locked)


def get_lock_block():
    # 1 get the lock
    while not process_lock.acquire():
        print 'try get lock . sleep 10 seconds . pid:%s tid:%s' % (os.getpid(),threading.current_thread().ident)
        time.sleep(8)

    print 'get the lock pid:%s tid:%s' % (os.getpid(),threading.current_thread().ident)
    # 2 start a thread to maintain a lock
    t = threading.Thread(target=_maintain_lock)
    t.start()


if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=3)
    results = []
    for i in range(3):
        result = pool.apply_async(get_lock_block)
        results.append(result)
    time.sleep(100)
    pool.close()
