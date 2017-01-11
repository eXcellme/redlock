### Forked from https://github.com/glasslion/redlock

For distributed locks in long-running jobs, you need to prevent lock expiration. 

This version of the redlock can be periodically updated lock expiration time (ttl) when a lock is acquired and the same host/process/thread try lock again.

### Demo :

```
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

```

refresh : True / False

refresh_granularity : host / process / thread

----------------
![RedLock logo](https://github.com/glasslion/redlock/raw/master/docs/assets/redlock-small.png)

## RedLock - Distributed locks with Redis and Python

[![Build Status](https://travis-ci.org/glasslion/redlock.svg?branch=master)](https://travis-ci.org/glasslion/redlock)

This library implements the RedLock algorithm introduced by [@antirez](http://antirez.com/)


### Yet another ...
There are already a few redis based lock implementations in the Python world, e.g.  [retools](https://github.com/bbangert/retools),  [redis-lock](https://pypi.python.org/pypi/redis-lock/0.2.0). 

However, these libraries can only work with *single-master* redis server. When the Redis master goes down, your application has to face a single point of failure . We can't rely on the master-slave replication, because Redis replication is asynchronous.

> This is an obvious race condition with the master-slave replication model :
>  1. Client A acquires the lock into the master.
>  2. The master crashes before the write to the key is transmitted to the slave.
>  3. The slave gets promoted to master.
>  4. Client B acquires the lock to the same resource A already holds a lock for. SAFETY VIOLATION!

### A quick introduction to the RedLock algorithm
To resolve this problem, the Redlock algorithm assume we have `N` Redis masters. These nodes are totally independent (no replications). In order to acquire the lock, the client will try to acquire the lock in all the N instances sequentially. If and only if the client was able to acquire the lock in the majority (`(N+1)/2`)of the instances, the lock is considered to be acquired.

The detailed description of the RedLock algorithm can be found in the Redis documentation: [Distributed locks with Redis](http://redis.io/topics/distlock).

### APIs

The `redlock.RedLock` class shares a similar API with the `threading.Lock` class in the  Python Standard Library.

#### Basic Usage

```python
from redlock import RedLock
# By default, if no redis connection details are 
# provided, RedLock uses redis://127.0.0.1:6379/0
lock =  RedLock("distributed_lock")
lock.acquire()
do_something()
lock.release()
```

#### With Statement / Context Manager

As with `threading.Lock`, `redlock.RedLock` objects are context managers thus support the [With Statement](https://docs.python.org/2/reference/datamodel.html#context-managers). This way is more pythonic and recommended.

```python
from redlock import RedLock
with RedLock("distributed_lock"):
    do_something()
```

#### Specify multiple Redis nodes

```python
from redlock import RedLock
with RedLock("distributed_lock", 
              connection_details=[
                {'host': 'xxx.xxx.xxx.xxx', 'port': 6379, 'db': 0},
                {'host': 'xxx.xxx.xxx.xxx', 'port': 6379, 'db': 0},
                {'host': 'xxx.xxx.xxx.xxx', 'port': 6379, 'db': 0},
                {'host': 'xxx.xxx.xxx.xxx', 'port': 6379, 'db': 0},
              ]
            ):
    do_something()
```

The `connection_details` parameter expects a list of keyword arguments for initializing Redis clients.
Other acceptable Redis client arguments  can be found on the [redis-py doc](http://redis-py.readthedocs.org/en/latest/#redis.StrictRedis).

#### Reuse Redis clients with the RedLockFactory

Usually the connection details of the Redis nodes are fixed. `RedLockFactory` can help reuse them, create multiple RedLocks but only initialize the clients once.

```python
from redlock import RedLockFactory
factory = RedLockFactory(
    connection_details=[
        {'host': 'xxx.xxx.xxx.xxx'},
        {'host': 'xxx.xxx.xxx.xxx'},
        {'host': 'xxx.xxx.xxx.xxx'},
        {'host': 'xxx.xxx.xxx.xxx'},
    ])

with factory.create_lock("distributed_lock"):
    do_something()

with factory.create_lock("another_lock"):
    do_something()
```
