import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

class PlaylistDetailWindow:
    def __init__(self, api, playlist_id):
        self.window = tk.Toplevel()
        self.window.title("歌单详情")
        self.window.geometry("800x600")
        self.api = api
        self.playlist_id = playlist_id
        self.setup_ui()
        self.load_playlist_detail()

    def setup_ui(self):
        # 顶部信息区域
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(fill=tk.X, pady=10, padx=10)

        # 左侧封面区域
        self.left_frame = tk.Frame(self.top_frame)
        self.left_frame.pack(side=tk.LEFT, padx=10)

        # 歌单封面
        self.cover_label = tk.Label(self.left_frame)
        self.cover_label.pack(pady=5)

        # 右侧信息区域
        self.info_frame = tk.Frame(self.top_frame)
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # 在标题旁添加播放按钮
        title_frame = tk.Frame(self.info_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        self.title_label = tk.Label(
            title_frame,
            font=("微软雅黑", 16, "bold"),
            wraplength=400,
            justify=tk.LEFT
        )
        self.title_label.pack(side=tk.LEFT)

        self.play_btn = tk.Button(
            title_frame,
            text="立即播放",
            command=self.play_playlist,
            font=("微软雅黑", 10)
        )
        self.play_btn.pack(side=tk.LEFT, padx=10)

        # 简介区域
        tk.Label(
            self.info_frame,
            text="简介：",
            font=("微软雅黑", 10, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        # 简介文本框
        self.description_text = tk.Text(
            self.info_frame,
            height=4,
            wrap=tk.WORD,
            font=("微软雅黑", 9),
            relief=tk.FLAT,
            background=self.window.cget("background")
        )
        self.description_text.pack(fill=tk.X, pady=(0, 10))

        # 创建者区域
        tk.Label(
            self.info_frame,
            text="创建者：",
            font=("微软雅黑", 10, "bold")
        ).pack(anchor="w", pady=(10, 5))

        # 创建者信息框架
        self.creator_frame = tk.Frame(self.info_frame)
        self.creator_frame.pack(fill=tk.X, pady=(0, 10), anchor="w")

        # 创建者头像
        self.creator_avatar = tk.Label(self.creator_frame)
        self.creator_avatar.pack(side=tk.LEFT, padx=5)

        # 创建者名称
        self.creator_name = tk.Label(
            self.creator_frame,
            font=("微软雅黑", 10),
            fg="gray"
        )
        self.creator_name.pack(side=tk.LEFT, padx=5)

        # 歌曲列表区域
        self.tracks_frame = tk.Frame(self.window)  # 先创建 tracks_frame
        self.tracks_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # 创建表格
        columns = ("序号", "歌曲", "歌手", "专辑", "时长")
        self.tree = ttk.Treeview(self.tracks_frame, columns=columns, show="headings")
        
        # 设置Treeview字体
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        style.configure("Treeview", font=("微软雅黑", 9), rowheight=25)

        # 设置列标题和宽度
        column_widths = {
            "序号": 50,
            "歌曲": 200,
            "歌手": 150,
            "专辑": 200,
            "时长": 80
        }
        
        for col, width in column_widths.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.tracks_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定双击事件
        self.tree.bind("<Double-1>", self.play_song)

    def load_playlist_detail(self):
        detail = self.api.get_playlist_detail(self.playlist_id)
        if detail.get("code") == 200:
            playlist = detail["playlist"]
            
            try:
                # 更新标题
                self.window.title(playlist["name"])
                self.title_label.config(text=playlist["name"])

                # 更新描述
                self.description_text.delete("1.0", tk.END)
                description = playlist.get("description") or "暂无简介"
                self.description_text.insert("1.0", description)
                self.description_text.config(state="disabled")

                # 加载歌单封面
                if playlist.get("coverImgUrl"):
                    response = requests.get(playlist["coverImgUrl"])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.cover_label.config(image=photo)
                    self.cover_label.image = photo

                # 加载创建者头像和信息
                creator = playlist.get("creator", {})
                if creator.get("avatarUrl"):
                    avatar_response = requests.get(creator["avatarUrl"])
                    avatar_img = Image.open(BytesIO(avatar_response.content))
                    avatar_img = avatar_img.resize((30, 30))  # 保持头像大小一致
                    avatar_photo = ImageTk.PhotoImage(avatar_img)
                    self.creator_avatar.config(image=avatar_photo)
                    self.creator_avatar.image = avatar_photo

                # 设置创建者名称
                creator_name = creator.get("nickname", "未知创建者")
                self.creator_name.config(text=creator_name)

            except Exception as e:
                print(f"加载歌单详情失败: {e}")

            # 加载歌曲列表
            self.load_tracks()

    def load_tracks(self):
        """单独处理歌曲列表加载"""
        try:
            tracks = self.api.get_playlist_tracks(self.playlist_id)
            if tracks.get("code") == 200:
                # 清空现有列表
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # 添加新的歌曲
                for i, song in enumerate(tracks["songs"], 1):
                    artists = "/".join(ar["name"] for ar in song["ar"])
                    duration = f"{song['dt']//60000}:{(song['dt']//1000)%60:02d}"
                    
                    self.tree.insert("", "end", values=(
                        i,
                        song["name"],
                        artists,
                        song["al"]["name"],
                        duration
                    ), tags=(str(song["id"]),))
        except Exception as e:
            print(f"加载歌曲列表失败: {e}")

    def play_song(self, event):
        """双击播放歌曲"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        song_id = self.tree.item(item, "tags")[0]
        # 获取当前歌单所有歌曲
        all_songs = self.get_all_songs()
        # 打开播放器并设置播放列表
        from player_window import PlayerWindow
        player = PlayerWindow.get_instance(self.api)
        player.set_playlist(all_songs, current_id=song_id)
        player.show()

    def play_playlist(self):
        """播放整个歌单"""
        songs = self.get_all_songs()
        if songs:
            from player_window import PlayerWindow
            player = PlayerWindow.get_instance(self.api)
            player.set_playlist(songs)
            player.show()

    def get_all_songs(self):
        """获取歌单所有歌曲信息"""
        songs = []
        for item in self.tree.get_children():
            song_id = self.tree.item(item, "tags")[0]
            values = self.tree.item(item, "values")
            songs.append({
                "id": song_id,
                "name": values[1],
                "artist": values[2],
                "album": values[3],
                "duration": values[4]
            })
        return songs

    def refresh_playlist(self):
        """刷新歌单"""
        self.load_playlist_detail()

    def on_closing(self):
        """窗口关闭时的处理"""
        self.window.destroy()

    def run(self):
        """运行窗口"""
        # 绑定窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 设置窗口最小尺寸
        self.window.minsize(600, 400)
        # 运行窗口
        self.window.mainloop()
