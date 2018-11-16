# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.23 01:16
# @Author  : flytocc
# @File    : AppUI.py
# @Software: PyCharm

import time

from tkinter import *

from FooterBar import FooterBar
from VerticalScrolledFrame import VerticalScrolledFrame


class AppUI(Tk):
    def __init__(self, width=1015, height=500, *args, **kwargs):
        super(AppUI, self).__init__(*args, **kwargs)

        screenwidth = self.winfo_screenwidth()  # 屏幕宽度
        screenheight = self.winfo_screenheight()  # 屏幕高度
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2,
                                (screenheight - height) / 2)  # window_H window_W 为窗口的 高度 宽度
        self.geometry(size)
        self.title("智能仪表数据监视系统")  # 设置标题
        self.resizable(1, 1)  # 宽度 高度是否可变 0 不可变
        self.iconbitmap('./ico/setting.ico')  # 设置图标

        self.vsf = VerticalScrolledFrame(self)

        fb = FooterBar(self, self.vsf)
        fb.click_add_dev(init=True)

        pass # 自动加载已扫描到的设备


if __name__ == "__main__":

    app = AppUI(width=1015)

    app.mainloop()

    # do while root window quit()
    try:
        print("Try to close the socket server.")
        app.vsf.interior.save_data_right_now_flag = True
    except:
        print("Sorry! Close the socket server failed.")

    print("Wait 5s.\nThere is still some unfinished business to settle. ")
    time.sleep(5)
    print("EXIT")
    sys.exit()
