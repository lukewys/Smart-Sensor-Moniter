# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.21 22:21
# @Author  : flytocc
# @File    : FooterBar.py
# @Software: PyCharm

import threading

import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox

from ScanningDev import ScanningDev
from Container import Container

THREAD_NUM = 32  # the number of thread for scanning dev


class FooterBar(Frame):
    def __init__(self, master, vsframe, **kw):
        super(FooterBar, self).__init__(master, **kw)
        self.place(relx=0, rely=1, anchor='sw', relwidth=1)

        self.dev_list = []  # save the ip of device can be scanned
        self.old_dev_list = []
        self.vsframe = vsframe

        # display the number of device
        self.text = tk.StringVar()
        self.text.set(" 已连接设备数量: 0")
        label = tk.Label(self, textvariable=self.text)
        label.pack(side='left')

        # refresh the device list
        self.refreshing = False

        def click_refresh_dev_list():
            if self.refreshing == False:
                self.refreshing = True
                print('Scanning Device')
                self.dev_list.clear()  # clear list, to move the offline device

                for thread_id in range(THREAD_NUM):
                    ScanningDev(dev_list=self.dev_list,
                                lock=threading.Lock(),
                                thread_id=thread_id,
                                thread_num=THREAD_NUM
                                ).start()
                self.after(ms=2000, func=self.refresh_dev_chosen_value)

            else:
                messagebox.showinfo(title="提示", message="设备列表刷新中")

        click_refresh_dev_list()
        self.buttonRe = Button(self, text="刷新设备列表", command=click_refresh_dev_list)
        self.buttonRe.pack(side='right')

        # button to add the device selected in the Combobox

        self.button = Button(self, text="添加面板", command=self.click_add_dev)
        self.button.pack(side='right')

        # create a Combobox to display the device's ip scanned before
        self.dev_chosen = Combobox(self, width=20, textvariable=tk.StringVar(), state='readonly')
        self.dev_chosen.pack(side='right')

        self.refresh_footer_online_dev_num()

    def click_add_dev(self, init=False):
        if not init:
            chosen = self.dev_chosen.get()
            if chosen in self.vsframe.interior.dev_online:
                messagebox.showinfo(title="提示", message='该设备的面板已存在！')
            elif chosen == "请选择要添加的设备":
                messagebox.showinfo(title="提示", message="请选择要添加的设备")
            else:
                Container(self.vsframe.interior, chosen, 50).time_chosen.current(0)
                messagebox.showinfo(title="提示", message="成功添加设备: %s" % chosen)
        else:  # when init
            for i in range(len(self.dev_list)):
                Container(self.vsframe.interior, self.dev_list[i], 50).time_chosen.current(0)

    def refresh_footer_online_dev_num(self):
        # 刷新设备数量label
        self.text.set('已连接设备数量: %d' % len(self.vsframe.interior.dev_online))
        self.after(1000, self.refresh_footer_online_dev_num)

    def refresh_dev_chosen_value(self):
        dev_list = self.dev_list
        newadddev_message = ""
        old_dev_set = set(self.old_dev_list)
        for i in range(len(dev_list)):
            if dev_list[i] not in old_dev_set:
                newadddev_message += "\n添加 " + dev_list[i]
        self.old_dev_list = dev_list
        dev_list.insert(0, "请选择要添加的设备")
        self.dev_chosen['values'] = dev_list  # 设置下拉列表的值
        self.dev_chosen.current(0)  # Combobox display "请选择要添加的设备"
        self.refreshing = False
        print("Scanning Finished")
        messagebox.showinfo(title="提示", message="设备列表刷新完成%s" % newadddev_message)


if __name__ == "__main__":
    root = tk.Tk()
    screenwidth = root.winfo_screenwidth()  # 屏幕宽度
    screenheight = root.winfo_screenheight()  # 屏幕高度
    size = '%dx%d+%d+%d' % (800, 100, (screenwidth - 800) / 2,
                            (screenheight - 100) / 2)  # window_H window_W 为窗口的 高度 宽度
    root.geometry(size)
    root.title("智能仪表数据监视系统")  # 设置标题
    # root.resizable(1, 0)  # 宽度 高度是否可变 0 不可变
    root.iconbitmap('../ico/setting.ico')  # 设置图标

    # frame = Frame(root)
    # frame.pack(fill='both', expand='true', side='top')

    footer = FooterBar(root, vsframe=None)

    root.mainloop()
