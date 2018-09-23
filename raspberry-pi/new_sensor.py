import socket
import os
import time
import sys
import Adafruit_DHT
import psutil
import RPi.GPIO as GPIO
import threading
import inspect
import ctypes
from w1thermsensor import W1ThermSensor

Trig_Pin = 26
Echo_Pin = 20
People_Pin = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(Trig_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Echo_Pin, GPIO.IN)
GPIO.setup(People_Pin, GPIO.IN)

global CPU_TEMP_STATE
global READ_TEMP_HUMID
global READ_DIS
global READ_TEMP

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

def get_time():
    return time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))

def get_temp():
    global READ_TEMP
    READ_TEMP = -1
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "01161b900cee")
    READ_TEMP = str(get_time() + "/" + '%0.2f' % sensor.get_temperature()
                   + "/00" + "/" + "0x00")

def server_init(name, host_ip, host_port):
    apply_ip = host_ip + r"/24"
    os.system("ip addr add " + apply_ip + " dev wlan0")
    print(get_time() +
          "Starting " + name)
    socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(name + "listen @ %s:%d!" % (host_ip, host_port))
    host_addr = (host_ip, host_port)
    socket_tcp.bind(host_addr)
    return socket_tcp


def server_Temp_sensor(host_ip="192.168.1.110", host_port=50):
    name = "Temp sensor server "
    socket_tcp = server_init(name, host_ip, host_port)
    global READ_TEMP
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(("Temp Humid Sensor:Time/Temp/PlaceHolder/ErrorCode").encode())
        while (1):
            try:
                thread_get_temp = threading.Thread(target=get_temp,
                                                   args=())
                thread_get_temp.start()
                time.sleep(1)
                if READ_TEMP == -1:
                    message = (get_time() + "/0/00/0x01")
                    stop_thread(thread_get_temp)
                else:
                    message = READ_TEMP
                socket_con.send((message).encode())

            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break

def main():
    threads = []

    thread_Temp_sensor = threading.Thread(target=server_Temp_sensor,
                                                args=())
    threads.append(thread_Temp_sensor)
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()