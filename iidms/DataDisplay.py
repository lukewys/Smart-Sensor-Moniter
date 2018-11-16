# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.23 11:47
# @Author  : flytocc
# @File    : DataDisplay.py
# @Software: PyCharm

import time

import tkinter as tk
from tkinter.ttk import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.ticker import FormatStrFormatter


class DrawPic(FigureCanvas):
    def __init__(self, master, data_ys_list):
        self.data_ys_list = data_ys_list
        fig = Figure((5, 3))  # 画布宽度
        super(DrawPic, self).__init__(fig, master)
        self.get_tk_widget().pack(fill='both', expand='true', side='top')

        # 双y轴
        ax = fig.add_subplot(111)
        ax2 = ax.twinx()  # 添加第二y轴

        # 暂停功能表示
        self.pause_draw = False
        self.restart_flag = False

        line, = ax.plot([], [], lw=2, color="blue")
        line2, = ax2.plot([], [], lw=2, color="red")
        dot = ax.scatter([], [], c='orange', edgecolors='none', s=50)

        ax.grid()  # 显示网格
        self.xticks_init_flag = False
        self.xticks = 0
        self.ymax = 0
        self.ymin = 0
        self.y2max = 0
        self.y2min = 0

        def pause_draw():
            cnt = 0
            while cnt < 600:
                cnt += 1
                yield cnt

        def init():
            # 各坐标轴数据范围
            ax.set_ylim(10, 30)  # y轴数据范围
            ax2.set_ylim(0, 5)  # y2轴数据范围
            ax.set_xlim(1, 30)  # x轴数据范围

            # 初始数据为空
            line.set_data([], [])
            line2.set_data([], [])

            # 设置两个折现线宽lw及颜色color
            ax.set_ylabel(r"data1", fontsize=8, color="blue")
            ax2.set_ylabel(r"data2", fontsize=8, color="red")

            # 标签精度 一位小数
            ax.yaxis.set_major_formatter(FormatStrFormatter('%1.1f'))
            ax.yaxis.set_minor_formatter(FormatStrFormatter('%1.1f'))

            # 不显示横轴标签
            ax.set_xticks([])

            # 设置两个纵轴其标签刻度的颜色
            for label in ax.get_yticklabels():
                label.set_color("blue")
            for label in ax2.get_yticklabels():
                label.set_color("red")

            return line, line2

        def run(data):
            # update the data
            try:
                draw_flag = False
                y = self.data_ys_list[1][-1]
                y2 = self.data_ys_list[2][-1]
                if self.xticks_init_flag == False:
                    self.xticks = self.data_ys_list[0][-1]
                    self.xticks_init_flag = True
                    draw_flag = True

                xmin, xmax = ax.get_xlim()
                ymin, ymax = ax.get_ylim()
                y2min, y2max = ax2.get_ylim()

                if self.restart_flag == True:
                    self.restart_flag = False
                    if self.ymax > y:
                        y = self.ymax
                    if self.ymin < y:
                        y = self.ymin
                    if self.y2max > y2:
                        y2 = self.y2max
                    if self.y2min < y2:
                        y2 = self.y2min

                if not self.pause_draw:
                    time_init = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.xticks - 2))
                    time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.xticks + data - 3))
                    ax.set_xlabel(time_init + " - " + time_now, fontsize=11, color="purple")

                    if data >= xmax:
                        ax.set_xlim(xmin, 2 * xmax)
                        draw_flag = True

                    if y >= ymax:
                        if 2 * ymax - ymin > y + 5:
                            ax.set_ylim(ymin, 2 * ymax - ymin)
                        else:
                            ax.set_ylim(ymin, y + 5)
                        draw_flag = True

                    if y < ymin:
                        if ymin * 2 - ymax < y:
                            ax.set_ylim(ymin * 2 - ymax, ymax)
                        else:
                            ax.set_ylim(y, ymax)
                        draw_flag = True

                    if y2 >= y2max:
                        if 2 * y2max - y2min > y2 + 5:
                            ax2.set_ylim(y2min, 2 * y2max - y2min)
                        else:
                            ax2.set_ylim(y2min, y2 + 5)
                        draw_flag = True

                    if y2 < y2min:
                        if y2min * 2 - y2max < y2:
                            ax2.set_ylim(y2min * 2 - y2max, y2max)
                        else:
                            ax.set_ylim(y2, ymax)
                        draw_flag = True

                    if draw_flag == True:
                        ax.figure.canvas.draw()

                    line.set_data(self.data_ys_list[4], self.data_ys_list[1])
                    line2.set_data(self.data_ys_list[4], self.data_ys_list[2])
                    # Set x and y data...
                    dot.set_offsets(self.data_ys_list[3])


                else:  # 暂停后的操作
                    self.restart_flag = True

                    if self.ymax < y:
                        self.ymax = y
                    if self.ymin > y:
                        self.ymin = y
                    if self.y2max < y2:
                        self.y2max = y2
                    if self.y2min > y2:
                        self.y2min = y2

            except:
                pass

            return line, line2

        self.ani = animation.FuncAnimation(fig, run, pause_draw, blit=False,
                                           interval=1000,  # 刷新间隔
                                           repeat=False,  # 重复绘制
                                           init_func=init)


