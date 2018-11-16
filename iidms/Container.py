# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.22 15:29
# @Author  : flytocc
# @File    : Container.py
# @Software: PyCharm

import threading
import time

import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox

import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import socket

import json

from DataDisplay import DrawPic, Tree


class Container(LabelFrame):
    def __init__(self, master, ip, port):
        # init frame
        super(Container, self).__init__(master,
                                        labelanchor='ne',  # 标签显示位置, ne为右上角的上边框
                                        text="仪表 %s:%d" % (ip, port),  # 标签内容
                                        )
        self.pack(fill='both', expand='true', side='top')

        # server info ip:port
        self.ip, self.port = ip, port

        # data
        self.data_dict = {}  # save the data got from sever for store
        # data for treeview and matplotlib
        self.data_ys_list = [[], [], [], [], []]  # [[timestamp], [data1], [data2], [error], [index]]

        # some flag to stop the treeview and matplotlib
        self.stop_get_data_flag = False
        self.stop_refresh_flag = False

        # refresh the online dev list
        master.dev_online.add(ip)  # add ip to dev_online

        # create a frame to put labels and buttons
        head_frame = Frame(self)
        head_frame.pack(fill='both', expand='true', side='top')

        # label 时段
        time_label = Label(head_frame, text='时段')
        time_label.grid(column=0, row=0)

        # combobox 创建一个下拉列表用于选择时段
        self.time_chosen = Combobox(head_frame, width=14, textvariable=tk.StringVar(), state='readonly')
        self.time_chosen['values'] = ('实时60秒', '近三分钟', '近十分钟')  # 设置下拉列表的值
        self.time_chosen.grid(column=1, row=0)  # 设置其在界面中出现的位置  column代表列   row 代表行

        def time_choose_adaptor(fun, **kwds):  # 传递参数
            # 事件处理函数的适配器，相当于中介
            return lambda event, fun=fun, kwds=kwds: fun(event, **kwds)

        def time_choose(event, self):  # 下拉列表触发函数
            chosen = self.time_chosen.get()
            if chosen == '实时60秒':  # '实时60秒'
                pass
                # self.stop_refresh_flag = False

            else:  # '实时60秒'
                # self.stop_refresh_flag = True
                # 弹出一个新的子窗口
                tl = tk.Toplevel()
                f = Figure(figsize=(8, 5), dpi=100)
                canvas = FigureCanvasTkAgg(f, master=tl)
                canvas.get_tk_widget().pack(fill='both', expand='true', side='top')
                ax = f.add_subplot(111)
                ax2 = ax.twinx()
                mpl.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
                mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
                ax.set_ylabel('data1')  # y轴标题 左
                ax2.set_ylabel('data2')
                ax.grid()  # 显示网格

                # 当数据量不足时尽可能用多的数据
                data_len = 0
                if chosen == '近三分钟':
                    if len(self.data_ys_list[1]) >= 180:
                        data_len = -180
                    else:
                        data_len = -len(self.data_ys_list[1])
                if chosen == '近十分钟':
                    if len(self.data_ys_list[1]) >= 600:
                        data_len = -600
                    else:
                        data_len = -len(self.data_ys_list[1])

                # 添加折线图
                ax.plot(self.data_ys_list[4][data_len:], self.data_ys_list[1][data_len:], lw=2, color="blue")  # lw线宽
                ax2.plot(self.data_ys_list[4][data_len:], self.data_ys_list[2][data_len:], lw=2, color="red")  # 及线颜色

                # 添加散点图 显示错误码
                dot = ax.scatter([], [], c='orange', edgecolors='none', s=50)
                dot.set_offsets(self.data_ys_list[3])

                # 不显示横坐标刻度标签
                ax.set_xticks([])

                # 设置横坐标标题
                t = self.ip + ": " + chosen + "的数据"  # eg: "192.168.1.1: 仅三分钟的数据"
                ax.set_title(u'%s' % t)

                # 显示数据的具体起止时间
                start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.data_ys_list[0][-1]))
                stop_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.data_ys_list[0][data_len]))
                ax.set_xlabel("%s  --  %s" % (start_time, stop_time))

                # 设置两个纵轴其标签刻度的颜色
                for label in ax.get_yticklabels():
                    label.set_color("blue")
                for label in ax2.get_yticklabels():
                    label.set_color("red")

                # 生成图像
                canvas.show()

        self.time_chosen.bind("<<ComboboxSelected>>",
                              time_choose_adaptor(time_choose, self=self))  # 下拉列表框被选中时，绑定time_chooe()函数

        # button被点击之后会被执行
        def click_start():  # 当action_start被点击时,该函数则生效
            self.stop_refresh_flag = False
            self.canvas.pause_draw = False
            # self.refresh()

        action_start = Button(head_frame, text="开始", command=click_start)  # 创建一个按钮
        action_start.grid(column=2, row=0)  # 设置其在界面中出现的位置 column代表列 row 代表行

        def click_stop():  # 当action_stop被点击时,该函数则生效
            self.stop_refresh_flag = True
            self.canvas.pause_draw = True

        action_stop = Button(head_frame, text="暂停", command=click_stop)
        action_stop.grid(column=3, row=0)

        def click_close():  # 当action_close被点击时,该函数则生效
            if len(master.dev_online) > 1:
                if tk.messagebox.askyesno(title='提示', message='面板关闭后将断开与设备的连接。断开连接后将无法继续获取数据。是否退出？') == True:
                    self.stop_get_data_flag = True

                    # remove ip from dev_line
                    master.dev_online.remove(ip)

                    # 销毁面板
                    self.destroy()

            else:
                if tk.messagebox.askyesno(title='提示', message='这是最后一个面板，关闭后将退出程序。是否确定？') == True:
                    self.stop_get_data_flag = True

                    # 关闭并销毁窗口
                    master.master.quit()
                    master.master.destroy()

        action_close = Button(head_frame, text="关闭", command=click_close)
        action_close.grid(column=5, row=0)

        # father of canvas and treeview
        pw = PanedWindow(self, orient="horizontal")
        pw.pack(fill='both', expand='true')

        # Canvas
        self.canvas_frame = Frame(pw)
        pw.add(self.canvas_frame)
        self.canvas = DrawPic(self.canvas_frame, self.data_ys_list)  # 创建图像

        # Treeview
        self.tree_frame = Frame(pw)
        pw.add(self.tree_frame)
        self.tree = Tree(self.tree_frame)  # 绘制表格

        threading.Thread(target=self.get_data, args=(master,)).start()  # 连接server 并获取数据
        self.refresh()
        self.canvas.show()

    # Refresh
    def refresh(self):
        if self.stop_refresh_flag == False:
            self.tree.update_tree(self.data_dict, self.time_chosen.get())

        self.after(1000, self.refresh)

    # 连接并获取数据
    def get_data(self, master):
        # create Socket，SOCK_STREAM default type is TCP
        socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server's ip and port
        server_address = (self.ip, self.port)
        # try to connect the server
        try:
            socket_tcp.connect(server_address)
        except:
            return False

        # 接收服务器发来的欢迎数据
        data = socket_tcp.recv(512).decode()

        # 接收服务器发来的数据
        num = 0
        index = 0
        while (True):
            for j in range(60):
                # 窗口关闭时 立即断开连接 并写数据入文件
                if master.save_data_right_now_flag == True or self.stop_get_data_flag == True:
                    with open("./data/%s.json" % self.ip, 'a') as f:
                        json.dump(self.data_dict, f)

                    # 断开server连接
                    socket_tcp.close()
                    print("socket close: %s" % self.ip)

                    return

                data_row_str = socket_tcp.recv(512).decode()
                data_str_ary = data_row_str.split('/')
                timestamp_int = int(time.time()) + 1  # 加1秒为了容错
                self.data_dict[timestamp_int] = data_str_ary

                # 记录时间戳
                self.data_ys_list[0].append(timestamp_int)

                # 错误码 画散点图
                if data_str_ary[3] != '0x00':
                    self.data_ys_list[3].append((index, 15))

                # 记录index
                self.data_ys_list[4].append(index)

                # 记录data1 data2 画折线图
                for i in range(1, 3):
                    self.data_ys_list[i].append(float(data_str_ary[i]))

                if num > 600:
                    self.data_dict.pop(timestamp_int - 600)  # data_dict 最大容量为600
                else:
                    num += 1

                index += 1

            # 每60s写文件一次
            with open("./data/%s.json" % self.ip, 'a') as f:
                json.dump(self.data_dict, f)


