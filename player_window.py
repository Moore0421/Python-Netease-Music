import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import re
import os
import uuid
import vlc
import subprocess
import threading
import psutil
import time

class PlayerWindow:
    _instance = None
    
    @classmethod
    def get_instance(cls, api=None):
        """获取播放器实例（单例模式）"""
        if not cls._instance or not cls._instance.window.winfo_exists():
            cls._instance = cls(api)
        return cls._instance

    def __init__(self, api):
        if PlayerWindow._instance and PlayerWindow._instance.window.winfo_exists():
            raise Exception("This class is a singleton!")
            
        self.window = tk.Toplevel()
        self.window.title("正在播放")
        self.window.geometry("1000x600")
        # 保持窗口引用，避免被销毁
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.api = api
        
        # 播放列表管理
        self.playlist = []
        self.current_index = -1
        
        # 播放控制变量
        self.is_playing = False
        self.current_time = 0
        self.total_time = 0
        self.play_mode = "sequence"
        
        # 添加歌词解析变量
        self.lyrics = []  # [(time, text), ...]
        self.current_lyric_index = -1
        
        # 添加音频处理临时目录
        self.temp_dir = self.create_temp_dir()
        self.current_audio = None
        
        # VLC相关
        self._vlc_instance = vlc.Instance()
        self._vlc_player = None
        self._media = None
        self._media_path = None
        self._duration = 0
        self._progress_updating = False
        self._seek_by_user = False
        self.vlc_process = None
        self.current_file = None
        self.monitor_thread = None
        self.progress_update_id = None  # 添加进度更新ID追踪

        self.setup_ui()
        PlayerWindow._instance = self

    def hide_window(self):
        """隐藏窗口而不是销毁"""
        self.window.withdraw()

    def show(self):
        """显示窗口"""
        if not self.window.winfo_exists():
            # 如果窗口已被销毁，重新创建
            PlayerWindow._instance = None
            return PlayerWindow.get_instance(self.api)
        else:
            self.window.deiconify()
            self.window.lift()
            return self

    def set_playlist(self, songs, current_id=None):
        """设置播放列表"""
        if not self.window.winfo_exists():
            # 如果窗口不存在，重新创建
            PlayerWindow._instance = None
            instance = PlayerWindow.get_instance(self.api)
            instance.set_playlist(songs, current_id)
            instance.show()
            return
            
        self.playlist = songs
        self.current_index = -1
        
        if current_id:
            # 从指定歌曲开始播放
            for i, song in enumerate(songs):
                if str(song["id"]) == str(current_id):
                    self.current_index = i
                    break
        
        # 根据播放模式选择开始播放的歌曲
        if self.play_mode == "random" and not current_id:
            import random
            self.current_index = random.randint(0, len(songs) - 1)
        elif not current_id:
            self.current_index = 0

        if self.current_index >= 0:
            self.play_current()

    def setup_ui(self):
        # 主布局分为左右两部分
        self.left_frame = tk.Frame(self.window, width=400)
        self.right_frame = tk.Frame(self.window, width=600)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.left_frame.pack_propagate(False)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=20, pady=20)

        # 左侧布局
        # 专辑图片
        self.cover_frame = tk.Frame(self.left_frame, height=300)
        self.cover_frame.pack(fill=tk.X, pady=(0, 20))
        self.cover_label = tk.Label(self.cover_frame)
        self.cover_label.pack(expand=True)

        # 歌曲信息
        self.info_frame = tk.Frame(self.left_frame)
        self.info_frame.pack(fill=tk.X, pady=10)
        
        self.title_label = tk.Label(
            self.info_frame,
            text="微软雅黑",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack()
        
        self.artist_label = tk.Label(
            self.info_frame,
            text="微软雅黑",
            font=("Arial", 12)
        )
        self.artist_label.pack()
        
        self.album_label = tk.Label(
            self.info_frame,
            text="微软雅黑",
            font=("Arial", 10),
            fg="gray"
        )
        self.album_label.pack()

        # 进度条
        self.progress_frame = tk.Frame(self.left_frame)
        self.progress_frame.pack(fill=tk.X, pady=20)
        
        self.time_label = tk.Label(self.progress_frame, text="00:00")
        self.time_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Scale(
            self.progress_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.on_progress_change
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.duration_label = tk.Label(self.progress_frame, text="00:00")
        self.duration_label.pack(side=tk.LEFT)

        # 播放控制
        self.control_frame = tk.Frame(self.left_frame)
        self.control_frame.pack(fill=tk.X, pady=20)

        # 播放模式按钮
        self.mode_btn = tk.Button(
            self.control_frame,
            text="顺序播放",
            command=self.toggle_play_mode
        )
        self.mode_btn.pack(side=tk.LEFT, padx=5)

        # 上一曲
        self.prev_btn = tk.Button(
            self.control_frame,
            text="上一曲",
            command=self.play_previous
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        # 播放/暂停
        self.play_btn = tk.Button(
            self.control_frame,
            text="播放",
            width=8,
            command=self.toggle_play
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # 下一曲
        self.next_btn = tk.Button(
            self.control_frame,
            text="下一曲",
            command=self.play_next
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # 右侧布局
        # 歌词标题
        tk.Label(
            self.right_frame,
            text="歌词",
            font=("微软雅黑", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # 歌词显示区域
        self.lyric_frame = tk.Frame(self.right_frame)
        self.lyric_frame.pack(fill=tk.BOTH, expand=True)

        self.lyric_text = tk.Text(
            self.lyric_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 14), # 增大歌词字体
            relief=tk.FLAT,
            selectbackground="lightblue",
            spacing1=8,  # 增加行间距
            spacing3=8,
            padx=10,
            pady=10
        )
        self.lyric_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 歌词滚动条
        lyric_scrollbar = ttk.Scrollbar(self.lyric_frame)
        lyric_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置歌词文本和滚动条
        self.lyric_text.config(yscrollcommand=lyric_scrollbar.set)
        lyric_scrollbar.config(command=self.lyric_text.yview)

    def on_progress_change(self, value):
        """进度条改变处理"""
        if self._vlc_player and self.total_time > 0:
            self._seek_by_user = True
            target_time = (float(value) * self.total_time) / 100
            self._vlc_player.set_time(int(target_time * 1000))
            self.current_time = int(target_time)
            self.window.after(200, lambda: setattr(self, "_seek_by_user", False))

    def toggle_play_mode(self):
        """切换播放模式"""
        modes = {
            "sequence": ("随机播放", "random"),
            "random": ("单曲循环", "single"),
            "single": ("顺序播放", "sequence")
        }
        text, mode = modes[self.play_mode]
        self.play_mode = mode
        self.mode_btn.config(text=text)

    def toggle_play(self):
        """播放/暂停切换"""
        if not self.vlc_process:
            return
        
        if self.is_playing:
            # 发送空格键给VLC窗口来触发暂停
            subprocess.run(['nircmd', 'sendkey', 'vlc.exe', 'space'])
            self.play_btn.config(text="播放")
        else:
            subprocess.run(['nircmd', 'sendkey', 'vlc.exe', 'space'])
            self.play_btn.config(text="暂停")
        
        self.is_playing = not self.is_playing

    def pause(self):
        """暂停播放"""
        if self._vlc_player and self.is_playing:
            self._vlc_player.pause()
            self.is_playing = False
            self.play_btn.config(text="播放")

    def resume(self):
        """恢复播放"""
        if self._vlc_player:
            self._vlc_player.play()
            self.is_playing = True
            self.play_btn.config(text="暂停")
            self.update_progress()
            self.update_lyrics_position()

    def play_previous(self):
        """播放上一首"""
        if not self.playlist:
            return
            
        # 先停止当前播放
        self.stop_current_playback()
            
        if self.play_mode == "single":
            self.play_current()
        elif self.play_mode == "random":
            import random
            self.current_index = random.randint(0, len(self.playlist) - 1)
            self.play_current()
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_current()
    
    def play_current(self):
        """播放当前歌曲"""
        if self.current_index >= 0 and self.current_index < len(self.playlist):
            song = self.playlist[self.current_index]
            song_id = song["id"]
            if self.load_song(song_id):
                # 播放成功后更新歌词
                self.update_lyrics_position()
                self.highlight_current_lyric()
                self.update_progress()
                self.check_music_end()
        else:
            print("当前索引无效，无法播放歌曲")

    def play_next(self):
        """播放下一首"""
        if not self.playlist:
            return
            
        # 先停止当前播放
        self.stop_current_playback()
        
        if self.play_mode == "single":
            # 单曲循环
            self.play_current()
        elif self.play_mode == "random":
            # 随机播放
            import random
            self.current_index = random.randint(0, len(self.playlist) - 1)
            self.play_current()
        else:
            # 顺序播放
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_current()

    def update_progress(self):
        """更新进度条"""
        # 取消之前的进度更新定时器（如果存在）
        if hasattr(self, 'progress_update_id') and self.progress_update_id:
            self.window.after_cancel(self.progress_update_id)
            self.progress_update_id = None

        if self.is_playing and not self._seek_by_user:
            # 自增进度
            self.current_time += 0.2  # 每200ms增加0.2秒
            if self.total_time > 0:
                progress = (self.current_time / self.total_time) * 100
                self.progress_bar.set(progress)
                
                # 更新时间标签
                current = f"{int(self.current_time)//60:02d}:{int(self.current_time)%60:02d}"
                total = f"{self.total_time//60:02d}:{self.total_time%60:02d}"
                self.time_label.config(text=current)
                self.duration_label.config(text=total)
                
                # 如果到达结尾，触发结束事件
                if self.current_time >= self.total_time:
                    self.on_song_complete()
                    return
            
            # 每200ms更新一次
            self.progress_update_id = self.window.after(200, self.update_progress)

    def get_current_pos(self):
        """获取当前播放时间（秒）"""
        if self._vlc_player:
            return self._vlc_player.get_time() / 1000
        return 0

    def seek(self, position):
        """跳转播放位置"""
        if not self.vlc_process:
            return
        
        # 更新UI显示
        self.current_time = position
        if self.total_time > 0:
            progress = (position / self.total_time) * 100
            self.progress_bar.set(progress)
        
        # 停止当前播放并重新开始
        self.stop_current_playback()
        
        # 使用新的起始位置重新播放
        if self.current_file:
            self.vlc_process = subprocess.Popen(
                ['vlc', '--intf', 'dummy', '--play-and-exit', 
                 '--start-time', str(position), self.current_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def load_song(self, song_id):
        """加载歌曲"""
        try:
            # 获取歌曲详情
            song_detail = self.api.get_song_detail(song_id)
            if song_detail.get("code") == 200 and song_detail.get("songs"):
                song = song_detail["songs"][0]
                
                # 更新界面信息
                self.update_song_info(song)
                
                # 获取歌曲URL
                url_result = self.api.get_song_url(song_id)
                if url_result.get("code") == 200 and url_result["data"][0]["url"]:
                    url = url_result["data"][0]["url"]
                    self.play_url(url)
                    
                    # 获取歌词
                    self.load_lyrics(song_id)
                    
                    # 保存当前歌曲信息
                    self.current_song = song
                    return True
            return False
        except Exception as e:
            print(f"加载歌曲失败: {e}")
            return False

    def update_song_info(self, song):
        """更新歌曲信息显示"""
        self.title_label.config(text=song["name"])
        artists = "/".join(ar["name"] for ar in song["ar"])
        self.artist_label.config(text=artists)
        self.album_label.config(text=song["al"]["name"])
        
        # 加载专辑封面
        try:
            response = requests.get(song["al"]["picUrl"])
            img = Image.open(BytesIO(response.content))
            img = img.resize((250, 250))
            photo = ImageTk.PhotoImage(img)
            self.cover_label.config(image=photo)
            self.cover_label.image = photo
        except Exception as e:
            print(f"加载封面失败: {e}")

    def create_temp_dir(self):
        """创建临时文件目录"""
        import os
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

    def play_url(self, url):
        """播放指定URL的音乐"""
        try:
            # 先停止当前播放和监控
            self.stop_current_playback()
            if self.monitor_thread and self.monitor_thread.is_alive():
                # 等待旧线程结束
                self.monitor_thread.join(timeout=1.0)
            
            # 显示加载状态
            original_title = self.title_label.cget('text')
            self.title_label.config(text=f"{original_title} (下载中...)")
            
            # 下载音频文件到临时目录
            temp_file = os.path.join(self.temp_dir, f"temp_music_{uuid.uuid4().hex}.mp3")
            response = requests.get(url)
            if response.status_code == 200:
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                
                # 检查文件大小
                if os.path.getsize(temp_file) < 1024:
                    print("音频文件过小，可能无效")
                    self.title_label.config(text=original_title)
                    return

                # 使用系统VLC播放
                self.current_file = temp_file
                self.vlc_process = subprocess.Popen(
                    ['vlc', '--intf', 'dummy', '--play-and-exit', temp_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # 更新状态
                self.is_playing = True
                self.play_btn.config(text="暂停")
                self.title_label.config(text=original_title)
                
                # 启动新的监控线程
                self.monitor_thread = threading.Thread(target=self._monitor_playback)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
                
                # 重置并开始更新进度
                self.current_time = 0
                self.total_time = self.get_audio_duration(temp_file)
                self.update_progress()
                self.update_lyrics_position()
                
        except Exception as e:
            print(f"播放失败: {e}")
            self.stop_current_playback()
            self.title_label.config(text=original_title)

    def _monitor_playback(self):
        """监控VLC进程状态"""
        while self.vlc_process and self.vlc_process.poll() is None:
            time.sleep(0.5)
        
        # 如果进程结束，更新UI
        if self.is_playing:
            self.window.after(0, self.on_song_complete)

    def stop_current_playback(self):
        """停止当前播放并清理资源"""
        # 取消进度更新定时器
        if hasattr(self, 'progress_update_id') and self.progress_update_id:
            self.window.after_cancel(self.progress_update_id)
            self.progress_update_id = None
        
        # 停止VLC进程
        if self.vlc_process:
            try:
                parent = psutil.Process(self.vlc_process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except:
                pass
            self.vlc_process = None
        
        # 重置状态
        self.is_playing = False
        self.play_btn.config(text="播放")
        self.current_time = 0
        self.total_time = 0
        self.progress_bar.set(0)
        self.time_label.config(text="00:00")
        self.duration_label.config(text="00:00")

    def clear_temp_files(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"清理临时文件失败: {e}")

    def on_closing(self):
        """窗口关闭时的处理"""
        self.stop_current_playback()
        self.clear_temp_files()
        self.window.destroy()

    def check_music_end(self):
        """检查音乐是否播放结束"""
        if self._vlc_player and self.is_playing:
            state = self._vlc_player.get_state()
            if state == vlc.State.Ended:
                self.on_song_complete()
            elif state == vlc.State.Error:
                print("VLC播放错误")
            else:
                self.window.after(500, self.check_music_end)

    def on_song_complete(self):
        """当前歌曲播放完成时的处理"""
        if self.play_mode == "single":
            # 单曲循环
            self.play_current()
        else:
            # 播放下一首
            self.play_next()

    def load_lyrics(self, song_id):
        """加载歌词"""
        try:
            self.lyrics = []
            self.current_lyric_index = -1
            self.lyric_text.delete(1.0, tk.END)
            
            lyric_result = self.api.get_song_lyric(song_id)
            if lyric_result.get("code") == 200:
                lrc = lyric_result.get("lrc", {}).get("lyric", "")
                if lrc:
                    # 解析歌词
                    self.lyrics = self.parse_lyrics(lrc)
                    # 显示歌词
                    self.show_lyrics()
                else:
                    self.lyric_text.insert(tk.END, "暂无歌词")
        except Exception as e:
            print(f"加载歌词失败: {e}")
            self.lyric_text.insert(tk.END, "加载歌词失败")

    def parse_lyrics(self, lrc_text):
        """解析歌词文本"""
        lyrics = []
        for line in lrc_text.split('\n'):
            if line.strip():
                # 匹配时间戳 [mm:ss.xx]
                time_stamps = re.findall(r'\[(\d{2}):(\d{2})\.?\d*\]', line)
                text = re.sub(r'\[.*?\]', '', line).strip()
                if time_stamps and text:
                    for minute, second in time_stamps:
                        time_seconds = int(minute) * 60 + int(second)
                        lyrics.append((time_seconds, text))
        return sorted(lyrics)  # 按时间排序

    def show_lyrics(self):
        """显示歌词"""
        self.lyric_text.delete(1.0, tk.END)
        self.lyric_text.tag_configure("current", background="lightblue")
        for _, text in self.lyrics:
            self.lyric_text.insert(tk.END, text + '\n')

    def update_lyrics_position(self):
        """更新歌词位置"""
        if not self.lyrics or not self.is_playing:
            return

        try:
            # 使用自增的current_time来更新歌词
            current_pos = int(self.current_time)  # 取整数部分
            
            # 查找当前应显示的歌词
            for i, (time, _) in enumerate(self.lyrics):
                if time > current_pos:
                    if i != self.current_lyric_index:
                        self.current_lyric_index = i - 1
                        self.highlight_current_lyric()
                    break
            
            # 安排下一次更新
            if self.is_playing:
                self.window.after(200, self.update_lyrics_position)
        except Exception as e:
            print(f"更新歌词位置失败: {e}")

    def highlight_current_lyric(self):
        """高亮显示当前歌词"""
        if not self.lyrics:
            return
            
        # 移除所有高亮
        self.lyric_text.tag_remove("current", "1.0", tk.END)
        
        if 0 <= self.current_lyric_index < len(self.lyrics):
            # 计算行号
            start = f"{self.current_lyric_index + 1}.0"
            end = f"{self.current_lyric_index + 2}.0"
            
            # 添加高亮
            self.lyric_text.tag_add("current", start, end)
            
            # 滚动到可见区域
            self.lyric_text.see(start)

    def get_audio_duration(self, file_path):
        """获取音频文件时长（秒）"""
        try:
            # 临时创建一个VLC实例来获取时长
            instance = vlc.Instance()
            media = instance.media_new(file_path)
            media.parse()
            duration = media.get_duration() // 1000  # 转换为秒
            media.release()
            instance.release()
            return duration
        except:
            # 如果无法获取时长，返回一个默认值（如3分钟）
            return 180