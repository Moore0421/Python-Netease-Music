# Python-Netease-Music
这是一个基于 Python 和 Tkinter 构建的网易云音乐 Python GUI 客户端。

## 说在前面
- 这只是我的个人学习之作，不保证日常的使用，界面和性能还有诸多优化空间，也有诸多功能尚未实现

## 已有功能
- **用户登录**
    - 手机号登录
        - 未经测试，推荐二维码登录
    - 二维码登录
    - 保存登录状态
- **歌单显示**
    - 首页-个性化推荐歌单
    - 我的-创建/收藏歌单
    - 双击歌单显示歌单详情
- **音乐播放**
    - 歌单详情页播放
    - 显示歌曲信息
    - 基础音乐控制
        - 由于播放的实现方式特殊，暂不支持暂停和进度条控制
    - 歌词显示
        - 暂无翻译

## 未做功能
- 本地播放（已规划）
- 太多了...

## 系统需求与依赖
### 操作系统
- 由于播放的实现方式特殊，暂支持Windows

### 软件要求
- [Python](https://www.python.org/downloads/)
    - 推荐`3.8.x`及以上
    - 在安装前请选择底部`Add Python.exe to PATH`添加到系统环境变量
- [NeteaseCloudMusicAPI](https://github.com/IamFurina/NeteaseCloudMusicAPI):
    - 安装[Node.JS](https://nodejs.org/zh-cn)
    - 克隆仓库并安装运行
    - 可部署到本地或者公网服务器
    - 修改`api.py`中第六行`self.base_url`为API运行地址
    - 若要集成[NeteaseCloudMusic_PythonSDK](https://github.com/2061360308/NeteaseCloudMusic_PythonSDK)还需我研究一手
- [VLC Media Player](https://www.videolan.org/)
    - 通过调用VLC后台进程播放音乐 ← 特殊之处
    - 安装后请将安装路径`C:\Program Files\VideoLAN\VLC(默认)`添加到系统环境变量`Path`
    - 为什么？因为尝试`pygame`/`python-vlc`直接播放总是不尽人意，只好另辟蹊径

### 项目依赖
- 查看`requirement.txt`，就不说明了

## 软件运行

* 运行前请先部署好`NeteaseCloudMusicAPI`

```bash
git clone https://https://github.com/Moore0421/Python-Netease-Music
cd Python-Netease-Music
pip install -t `requirement.txt`
python login.py
```

* 然后页面上点击扫码登录即可

## 反馈建议

- 第一版功能和页面还有一些东西的实现方式过于粗糙
- 欢迎各位提交 Issues 和 PR，提供更多建议
- 非常欢迎大家参与进来，共同维护
    - 还是ELECTRON好用（x）
