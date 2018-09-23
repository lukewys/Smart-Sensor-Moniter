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


def checkdist(Trig_Pin=26, Echo_Pin=20):
    GPIO.output(Trig_Pin, GPIO.HIGH)
    time.sleep(0.00015)
    GPIO.output(Trig_Pin, GPIO.LOW)
    while not GPIO.input(Echo_Pin):
        pass
    t1 = time.time()
    while GPIO.input(Echo_Pin):
        pass
    t2 = time.time()
    return (t2 - t1) * 340 * 100 / 2


def get_dis():
    global READ_DIS
    READ_DIS = -1

    READ_DIS = str(get_time() + "/" + '%0.2f' % checkdist() + "/00" + "/" + "0x00")


'''
try:
    while True:
        print ('Distance:%0.2f cm' % checkdist())
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    '''


def detect_people(People_Pin=21):
    if GPIO.input(People_Pin):
        return (get_time() + "/" + "True" + "/" + "00/" + "0x00")
    else:
        return (get_time() + "/" + "False" + "/" + "00/" + "0x00")


def get_temp_humid():
    sensor = Adafruit_DHT.DHT11
    gpio = 17
    humidity = None
    temperature = None
    global READ_TEMP_HUMID
    READ_TEMP_HUMID = -1
    while humidity is None or temperature is None:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio)
    READ_TEMP_HUMID = (get_time() + "/" + str(temperature)
                       + "/" + str(humidity) + "/" + "0x00")


def get_time():
    return time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))


'''
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return (res.replace("temp=", "").replace("'C\n", ""))


def getCPUstate(interval=0.05):
    return (" CPU: " + str(psutil.cpu_percent(interval)) + "%")
'''

def get_temp():
    global READ_TEMP
    READ_TEMP = -1
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "01161b900cee")
    READ_TEMP = str(get_time() + "/" + '%0.2f' % sensor.get_temperature()
                   + "/00" + "/" + "0x00")

def get_CPU():
    global CPU_TEMP_STATE
    CPU_TEMP_STATE = -1
    cputemp = os.popen('vcgencmd measure_temp').readline()
    cputemp = (cputemp.replace("temp=", "").replace("'C\n", ""))
    cpustate = (str(psutil.cpu_percent(0.8)))
    CPU_TEMP_STATE = (get_time() + "/" +
                      str(cputemp + "/" + cpustate) + "/" + "0x00")


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


def server_CPU_sensor(host_ip="192.168.1.105", host_port=50):
    name = "CPU sensor server "
    socket_tcp = server_init(name, host_ip, host_port)
    global CPU_TEMP_STATE
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(("CPU Sensor:Time/Temp/CPUstate/ErrorCode").encode())
        while (1):
            try:
                thread_get_CPU = threading.Thread(target=get_CPU,
                                                  args=())
                thread_get_CPU.start()
                time.sleep(1)
                if CPU_TEMP_STATE == -1:
                    message = (get_time() + "/0/0/0x01")
                    stop_thread(thread_get_CPU)
                else:
                    message = CPU_TEMP_STATE
                socket_con.send((message).encode())

            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break


def server_Distance_sensor(host_ip="192.168.1.106", host_port=50):
    name = "Distance sensor server "
    socket_tcp = server_init(name, host_ip, host_port)
    global READ_Dis
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(
            ("Distance Sensor:Time/Distance/PlaceHolder/ErrorCode").encode())

        while (1):
            try:

                thread_get_dis = threading.Thread(target=get_dis,
                                                  args=())
                thread_get_dis.start()
                time.sleep(1)
                if READ_DIS == -1:
                    message = (get_time() + "/0/00/0x01")
                    stop_thread(thread_get_dis)
                else:
                    message = READ_DIS

                socket_con.send((message).encode())

            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break


def server_Infrared_sensor(host_ip="192.168.1.107", host_port=50):
    name = "Infrared sensor server "
    socket_tcp = server_init(name, host_ip, host_port)

    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(
            ("Infrared Sensor:Time/Infrared_Exists/PlaceHolder/ErrorCode").encode())
        while (1):
            try:
                socket_con.send(str(detect_people()).encode())
                time.sleep(1)

            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break


def server_Temp_Humid_sensor(host_ip="192.168.1.108", host_port=50):
    name = "Temp Humid sensor server "
    socket_tcp = server_init(name, host_ip, host_port)
    global READ_TEMP_HUMID
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(("Temp Humid Sensor:Time/Temp/Humid/ErrorCode").encode())
        while (1):
            try:
                thread_get_temp_humid = threading.Thread(target=get_temp_humid,
                                                   args=())
                thread_get_temp_humid.start()
                time.sleep(2)
                if READ_TEMP_HUMID == -1:
                    message = (get_time() + "/0/0/0x01")
                    stop_thread(thread_get_temp_humid)
                else:
                    message = READ_TEMP_HUMID
                socket_con.send((message).encode())

            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break

def server_Temp_sensor(host_ip="192.168.1.109", host_port=50):
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
    thread_CPU_sensor = threading.Thread(target=server_CPU_sensor,
                                         args=())
    threads.append(thread_CPU_sensor)
    thread_Distance_sensor = threading.Thread(target=server_Distance_sensor,
                                              args=())
    threads.append(thread_Distance_sensor)
    thread_Infrared_sensor = threading.Thread(target=server_Infrared_sensor,
                                              args=())
    threads.append(thread_Infrared_sensor)
    thread_Temp_Humid_sensor = threading.Thread(target=server_Temp_Humid_sensor,
                                                args=())
    threads.append(thread_Temp_Humid_sensor)
    #thread_Temp_sensor = threading.Thread(target=server_Temp_sensor,
    #                                           args=())
    #threads.append(thread_Temp_sensor)
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()

# socket_tcp.close()
