# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.21 20:24
# @Author  : flytocc
# @File    : VerticalScrolledFrame.py
# @Software: PyCharm

import tkinter as tk
from tkinter.ttk import *


# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame
class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """

    def __init__(self, master, **kw):
        # Style().configure('Frame.TFrame', background='#3c3f41')
        super(VerticalScrolledFrame, self).__init__(master, **kw)
        self.pack(fill='both', expand='true', side='top')

        # create a canvas object and a vertical scrollbar for scrolling it
        vertical_scrollbar = Scrollbar(self, orient='vertical')
        vertical_scrollbar.pack(fill='y', side='right', expand='false')
        canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vertical_scrollbar.set)
        canvas.pack(side='left', fill='both', expand='true')
        vertical_scrollbar.config(command=canvas.yview)

        # set height as screen's height
        height = self.winfo_screenheight()
        master.config(height=height)
        canvas.config(height=height)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        self.interior.dev_online = set()  # save the ip of device online
        self.interior.save_data_right_now_flag = False
        self.interior.master = master
        interior_id = canvas.create_window(0, 0, window=interior, anchor='nw')

        # mousewheel for scrolling
        def _on_mousewheel(event):
            # print(event)
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        interior.bind_all("<MouseWheel>", _on_mousewheel)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)


if __name__ == "__main__":
    root = tk.Tk()
    screenwidth = root.winfo_screenwidth()  # 屏幕宽度
    screenheight = root.winfo_screenheight()  # 屏幕高度
    size = '%dx%d+%d+%d' % (800, 100, (screenwidth - 800) / 2,
                            (screenheight - 100) / 2)  # window_H window_W 为窗口的 高度 宽度
    root.geometry(size)
    root.title('智能仪表数据监视系统')  # 设置标题
    # root.resizable(0, 0)  # 宽度 高度是否可变 0 不可变
    root.iconbitmap('../ico/setting.ico')  # 设置图标

    vsf = VerticalScrolledFrame(root)

    pw = PanedWindow(vsf.interior, orient="horizontal")
    pw.pack(fill='both', expand='true')

    button = Button(pw, text="添加面板")
    pw.add(button)

    button2 = Button(pw, text="添加面板")
    pw.add(button2)
    # button.pack(side='right')

    root.mainloop()