class Tree(Treeview):
    def __init__(self, master, tree_col=("timestamp", "temperature", "weight", "error"),
                 tree_col_text=("时间戳", "数据1", "数据2", "错误码")):
        super(Tree, self).__init__(master, show="headings", columns=tree_col)

        master.ybar = Scrollbar(master, orient='vertical', command=self.yview)  # 定义y滚动条
        master.xbar = Scrollbar(master, orient="horizontal", command=self.xview)  # x滚动条
        self.configure(xscrollcommand=master.xbar.set, yscrollcommand=master.ybar.set)  # x,y滚动条关联

        master.ybar.pack(fill='both', expand='false', side='right')
        master.xbar.pack(fill='both', expand='false', side='bottom')
        self.pack(fill='both', expand='true', side='left')

        self.now_flag = True

        assert len(tree_col) == len(tree_col_text), "tree_col and tree_col_text argument must have same length"

        self.column(tree_col[0], anchor="center", minwidth=150, width=150, stretch='false')  # 表示列,不显示
        self.heading(tree_col[0], text=tree_col_text[0])
        for i in range(1, len(tree_col)):
            self.column(tree_col[i], anchor="center", minwidth=100, width=100, stretch='false')  # 表示列,不显示
            self.heading(tree_col[i], text=tree_col_text[i])  # 显示表头

    def update_tree(self, data_dict, option):
        timestamp_int = int(time.time())

        if option == '实时60秒':
            self.now_flag = True
            # 删除旧数据
            items = self.get_children()
            if len(items) >= 20:  # 最多存储180条数据f
                for i in range(20, len(items)):
                    if self.item(items[i], "values")[3] == '0x00':  # 保留错误项
                        self.delete(items[i])

            try:
                self.insert("", 0, values=data_dict[timestamp_int])
            except:
                pass
        elif option == '近三分钟':  # '近三分钟'
            if self.now_flag == True:
                self.now_flag = False
                data_len = len(data_dict)
                if data_len >= 180:
                    data_dict = 180

                for i in range(data_len):
                    try:
                        self.insert("", i, values=data_dict[timestamp_int + i - data_len])
                    except:
                        pass

        elif option == '近十分钟':  # '近十分钟'
            print('近十分钟')
            if self.now_flag == True:
                self.now_flag = False
                data_len = len(data_dict)
                if data_len >= 600:
                    data_dict = 180
                else:
                    data_len = int(data_len / 3.33)
                for i in range(data_len):
                    try:
                        self.insert("", i, values=data_dict[timestamp_int + i * 3 - data_len * 3])
                    except:
                        pass
        # self.tree.after(1000, self.update_tree)  # 每1000ms刷新一次


if __name__ == "__main__":
    from iidms.VerticalScrolledFrame import VerticalScrolledFrame
    from iidms.Container import Container

    root = tk.Tk()
    screenwidth = root.winfo_screenwidth()  # 屏幕宽度
    screenheight = root.winfo_screenheight()  # 屏幕高度
    size = '%dx%d+%d+%d' % (800, 500, (screenwidth - 800) / 2,
                            (screenheight - 500) / 2)  # window_H window_W 为窗口的 高度 宽度
    root.geometry(size)
    root.title("智能仪表数据监视系统")  # 设置标题
    # root.resizable(1, 0)  # 宽度 高度是否可变 0 不可变
    root.iconbitmap('../ico/setting.ico')  # 设置图标

    vsf = VerticalScrolledFrame(root)
    # vsf.pack()
    vsf.place(relwidth=1, relheight=1)
    con = Container(vsf.interior, '192.168.1.105', 1)

    # tree = Tree(con.tree_frame)
    # pic = DrawPic(con.canvas_frame)
    # con.canvas.show()

    root.mainloop()
