import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
from api import NetEaseAPI
from player_window import PlayerWindow

class MainWindow:
    def __init__(self, cookie=None, user_id=None):
        self.root = tk.Tk()
        self.root.title("网易云音乐")
        self.root.geometry("600x700")
        self.api = NetEaseAPI()
        if cookie and user_id:
            self.api.set_user_info(cookie, user_id)  # 设置完整的用户信息
        self.setup_ui()
        self.load_playlists()
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_closing) # 添加关闭协议

    def setup_ui(self):
        # 顶部按钮栏
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, pady=10)

        tk.Button(self.top_frame, text="本地音乐", command=self.show_local, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)
        tk.Button(self.top_frame, text="我的音乐", command=self.show_my_music, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)
        tk.Button(self.top_frame, text="播放页面", command=self.show_player, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)

        # 内容区域（使用Canvas实现滚动效果）
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 推荐歌单标题
        tk.Label(self.scrollable_frame, text="推荐歌单", font=("微软雅黑", 16, "bold")).pack(pady=10)
        
        # 创建网格布局来显示歌单
        self.playlist_frame = tk.Frame(self.scrollable_frame)
        self.playlist_frame.pack(fill=tk.BOTH, expand=True, padx=20)

    def load_playlists(self):
        playlists = self.api.get_personalized_playlists(limit=12)
        if playlists.get("code") == 200:
            row = 0
            col = 0
            for playlist in playlists["result"]:
                self.create_playlist_card(playlist, row, col)
                col += 1
                if col >= 4:  # 每行显示4个歌单
                    col = 0
                    row += 1

    def create_playlist_card(self, playlist, row, col):
        # 创建歌单卡片框架
        card = tk.Frame(self.playlist_frame, relief=tk.RAISED, borderwidth=1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        try:
            # 获取并显示歌单封面
            response = requests.get(playlist["picUrl"])
            img = Image.open(BytesIO(response.content))
            img = img.resize((120, 120))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(card, image=photo)
            img_label.image = photo
            img_label.pack()

            # 显示歌单名称
            name_label = tk.Label(card, text=playlist["name"], wraplength=120, font=("微软雅黑", 9))
            name_label.pack()

            # 绑定点击事件
            img_label.bind("<Button-1>", lambda e, pid=playlist["id"]: self.open_playlist(pid))
            name_label.bind("<Button-1>", lambda e, pid=playlist["id"]: self.open_playlist(pid))

        except Exception as e:
            print(f"Error loading playlist card: {e}")

    def open_playlist(self, playlist_id):
        """打开歌单详情页面"""
        from playlist_detail import PlaylistDetailWindow
        detail_window = PlaylistDetailWindow(self.api, playlist_id)
        detail_window.run()

    def show_local(self):
        # TODO: 实现显示本地音乐功能
        print("显示本地音乐")

    def show_my_music(self):
        """显示我的音乐页面"""
        from my_music import MyMusicWindow
        my_music = MyMusicWindow(self.api)
        my_music.run()

    def show_player(self):
        # TODO: 实现显示播放页面功能
        player = PlayerWindow.get_instance(self.api) # 获取或创建播放器实例
        player.show() # 显示播放器窗口
        print("显示播放页面")

    def on_app_closing(self):
        """应用程序关闭时的处理"""
        player = PlayerWindow.get_instance()
        if player and player.window.winfo_exists():
            player.on_closing() # 调用播放器窗口的关闭处理
        self.root.destroy()

    def run(self):
        self.root.mainloop()
