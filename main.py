# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018.09.25 12:52
# @Author  : flytocc
# @File    : main.py
# @Software: PyCharm

import time

from AppUI import AppUI

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
