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


"""
虚拟出4个IP地址，并创建4个服务器，接收连接后以固定时间发送传感器数据
"""


# 针脚设置
Trig_Pin = 26
Echo_Pin = 20
People_Pin = 21

# GPIO设置
GPIO.setmode(GPIO.BCM)
GPIO.setup(Trig_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Echo_Pin, GPIO.IN)
GPIO.setup(People_Pin, GPIO.IN)

# 全局变量声明，用于多线程读取数据，判断延迟
global CPU_TEMP_STATE
global READ_TEMP_HUMID
global READ_DIS
global READ_TEMP

def _async_raise(tid, exctype):
    """
    用于杀进程的函数
    :param tid: 线程id
    :param exctype: SystemExit
    """

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
    """
    停止进程
    :param thread: 进程
    """
    _async_raise(thread.ident, SystemExit)


def checkdist(Trig_Pin=26, Echo_Pin=20):
    """
    用HC-SR04超声波传感器读取距离
    :param Trig_Pin:Trig针脚
    :param Echo_Pin:Echo针脚
    :return 距离（cm）
    """
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
    """
    多线程时读取距离的线程
    数据存入READ_DIS
    """
    global READ_DIS
    READ_DIS = -1
    READ_DIS = str(get_time() + "/" + '%0.2f' % checkdist() + "/00" + "/" + "0x00")


def detect_people(People_Pin=21):
    """
    用HC-SR501红外传感器进行人体监测的函数
    :param People_Pin:电平输出针脚
    :return:数据字符串
    """
    if GPIO.input(People_Pin):
        return (get_time() + "/" + "1" + "/" + "00/" + "0x00")
    else:
        return (get_time() + "/" + "0" + "/" + "00/" + "0x00")


def get_temp_humid():
    """
    读取DHT11的温度、湿度
    数据存入READ_TEMP_HUMID
    """
    sensor = Adafruit_DHT.DHT11
    gpio = 17  # 传感器数据针脚
    humidity = None
    temperature = None
    global READ_TEMP_HUMID
    READ_TEMP_HUMID = -1
    while humidity is None or temperature is None:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio)
    READ_TEMP_HUMID = (get_time() + "/" + str(temperature)
                       + "/" + str(humidity) + "/" + "0x00")


def get_time():
    """
    生成时间戳
    :return: 时间戳
    """
    return time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))


def get_CPU():
    """
    读取当前CPU温度以及当前0.8秒钟CPU的平均使用率
    数据存入CPU_TEMP_STATE变量
    """
    global CPU_TEMP_STATE
    CPU_TEMP_STATE = -1
    cputemp = os.popen('vcgencmd measure_temp').readline()
    cputemp = (cputemp.replace("temp=", "").replace("'C\n", ""))
    cpustate = (str(psutil.cpu_percent(0.8)))
    CPU_TEMP_STATE = (get_time() + "/" +
                      str(cputemp + "/" + cpustate) + "/" + "0x00")


def server_init(name, host_ip, host_port):
    """
    服务器初始化函数
    :param name: 服务器名
    :param host_ip: 想要创建的传感器IP地址
    :param host_port: 想要创建的传感器IP端口
    :return: socket_tcp类
    """
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
    socket_tcp = server_init(name, host_ip, host_port)  # 创建服务器
    global CPU_TEMP_STATE
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()  # 等待连接
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(("CPU Sensor:Time/Temp/CPUstate/ErrorCode").encode())  # 数据说明
        while (1):
            try:
                # 创建线程
                thread_get_CPU = threading.Thread(target=get_CPU,
                                                  args=())
                thread_get_CPU.start()
                time.sleep(1)
                # 判断超时
                if CPU_TEMP_STATE == -1:
                    message = (get_time() + "/0/0/0x01")
                    stop_thread(thread_get_CPU)
                else:
                    message = CPU_TEMP_STATE
                socket_con.send((message).encode())  # 发送数据
            # 处理异常
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
    socket_tcp = server_init(name, host_ip, host_port)  # 创建服务器
    global READ_Dis
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()  # 等待连接
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(
            ("Distance Sensor:Time/Distance/PlaceHolder/ErrorCode").encode())  # 数据说明

        while (1):
            try:
                # 创建线程
                thread_get_dis = threading.Thread(target=get_dis,
                                                  args=())
                thread_get_dis.start()
                time.sleep(1)
                # 判断超时
                if READ_DIS == -1:
                    message = (get_time() + "/0/00/0x01")
                    stop_thread(thread_get_dis)
                else:
                    message = READ_DIS

                socket_con.send((message).encode())  # 发送数据
            # 处理异常
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
    socket_tcp = server_init(name, host_ip, host_port)  # 创建服务器

    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()  # 等待连接
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(
            ("Infrared Sensor:Time/Infrared_Exists/PlaceHolder/ErrorCode").encode())  # 数据说明
        while (1):
            try:
                socket_con.send(str(detect_people()).encode())  # 发送数据
                time.sleep(1)
            # 处理异常
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
    socket_tcp = server_init(name, host_ip, host_port)  # 创建服务器
    global READ_TEMP_HUMID
    while (1):
        socket_tcp.listen(10)
        socket_con, (client_ip, client_port) = socket_tcp.accept()  # 等待连接
        print(get_time() + name +
              ": Connection accepted from %s." % client_ip)
        socket_con.send(("Temp Humid Sensor:Time/Temp/Humid/ErrorCode").encode())  # 数据说明
        thread_get_temp_humid = threading.Thread(target=get_temp_humid,
                                                 args=())
        thread_get_temp_humid.start()
        time.sleep(2)
        while (1):
            try:
                time.sleep(1)
                # 判断超时
                if READ_TEMP_HUMID == -1:
                    message = (get_time() + "/0/0/0x01")
                    stop_thread(thread_get_temp_humid)
                else:
                    message = READ_TEMP_HUMID
                    message=str(get_time()+message[20:])
                socket_con.send((message).encode())  # 发送数据

                time.sleep(1)
                if READ_TEMP_HUMID == -1:
                    message = (get_time() + "/0/0/0x01")
                else:
                    message = READ_TEMP_HUMID
                    message=str(get_time()+message[20:])
                socket_con.send((message).encode())  # 发送数据
                # 创建线程
                thread_get_temp_humid = threading.Thread(target=get_temp_humid,
                                                         args=())
                thread_get_temp_humid.start()
            # 处理异常
            except(BrokenPipeError):
                print(get_time()
                      + name + ": Disconnected")
                break
            except(ConnectionResetError):
                print(get_time()
                      + name + ": Connection reset by peer")
                break


def main():
    threads = []  # 创建线程列表

    # 创建线程并添加进线程列表
    thread_CPU_sensor = threading.Thread(target=server_CPU_sensor,
                                         args=("192.168.1.105",50))
    threads.append(thread_CPU_sensor)
    thread_Distance_sensor = threading.Thread(target=server_Distance_sensor,
                                              args=("192.168.1.106",50))
    threads.append(thread_Distance_sensor)
    thread_Infrared_sensor = threading.Thread(target=server_Infrared_sensor,
                                              args=("192.168.1.107",50))
    threads.append(thread_Infrared_sensor)
    thread_Temp_Humid_sensor = threading.Thread(target=server_Temp_Humid_sensor,
                                                args=("192.168.1.108",50))
    threads.append(thread_Temp_Humid_sensor)

    # 开始所有线程
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()


