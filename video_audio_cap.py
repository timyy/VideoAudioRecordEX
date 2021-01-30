# 录音录屏，合成
from colorAndProcess import Colored
import queue
import sys
import threading
import wave
import subprocess
import os
import time
from cv2 import cv2
import numpy as np
import sounddevice as sd
import soundfile as sf
from PIL import ImageGrab
import pyaudio
from pyaudio import PyAudio, paInt16
from scipy.io import wavfile
import mss
'''*******************************屏幕录制*******************************'''

color = Colored()


class VideoCapThread(threading.Thread):
    def __init__(self, videofile='record.avi', rect=None):
        threading.Thread.__init__(self)
        self.bRecord = True
        self.rect = rect
        self.fps = 15
        self.start_time = 0
        self.total_frame = 0

        # imagegrab 的性能不行，在130毫秒左右。
        # 改为mms，见文档https://www.soinside.com/question/KJujKBC3aBsMdmoMsnNsuU
        #大约提高一倍。

        im = self.grab_image(self.rect)
        print(rect, im.size)
        # *'XVID 是MPEG4， 也可以写成  'x','v','i','d'
        self.video = cv2.VideoWriter(videofile,
                                     cv2.VideoWriter_fourcc(*'XVID'), self.fps,
                                     im.size)  # 帧率为32，可以调节

    def grab_image(self, rect=None):
        if self.rect == None:
            # 全屏
            #im = ImageGrab.grab()
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                im = sct.grab(monitor)
        else:
            # 指定区域
            #            im = ImageGrab.grab(self.rect)
            mon = {
                "top": rect[1],
                "left": rect[0],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }
            with mss.mss() as sct:
                im = sct.grab(mon)
        return im

    def run(self):
        start_time = time.time()
        self.start_time = time.time()
        count = 0
        while self.bRecord:
            # 需要加入帧的控制，本人机器太慢，不是机器的问题，是库的问题。
            end_time = time.time()
            if self.total_frame < self.fps:
                # 小于一秒，不做全局控制。
                if end_time - start_time < (1.0 / self.fps):
                    time.sleep(0.001)
                    continue
                else:
                    start_time = end_time
            else:
                # 用总帧数和总时长进行FPS计算，可以保证声音和画面整体是对齐。
                # 但fps不能过大，过大了就没办法了，
                # 当然可以动态调整fps到合适的数值。
                # 也可以一直全速录，帧都存入内存，结束时计算帧率，生成文件。
                # 这样还省了存和编码的时间，速度更快。坏处是内存空间有限，录的时间有限
                # 64位4G内存，应该能录个个把小时，没有大问题
                # 可以做成用pp，多进程多CPU，性能会好一些。
                # 这个程序即录音又录像，单CPU还是有点慢
                now_fps = self.total_frame / (end_time - self.start_time)
                if now_fps > self.fps:
                    time.sleep(0.001)
                    continue
                else:
                    count += 1
                    if count > self.fps:
                        print(color.red('Recoding... '),
                              "fps:%.2f" % now_fps,
                              end='')
                        print(color.yellow("\tduration: %d s" %
                                           (int(end_time - self.start_time))),
                              end='\r')
                        count = 0
                    start_time = end_time
            self.total_frame += 1
            im = self.grab_image(self.rect)
            im = cv2.cvtColor(np.array(im), cv2.COLOR_BGRA2BGR)
            self.video.write(im)

        self.video.release()
        cv2.destroyAllWindows()

    def stoprecord(self):
        self.bRecord = False


'''*******************************麦克风输入-音频录制*******************************'''


class AudioRecThread(threading.Thread):
    def __init__(self, audiofile='record.wav'):
        threading.Thread.__init__(self)
        self.bRecord = True
        self.audiofile = audiofile
        self.chunk = 1024
        self.format = paInt16
        self.channels = 1
        self.rate = 16000

    def run(self):
        audio = PyAudio()
        wavfile = wave.open(self.audiofile, 'ab')
        wavfile.setnchannels(self.channels)
        wavfile.setsampwidth(audio.get_sample_size(self.format))
        wavfile.setframerate(self.rate)
        wavstream = audio.open(format=self.format,
                               channels=self.channels,
                               rate=self.rate,
                               input=True,
                               frames_per_buffer=self.chunk)
        while self.bRecord:
            wavfile.writeframes(wavstream.read(self.chunk))
        wavstream.stop_stream()
        wavstream.close()
        audio.terminate()

    def stoprecord(self):
        self.bRecord = False


'''*******************************系统输出音频录制*******************************'''


