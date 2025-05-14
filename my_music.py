import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

class MyMusicWindow:
    def __init__(self, api):
        self.window = tk.Toplevel()
        self.window.title("我的音乐")
        self.window.geometry("1000x600")  # 增加窗口宽度
        self.api = api
        self.setup_ui()
        self.load_playlists()

    def setup_ui(self):
        # 我的音乐标题
        title_label = tk.Label(self.window, text="我的音乐", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=10)                                                 

        # 创建主滚动区域
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(self.main_frame, bg=self.window.cget('bg'))  # 设置背景色
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        
        # 创建放置歌单的框架
        self.playlists_frame = tk.Frame(self.canvas, bg=self.window.cget('bg'))  # 设置背景色
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 打包组件
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # 在Canvas中创建窗口
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.playlists_frame,
            anchor="nw",
            width=self.canvas.winfo_width()  # 设置内容框架宽度
        )

        # 绑定事件
        self.bind_events()

        # 创建两栏的框架
        self.left_column = tk.Frame(self.playlists_frame)
        self.right_column = tk.Frame(self.playlists_frame)
        self.left_column.grid(row=0, column=0, padx=10, sticky="nsew")
        self.right_column.grid(row=0, column=1, padx=10, sticky="nsew")

        # 配置网格列权重
        self.playlists_frame.grid_columnconfigure(0, weight=1)
        self.playlists_frame.grid_columnconfigure(1, weight=1)

    def bind_events(self):
        """绑定所有需要的事件"""
        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.playlists_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 进入离开画布区域时绑定/解绑滚轮事件
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_frame_configure(self, event):
        """当内容框架大小改变时，更新画布滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """当画布大小改变时，调整内容框架宽度"""
        # 更新内容框架的宽度以匹配画布
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        """绑定鼠标滚轮事件"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """解绑鼠标滚轮事件"""
        self.canvas.unbind_all("<MouseWheel>")

    def create_playlist_card(self, playlist, parent, row):
        # 创建卡片框架
        frame = tk.Frame(
            parent,
            relief=tk.RAISED,
            borderwidth=1,
            bg=self.window.cget('bg')
        )
        frame.grid(row=row, column=0, sticky="ew", pady=5, padx=10)  # 增加水平内边距
        parent.grid_columnconfigure(0, weight=1)  # 使卡片填充整个列宽

        try:
            # 左侧信息区域（封面和标题）
            left_frame = tk.Frame(frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)  # 增加内边距
            
            # 获取歌单封面
            try:
                response = requests.get(playlist.get('coverImgUrl', ''))
                image = Image.open(BytesIO(response.content))
            except:
                # 如果无法加载图片，可以创建一个空白图片
                image = Image.new('RGB', (60, 60), color='gray')
            
            # 分类歌单
            image = image.resize((80, 80))  # 增大封面尺寸
            photo = ImageTk.PhotoImage(image)
            
            cover_label = tk.Label(left_frame, image=photo)
            cover_label.image = photo
            cover_label.pack(side=tk.LEFT, padx=10)

            # 右侧信息区域
            info_frame = tk.Frame(left_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)

            # 歌单名称
            name_label = tk.Label(
                info_frame, 
                text=playlist["name"],
                font=("微软雅黑", 12, "bold"),  # 修改字体
                wraplength=250,  # 增加文本宽度
                justify=tk.LEFT
            )
            name_label.pack(anchor="w", pady=2)

            # 创建者信息
            creator = f"by {playlist['creator']['nickname']}" if playlist.get('creator') else ""
            creator_label = tk.Label(
                info_frame,
                text=creator,
                font=("微软雅黑", 10), # 修改字体
                fg="gray"
            )
            creator_label.pack(anchor="w", pady=2)

            # 歌曲数量
            count_label = tk.Label(
                info_frame,
                text=f"{playlist['trackCount']}首歌曲",
                font=("微软雅黑", 10), # 修改字体
                fg="gray"
            )
            count_label.pack(anchor="w")

            # 绑定点击事件
            for widget in [frame, cover_label, name_label, creator_label, count_label]:
                widget.bind("<Button-1>", lambda e, pid=playlist["id"]: self.open_playlist(pid))
                widget.bind("<Enter>", lambda e, w=frame: self.on_hover(w))
                widget.bind("<Leave>", lambda e, w=frame: self.on_leave(w))

        except Exception as e:
            print(f"加载歌单失败: {e}")

    def on_hover(self, widget):
        """鼠标悬停效果"""
        widget.configure(relief=tk.RAISED, bg='#f0f0f0')

    def on_leave(self, widget):
        """鼠标离开效果"""
        widget.configure(relief=tk.RAISED, bg=self.window.cget('bg'))

    def load_playlists(self):
        response = self.api.get_user_playlists()
        if response.get("code") == 200:
            playlists = response["playlist"]
            
            # 清空现有内容
            for widget in self.left_column.winfo_children():
                widget.destroy()
            for widget in self.right_column.winfo_children():
                widget.destroy()

            # 分两栏显示歌单
            for i, playlist in enumerate(playlists):
                parent = self.left_column if i % 2 == 0 else self.right_column
                row = i // 2
                self.create_playlist_card(playlist, parent, row)

    def open_playlist(self, playlist_id):
        from playlist_detail import PlaylistDetailWindow
        detail_window = PlaylistDetailWindow(self.api, playlist_id)
        detail_window.run()

    def run(self):
        self.window.mainloop()
