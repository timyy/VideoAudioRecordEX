# VideoAudioRecordEX
可以录屏和声音的软件

## 由

由[pyHook](https://github.com/Zweo/Video_Audio_Record)改进。

## 改进说明看[readme_ex.md](https://github.com/timyy/VideoAudioRecordEX/README_EX.md)

## 热键

开始录制后，会自动隐藏，停止需要用热键
ctrl+shift+f5 开始
ctrl+shift+f6 结束
ctrl+shift+q  退出 

目前这个版本是录系统声音的，录麦克风需要修改程序。以后会做成选择的。
需要指定具有WASPAI功能的播放设备ID，

```py
SOUND_DEV_ID = 5  # 监听回放的设备ID
```

## 参考

[pyHook](https://github.com/Zweo/Video_Audio_Record)
[keyboard]
[python开发的录音机](https://blog.csdn.net/littlezhuhui/article/details/101025305)
(https://zhuanlan.zhihu.com/p/38136322) 多进程版，目前是多线程的，只用一个CPU，还是慢。可以用多进程，启多个cpu分别录音和录屏，录屏压成文件也采用单独的进程，并采用队列方式，应该能加速。
[mss]