class SoundRecThread(threading.Thread):
    def __init__(self, audiofile='record.wav'):
        threading.Thread.__init__(self)
        self.bRecord = True
        self.filename = audiofile
        self.samplerate = 44100
        self.channels = 2

    def run(self):
        q = queue.Queue()

        def callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        #sd.default.device[0] = 2
        with sf.SoundFile(self.filename,
                          mode='x',
                          samplerate=self.samplerate,
                          channels=self.channels) as file:
            with sd.InputStream(samplerate=self.samplerate,
                                channels=self.channels,
                                callback=callback):
                while self.bRecord:
                    file.write(q.get())

    def stoprecord(self):
        self.bRecord = False


'''*****************************系统输出音频录制 wasapi***************************'''


class AudioWasapiRecThread(threading.Thread):
    def __init__(self, audiofile='record.wav', dev_idx=0):
        threading.Thread.__init__(self)
        self.bRecord = True
        self.audiofile = audiofile
        self.chunk = 1024
        self.format = paInt16
        self.channels = 1
        self.rate = 16000
        self.dev_idx = dev_idx
        self._frames = []
        self._status = 0

    def run(self):
        audio = PyAudio()
        print("Sound device:", self.dev_idx)
        device_info = audio.get_device_info_by_index(self.dev_idx)
        self.channels = device_info["maxInputChannels"] if (
            device_info["maxOutputChannels"] < device_info["maxInputChannels"]
        ) else device_info["maxOutputChannels"]
        self.rate = int(device_info["defaultSampleRate"])
        print(color.yellow(str(device_info)))
        wavstream = audio.open(format=self.format,
                               channels=self.channels,
                               rate=self.rate,
                               input=True,
                               frames_per_buffer=self.chunk,
                               input_device_index=device_info["index"],
                               as_loopback=True)

        # wavstream = audio.open(format=self.format,
        #                        channels=self.channels,
        #                        rate=self.rate,
        #                        input=True,
        #                        frames_per_buffer=self.chunk)
        # 如果没有外放的话，loopback会没有数据，造成阻塞
        # 循环读取输入流
        while self.bRecord:
            data = wavstream.read(self.chunk)
            self._frames.append(data)

        self._status = 1
        wavstream.stop_stream()
        wavstream.close()
        # 保存到文件
        print("Saveing .... ", self.audiofile)
        with wave.open(self.audiofile, 'wb') as wavfile:
            wavfile.setnchannels(self.channels)
            wavfile.setsampwidth(audio.get_sample_size(self.format))
            wavfile.setframerate(self.rate)
            wavfile.writeframes(b''.join(self._frames))
        audio.terminate()
        self._status = 2

    # 停止录音
    def stoprecord(self):
        self.bRecord = False

    def status(self):
        return self._status


'''*******************************FFmpeg音视频合成*******************************'''


class FFmpegThread(threading.Thread):
    def __init__(self, avi_file, wav_file, mp4_file):
        threading.Thread.__init__(self)
        self.avi_file = avi_file
        self.wav_file = wav_file
        self.mp4_file = mp4_file
        self.mode = 'dir' if os.path.isdir(self.avi_file) else 'file'

    def combine_to_mp4(self, avi_file, wav_file, mp4_file):
        subprocess.call('ffmpeg -i {} -i {} -strict -2 -f mp4 {}'.format(
            avi_file, wav_file, mp4_file))
        os.remove(avi_file)
        os.remove(wav_file)

    def run(self):
        print('FFmpeg Start ……')
        if self.mode == 'file':
            self.combine_to_mp4(self.avi_file, self.wav_file, self.mp4_file)
        elif self.mode == 'dir':
            avi_files = os.listdir(self.avi_file)
            wav_files = os.listdir(self.wav_file)
            mp4_files = []
            file_num = len(avi_files)
            for i in range(file_num):
                avi_file = os.path.join(self.avi_file, avi_files[i])
                wav_file = os.path.join(self.wav_file, wav_files[i])
                if file_num == 1:
                    self.combine_to_mp4(avi_file, wav_file, self.mp4_file)
                    return
                mp4_file = self.mp4_file + '_{}.mp4'.format(i)
                mp4_files.append(mp4_file)
                self.combine_to_mp4(avi_file, wav_file, mp4_file)
            self.ts_to_mp4(mp4_files)

    def ts_to_mp4(self, files):
        ts_files = []
        for file in files:
            ts_file = file[:-3] + 'ts'
            ts_files.append(ts_file)
            command = 'ffmpeg -i {} -c copy -vbsf h264_mp4toannexb {}'
            command = command.format(file, ts_file)
            subprocess.call(command)
        input_files = '|'.join(ts_files)
        command = 'ffmpeg.exe -i "concat:{}" -c copy -absf aac_adtstoasc {}'
        command = command.format(input_files, self.mp4_file)
        subprocess.call(command)
        for item in files:
            os.remove(item)
        for item in ts_files:
            os.remove(item)

        print('FFmpeg Finish ……')
