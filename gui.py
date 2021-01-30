'''
github:timyy

2021.01.30
'''
import datetime
import os
import sys
import threading
import time
import signal
import keyboard

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QCursor
from video_audio_cap import (FFmpegThread, SoundRecThread, VideoCapThread,
                             AudioWasapiRecThread)
import win32api, win32con, win32gui
from colorAndProcess import Colored

SCREEN_WEIGHT = 1920 * 2
SCREEN_HEIGHT = 1080
WINDOW_WEIGHT = 480
WINDOW_HEIGHT = 240
RESULT_PATH = './res'  # 存储录屏和录音的位置
SOUND_DEV_ID = 5  # 监听回放的设备ID
color = Colored()


def create_dirs():
    if not os.path.exists(RESULT_PATH):
        os.mkdir(RESULT_PATH)
    video_path = os.path.join(RESULT_PATH, 'video')
    sound_path = os.path.join(RESULT_PATH, 'sound')
    if not os.path.exists(video_path):
        os.mkdir(video_path)
    if not os.path.exists(sound_path):
        os.mkdir(sound_path)
    return video_path, sound_path


def find_window_movetop(hwnd):
    #    hwnd = win32gui.FindWindow(None, name)
    #    hwnd = 0x000B0C72
    if hwnd == 0:
        return None
    else:
        win32gui.ShowWindow(hwnd, 5)
        win32gui.SetForegroundWindow(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        time.sleep(0.2)
        return rect


def find_window_by_cursor():
    time.sleep(3)
    point = win32api.GetCursorPos()
    hwnd = win32gui.WindowFromPoint(point)
    print(point)
    print("%x" % hwnd)
    return hwnd


class qt_window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.start_pressed = False
        self.cap_win_hwnd = 0
        self.file_path = None
        self.dragPosition = QtCore.QPoint(0, 0)
        self.video_path, self.sound_path = create_dirs()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint
                            | QtCore.Qt.Tool
                            | QtCore.Qt.WindowStaysOnTopHint)  # 去掉标题栏
        # 控件布局
        self.button_start_pause = QtWidgets.QPushButton(u"开始")
        self.button_stop = QtWidgets.QPushButton(u"结束")
        self.button_find_window = QtWidgets.QPushButton(u"指定录屏窗口(全屏)")
        self.button_exit = QtWidgets.QPushButton(u"退出")
        self.label_help = QtWidgets.QLabel()
        self.label_help.setText(
            "<p style='background:grey'>"
            "<body bgcolor='black'>"
            "<font style = 'font-size:25px; color:#00FF00;'> ctrl+shift+f5  start </font>"
            "<br/>"
            "<font style = 'font-size:20px; color:#FF0000; font-weight:bold'> ctrl+shift+f6 Stop </font>"
            "<br/>"
            "<font style = 'font-size:20px; color:#ffff00; font-weight:bold'> ctrl+shift+Q Exit </font>"
            "</p>")
        self.label_help.setStyleSheet(
            "border:2px solid blue; border-radius:10px")

        main_layout = QtWidgets.QVBoxLayout()  # 全局布局（1个）：竖直

        hlayout = QtWidgets.QHBoxLayout()  # 局部布局（2个）：水平、竖直、网格、表单
        #vlayout = QtWidgets.QVBoxLayout()

        hlayout.addWidget(self.button_start_pause)  # 局部布局添加部件（例如：按钮）
        hlayout.addWidget(self.button_stop)
        hlayout.addWidget(self.button_find_window)
        hlayout.addWidget(self.button_exit)
        hwg = QtWidgets.QWidget()  # 准备2个部件
        #vwg = QtWidgets.QWidget()

        hwg.setLayout(hlayout)  # 2个部件设置局部布局
        #vwg.setLayout(vlayout)

        main_layout.addWidget(hwg)  # 2个部件加至全局布局
        main_layout.addWidget(self.label_help)
        #main_layout.addWidget(vwg)

        self.setLayout(main_layout)  # 窗体本尊设置全局布局

        self.timeout = 120
        keyboard.add_hotkey('ctrl+shift+f5', self.start_pause)
        keyboard.add_hotkey('ctrl+shift+f6', self.stop)
        keyboard.add_hotkey('ctrl+shift+q', self.exit)

        # 界面美化
        style = """
            QPushButton {
                color: rgb(137, 221, 255);
                background-color: rgb(37, 121, 255);
                border-style:none;
                border:1px solid #3f3f3f;
                padding:5px;
                min-height:20px;
                border-radius:15px;
            }
        """
        self.setStyleSheet(style)
        palette1 = QtGui.QPalette()
        palette1.setColor(self.backgroundRole(),
                          QtGui.QColor("#F8F8FF"))  # 设置背景颜色
        self.setPalette(palette1)
        self.setFixedSize(WINDOW_WEIGHT, WINDOW_HEIGHT)

        # 绑定信号和槽
        self.button_start_pause.clicked.connect(self.start_pause)
        self.button_stop.clicked.connect(self.stop)
        self.button_find_window.clicked.connect(self.find_window)
        self.button_exit.clicked.connect(self.exit)

    def find_window(self):
        self.cap_win_hwnd = find_window_by_cursor()
        if self.cap_win_hwnd == 0:
            self.button_find_window.setText(u"指定录屏窗口(全屏)")
        else:
            self.button_find_window.setText(u"录屏：%x" % self.cap_win_hwnd)

    def start_pause(self):
        self.start_pressed = not self.start_pressed
        self.rect = find_window_movetop(self.cap_win_hwnd)
        if self.start_pressed:
            self.hide()
            self.button_start_pause.setText('暂停')
            now = str(datetime.datetime.now()).split('.')[0]
            now = now.replace(' ', '_').replace(':', '.')
            self.file_path = {
                'video': os.path.join(self.video_path, now + '.avi'),
                'sound': os.path.join(self.sound_path, now + '.wav'),
                'output': os.path.join(RESULT_PATH, now + '.mp4')
            }
            self.video_recorder = VideoCapThread(self.file_path['video'],
                                                 self.rect)
            #self.sound_recorder = SoundRecThread(self.file_path['sound'])
            self.sound_recorder = AudioWasapiRecThread(self.file_path['sound'],
                                                       dev_idx=SOUND_DEV_ID)
            self.video_recorder.start()
            self.sound_recorder.start()
        else:
            self.show()
            self.video_recorder.stoprecord()
            self.sound_recorder.stoprecord()
            self.button_start_pause.setText('开始')

    def stop(self):
        self.show()
        self.setGeometry(self.geometry())
        # http://www.voidcn.com/article/p-ajwrmndj-bvh.html

        self.button_start_pause.setText('开始')
        self.start_pressed = False
        if self.file_path and os.path.exists(self.file_path['video']):
            self.video_recorder.stoprecord()
            self.sound_recorder.stoprecord()
            # 写入文件会有一定时间的延时，所以要等一下，确认进程已经完成。
            time.sleep(2)
            while True:
                if self.sound_recorder.status() == 0:
                    # 还是初始状态，说明没有数据读入
                    break
                if not self.sound_recorder.is_alive():
                    break
                time.sleep(0.1)
            ffmpeg_th = FFmpegThread(self.video_path, self.sound_path,
                                     self.file_path['output'])
            ffmpeg_th.start()
            ffmpeg_th.join()
            print(color.red("Stoped."))

    def exit(self):
        self.stop()  # 开始转换
        # self.showMinimized()
        self.hide()
        print(80 * '-')
        start_time = time.time()
        while True:
            end_time = time.time()
            if end_time - start_time > self.timeout:
                # 超时则强退
                print(color.red("\n强退"))
                os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(1)
            nums = threading.activeCount()
            print(color.red("Exiting ... thread remain "),
                  nums,
                  " spend time: %d" % (int(end_time - start_time)),
                  " s",
                  end='\r')
            if nums == 3:
                print()
                # 强退
                os.kill(os.getpid(), signal.SIGTERM)

    def enterEvent(self, event):
        print('enter')
        self.hide_or_show('show', event)

    def leaveEvent(self, event):
        print('leave')
        self.hide_or_show('hide', event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry(
            ).topLeft()
            QtWidgets.QApplication.postEvent(self, QEvent(174))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.hide_or_show('hide', event)

    def hide_or_show(self, mode, event):
        pos = self.frameGeometry().topLeft()
        print(pos)
        if mode == 'show':
            if pos.x() + WINDOW_WEIGHT >= SCREEN_WEIGHT:  # 右侧隐藏
                self.move(
                    QtCore.QPoint(SCREEN_WEIGHT - WINDOW_WEIGHT + 2, pos.y()))
                event.accept()
            elif pos.x() <= 2:  # 左侧隐藏
                self.move(QtCore.QPoint(0, pos.y()))
                event.accept()
        elif mode == 'hide':
            if pos.x() + WINDOW_WEIGHT >= SCREEN_WEIGHT:  # 右侧隐藏
                self.move(QtCore.QPoint(SCREEN_WEIGHT - 2, pos.y()))
                event.accept()
            elif pos.x() <= 2:  # 左侧隐藏
                self.move(QtCore.QPoint(2 - WINDOW_WEIGHT, pos.y()))
                event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.exit()
        elif event.key() == Qt.Key_F5:
            self.start_pause()
        elif event.key() == Qt.Key_F6:
            self.stop()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = qt_window()
    ex.show()
    sys.exit(app.exec_())
