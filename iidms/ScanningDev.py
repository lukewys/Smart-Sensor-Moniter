# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.21 19:32
# @Author  : flytocc
# @File    : ScanningDev.py
# @Software: PyCharm

import threading
import socket

GATEWAY = '192.168.1.'
SERVER_PORT = 50


class ScanningDev(threading.Thread):
    def __init__(self, dev_list, lock, thread_id, thread_num=32):
        super(ScanningDev, self).__init__()
        self.dev_list = dev_list
        self.lock = lock
        self.thread_id = thread_id
        self.thread_num = thread_num

    def run(self):
        assert self.thread_num == 16 or self.thread_num == 32, "thread_num argument must be 16, 32"

        for ip_last_part in range(self.thread_id * self.thread_num, (self.thread_id + 1) * self.thread_num):
            # create Socket，SOCK_STREAM default type is TCP
            socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # set timeout
            socket_tcp.settimeout(0.12)
            # server's ip and port
            server_ip = GATEWAY + str(ip_last_part)
            server_address = (server_ip, SERVER_PORT)
            # try to connect the server
            try:
                socket_tcp.connect(server_address)
            except:
                continue
            # close the connect
            socket_tcp.close()
            self.lock.acquire()
            self.dev_list.append(server_ip)
            self.lock.release()


if __name__ == "__main__":
    dev_list = []
    print('Scanning')

    for thread_id in range(32):
        ScanningDev(dev_list=dev_list,
                    lock=threading.Lock(),
                    thread_id=thread_id,
                    thread_num=32
                    ).start()


    def finished():
        print("Finished")
        print(dev_list)
        timer.cancel()

    timer = threading.Timer(5, finished)
    timer.start()