if __name__ == "__main__":
    from iidms.VerticalScrolledFrame import VerticalScrolledFrame

    root = tk.Tk()
    screenwidth = root.winfo_screenwidth()  # 屏幕宽度
    screenheight = root.winfo_screenheight()  # 屏幕高度
    size = '%dx%d+%d+%d' % (1000, 500, (screenwidth - 1000) / 2,
                            (screenheight - 500) / 2)  # window_H window_W 为窗口的 高度 宽度
    root.geometry(size)
    root.title("智能仪表数据监视系统")  # 设置标题
    # root.resizable(1, 0)  # 宽度 高度是否可变 0 不可变
    root.iconbitmap('./ico/setting.ico')  # 设置图标

    vsf = VerticalScrolledFrame(root)
    # vsf.pack()
    vsf.place(relwidth=1, relheight=1)

    con = Container(vsf.interior, '192.168.1.105', 50)
    # Container(vsf.interior, '192.168.1.106', 50)

    root.mainloop()

    # do while root window quit()
    try:
        print("Try to close the socket server.")
        vsf.interior.save_data_right_now_flag = True
    except:
        print("Sorry! Close the socket server failed.")

    print("Wait 10s.\nThere is still some unfinished business to settle. ")
    time.sleep(10)
    print("EXIT")
