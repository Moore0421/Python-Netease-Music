import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import json
import os
from api import NetEaseAPI
import threading
import time
from io import BytesIO
import qrcode

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网易云音乐登录")
        self.root.geometry("400x500")
        self.api = NetEaseAPI()
        self.qr_checking = False
        self.load_login_info()

    def setup_ui(self):
        # 创建选项卡
        self.tab_control = ttk.Notebook(self.root)
        
        # 手机号登录选项卡
        self.phone_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.phone_tab, text='手机号登录')
        
        # 二维码登录选项卡
        self.qr_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.qr_tab, text='二维码登录')
        
        self.tab_control.pack(expand=1, fill="both")
        
        self.setup_phone_login()
        self.setup_qr_login()

    def setup_phone_login(self):
        # 手机号输入框
        tk.Label(self.phone_tab, text="手机号:", font=("微软雅黑", 10)).pack(pady=10)
        self.phone_entry = tk.Entry(self.phone_tab, font=("微软雅黑", 10))
        self.phone_entry.pack()

        # 密码输入框
        tk.Label(self.phone_tab, text="密码:", font=("微软雅黑", 10)).pack(pady=10)
        self.password_entry = tk.Entry(self.phone_tab, show="*", font=("微软雅黑", 10))
        self.password_entry.pack()

        # 记住登录复选框
        self.remember_var = tk.BooleanVar()
        self.remember_checkbox = tk.Checkbutton(self.phone_tab, text="记住登录", variable=self.remember_var, font=("微软雅黑", 9))
        self.remember_checkbox.pack(pady=5)

        # 登录按钮
        tk.Button(self.phone_tab, text="登录", command=self.phone_login, font=("微软雅黑", 10, "bold")).pack(pady=20)

    def setup_qr_login(self):
        # 二维码显示区域
        self.qr_label = tk.Label(self.qr_tab)
        self.qr_label.pack(pady=20)
        
        # 刷新二维码按钮
        tk.Button(self.qr_tab, text="刷新二维码", command=self.refresh_qr, font=("微软雅黑", 10)).pack(pady=10)
        
        # 状态标签
        self.status_label = tk.Label(self.qr_tab, text="请扫描二维码登录", font=("微软雅黑", 10))
        self.status_label.pack(pady=10)
        
        # 初始化二维码
        self.refresh_qr()

    def refresh_qr(self):
        self.qr_checking = False
        qr_key_resp = self.api.get_qr_key()
        if qr_key_resp.get("code") == 200:
            key = qr_key_resp["data"]["unikey"]
            qr_resp = self.api.create_qr(key)
            if qr_resp.get("code") == 200:
                qr_url = qr_resp["data"]["qrurl"]
                # 生成二维码图片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # 转换为 PhotoImage
                img = img.resize((200, 200))
                imgbytes = BytesIO()
                img.save(imgbytes, format='PNG')
                imgbytes.seek(0)
                self.qr_image = ImageTk.PhotoImage(Image.open(imgbytes))
                self.qr_label.config(image=self.qr_image)
                
                # 开始检查扫码状态
                self.qr_key = key
                self.qr_checking = True
                threading.Thread(target=self.check_qr_status).start()

    def update_status_label(self, text):
        """安全地更新状态标签"""
        if self.root and self.status_label:
            self.root.after(0, lambda: self.status_label.config(text=text))

    def open_main_window(self, cookie):
        """安全地打开主窗口"""
        if self.root:
            self.root.after(0, lambda: self.handle_login_success(cookie))

    def handle_login_success(self, cookie, user_info):
        """处理登录成功"""
        if not user_info or not user_info.get("id"):
            print("Warning: No user info received, trying to get status")
            status = self.api.get_user_status(cookie)
            if status.get("data", {}).get("account", {}).get("id"):
                user_info = {"id": status["data"]["account"]["id"]}
            else:
                print("Error: Failed to get user status:", status)
        
        if user_info and user_info.get("id"):
            self.save_login_info(cookie, user_info)
            self.root.destroy()
            from main_window import MainWindow
            main_window = MainWindow(cookie, user_info.get("id"))
            main_window.run()
        else:
            messagebox.showerror("错误", "获取用户信息失败")

    def check_qr_status(self):
        while self.qr_checking:
            status = self.api.check_qr_status(self.qr_key)
            if status.get("code") == 800:
                self.update_status_label("二维码已过期，请刷新")
                self.qr_checking = False
                break
            elif status.get("code") == 803:
                self.update_status_label("登录成功")
                cookie = status.get("cookie", "")
                user_info = status.get("profile", {})
                self.qr_checking = False
                self.root.after(0, lambda: self.handle_login_success(cookie, user_info))
                break
            elif status.get("code") == 802:
                self.update_status_label("扫码成功，请在手机上确认")
            time.sleep(2)

    def phone_login(self):
        phone = self.phone_entry.get()
        password = self.password_entry.get()

        if not phone or not password:
            messagebox.showerror("错误", "请输入手机号和密码")
            return

        result = self.api.login(phone, password)
        if result.get("code") == 200:
            cookie = result.get("cookie", "")
            # 获取用户状态
            status = result.get("status", {})
            if status.get("data", {}).get("account", {}).get("id"):
                user_info = {"id": status["data"]["account"]["id"]}
                if self.remember_var.get():
                    self.save_login_info(cookie, user_info)
                messagebox.showinfo("成功", "登录成功！")
                self.root.destroy()
                from main_window import MainWindow
                main_window = MainWindow(cookie, user_info["id"])
                main_window.run()
            else:
                messagebox.showerror("错误", "获取用户信息失败")
        else:
            messagebox.showerror("错误", result.get("msg", "登录失败"))

    def save_login_info(self, cookie, user_info):
        """保存登录信息"""
        with open("login_info.json", "w") as f:
            json.dump({
                "cookie": cookie,
                "user_id": user_info.get("id")
            }, f)

    def load_login_info(self):
        """加载登录信息"""
        try:
            if os.path.exists("login_info.json"):
                with open("login_info.json", "r") as f:
                    data = json.load(f)
                    if data.get("cookie") and data.get("user_id"):
                        self.api.set_cookie(data["cookie"])
                        status = self.api.post_login_status(data["cookie"])
                        if status.get("data", {}).get("account", {}).get("id") == data["user_id"]:
                            self.root.destroy()
                            from main_window import MainWindow
                            main_window = MainWindow(data["cookie"], data["user_id"])
                            main_window.run()
                            return
            self.setup_ui()
        except Exception as e:
            print(f"加载登录信息失败: {e}")
            self.setup_ui()

if __name__ == "__main__":
    app = LoginWindow()
    app.root.mainloop()
