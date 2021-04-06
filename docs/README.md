# 安装与使用

## 安装 AniMaid

AniMaid 由 Python 3 编写，使用了 `f-string` 功能，所以需要 Python 3.6 及以上版本。
同时 AniMaid 借助 qBittorrent 进行下载，请安装 qBittorrent 并[启动 WebUI 功能](https://github.com/lgallard/qBittorrent-Controller/wiki/How-to-enable-the-qBittorrent-Web-UI)。

1. 下载本项目代码
2. 安装 Python 包 `pip3 install -r scripts/requirements.txt`
3. 第一次使用时执行 `python3 animaid.py install` 来安装预设的配置文件，之后使用时不再需要安装
4. (可选) 安装 MongoDB 来储存 AniMaid 的本地数据库和日志，若不安装可使用默认的 JSON 方式存储数据
5. (可选) 安装 PLEX 媒体服务器来观看动画，若不安装可使用任意播放器播放下载得到的番剧
   1. 在 PLEX 里安装 [HAMA](https://github.com/ZeroQI/Hama.bundle) 插件，这个插件可以自动解析番剧文件名，从 [AniDB](anidb.net) 下载番剧信息并导入 PLEX
6. (可选) 安装 Slack 来获取 AniMaid 的通知信息

## 使用截图

**PLEX 媒体库**

![plex](https://github.com/TheNetAdmin/images/raw/master/animaid/plex.png)

**Slack 通知**

![slack](https://github.com/TheNetAdmin/images/raw/master/animaid/slack.png)
