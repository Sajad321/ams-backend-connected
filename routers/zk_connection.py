
from zk import ZK, const

conn = None
# create ZK instance
zk = ZK('192.168.0.115', port=4370, timeout=5,
        password=0, force_udp=False, ommit_ping=False)
try:
    # connect to device
    conn = zk.connect()
    # disable device, this method ensures no activity on the device while the process is run
    # conn.disable_device()
except Exception as e:
    print("Process terminate : {}".format(e))
