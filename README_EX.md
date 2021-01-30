# Video_Audio_Record

可以录屏和声音的软件

## 存在问题

### 只能录全屏

### 录屏FPS太慢，每秒5帧

### 只能耳机的声音，无法录系统播出的声音

### 没有快捷键

录制时为防止将程序界面也录进去，采用隐藏界面的做法。需要全局快捷键将程序停止或者呼叫回来。

## 改进

### spy++

用spy++取得需要录屏的程序的句柄，获取窗口坐标和范围，置顶窗口，录屏。

### 更换截屏包

用mss,比PIL快10倍

```bash
pip install mss
```

```python
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
```

### 帧控制

fps数量不对的话，视频和声音不会同步，严重的话20秒的片子会提前结束。
每帧控制会有误差，积累起来有时一分钟能差10秒。
所以需要对fps进行全局控制。

```py
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

                now_fps = self.total_frame  /(end_time-self.start_time)
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
            self.total_frame +=1
```

### 升级pyaudio

支持WASPAI, 支持回放，而且是数字式的，不失真。

当然，也可以用转录线将声卡和耳机连起来。
可以进一步多线程同时录制系统声音和耳机声音，做一个图形界面进行选择。

```python
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
```

#### 录的声量很小，可以后期软件处理，或者直接规一化。

#### pyaudio的编译

pyaudio 编译有一点问题，编译后安装时会出现LNK2001错误。/MT而不是/MD模式编译就好了。

### 增加全局钩子

pyhy不能多线程，已经不再维护。keyboard是官方的全局钩子。

```bash
pip install keyboard mouse
```

```python
        keyboard.add_hotkey('ctrl+shift+f5', self.start_pause)
        keyboard.add_hotkey('ctrl+shift+f6', self.stop)
        keyboard.add_hotkey('ctrl+shift+q', self.exit)
```
