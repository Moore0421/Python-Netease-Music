import requests
import time

class NetEaseAPI:
    def __init__(self):
        self.base_url = "http://localhost:3000"  # 网易云API地址
        self.cookie = None  # 添加cookie属性
        self.user_id = None  # 添加用户ID属性
        self.headers = {}    # 添加请求头

    def login(self, phone, password):
        """手机号登录接口"""
        try:
            timestamp = str(int(time.time() * 1000))
            response = requests.post(
                f"{self.base_url}/login/cellphone", 
                data={
                    "phone": phone,
                    "password": password,
                    "timestamp": timestamp
                }
            )
            result = response.json()
            print("Login response:", result)
            
            if result.get("code") == 200:
                result["status"] = self.get_user_status(result.get("cookie"))
            
            return result
        except Exception as e:
            print(f"Login error: {e}")
            return {"code": -1, "msg": f"登录失败: {str(e)}"}

    def get_qr_key(self):
        """获取二维码key"""
        try:
            timestamp = str(int(time.time() * 1000))
            response = requests.get(
                f"{self.base_url}/login/qr/key",
                params={"timestamp": timestamp}
            )
            return response.json()
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    def create_qr(self, key):
        """生成二维码"""
        try:
            timestamp = str(int(time.time() * 1000))
            response = requests.get(
                f"{self.base_url}/login/qr/create",
                params={
                    "key": key,
                    "qrimg": True,
                    "timestamp": timestamp
                }
            )
            return response.json()
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    def check_qr_status(self, key):
        """检查二维码状态"""
        try:
            timestamp = str(int(time.time() * 1000))
            response = requests.get(
                f"{self.base_url}/login/qr/check", 
                params={
                    "key": key,
                    "timestamp": timestamp
                }
            )
            result = response.json()
            print("QR status:", result)
            if result.get("code") == 803:
                cookie = result.get("cookie")
                status = self.post_login_status(cookie)
                if status.get("data", {}).get("account"):
                    result["profile"] = {"id": status["data"]["account"]["id"]}
            return result
        except Exception as e:
            print(f"QR check error: {e}")
            return {"code": -1, "msg": str(e)}

    def post_login_status(self, cookie=None):
        """获取登录状态"""
        try:
            timestamp = str(int(time.time() * 1000))
            headers = self.headers
            if cookie:
                if isinstance(cookie, dict):
                    cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
                else:
                    cookie_str = cookie
                headers = {'Cookie': cookie_str}
            
            print("Checking login status with headers:", headers)
            print("Using timestamp:", timestamp)
            
            response = requests.post(
                f"{self.base_url}/login/status",
                params={"timestamp": timestamp},
                data={"cookie": cookie} if cookie else {},
                headers=headers
            )
            result = response.json()
            print("Login status check result:", result)
            return result
        except Exception as e:
            print(f"Get login status error: {e}")
            return {"code": -1, "msg": str(e)}

    def get_user_status(self, cookie=None):
        """获取用户状态的包装方法"""
        return self.post_login_status(cookie)

    def get_personalized_playlists(self, limit=30):
        """获取推荐歌单"""
        try:
            response = requests.get(
                f"{self.base_url}/personalized", 
                params={"limit": limit},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取推荐歌单失败: {e}")
            return {"code": -1, "msg": str(e)}

    def set_cookie(self, cookie):
        """设置cookie和请求头"""
        self.cookie = cookie
        if isinstance(cookie, dict):
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
        else:
            cookie_str = cookie
        if 'MUSIC_U=' not in cookie_str:
            if '__csrf=' in cookie_str:
                csrf = cookie_str.split('__csrf=')[1].split(';')[0]
                cookie_str += f'; MUSIC_U={csrf}'
        self.headers = {'Cookie': cookie_str}
        print("Set cookie headers:", self.headers)

    def set_user_info(self, cookie, user_id):
        """设置用户信息"""
        self.set_cookie(cookie)
        self.user_id = user_id

    def get_playlist_detail(self, playlist_id):
        """获取歌单详情"""
        try:
            response = requests.get(
                f"{self.base_url}/playlist/detail",
                params={"id": playlist_id},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取歌单详情失败: {e}")
            return {"code": -1, "msg": str(e)}

    def get_playlist_tracks(self, playlist_id):
        """获取歌单所有歌曲"""
        try:
            response = requests.get(
                f"{self.base_url}/playlist/track/all",
                params={"id": playlist_id},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取歌单歌曲失败: {e}")
            return {"code": -1, "msg": str(e)}

    def get_user_playlists(self):
        """获取用户歌单"""
        try:
            response = requests.get(
                f"{self.base_url}/user/playlist",
                params={"uid": self.user_id,
                        "limit": 40}, 
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取用户歌单失败: {e}")
            return {"code": -1, "msg": str(e)}

    def get_song_url(self, song_id):
        """获取歌曲播放链接"""
        try:
            response = requests.get(
                f"{self.base_url}/song/url",
                params={
                    "id": song_id,
                    "level": "standard",
                },
                headers=self.headers
            )
            result = response.json()
            print("Song URL response:", result)
            return result
        except Exception as e:
            print(f"获取歌曲链接失败: {e}")
            return {"code": -1, "msg": str(e)}

    def get_song_lyric(self, song_id):
        """获取歌词"""
        try:
            response = requests.get(
                f"{self.base_url}/lyric",
                params={"id": song_id},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取歌词失败: {e}")
            return {"code": -1, "msg": str(e)}

    def get_song_detail(self, song_id):
        """获取歌曲详情"""
        try:
            response = requests.get(
                f"{self.base_url}/song/detail",
                params={"ids": song_id},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"获取歌曲详情失败: {e}")
            return {"code": -1, "msg": str(e)}
