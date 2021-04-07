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

## 使用说明

AniMaid 的基础使用方式在 [README](../README.md) 有所介绍，这里介绍一些详细的使用方式，包括配置文件的一些字段，以及命令等

### qBittorrent 配置

qBittorrent 相关配置位于 `config/secret.json` 中的 `qBittorrent` 域，请设置

1. `addr` 和 `port` qBittorrent WebUI 的地址与端口
2. `username` 和 `password` WebUI 的登陆用户名和密码
3. `download_path` qBittorrent 的下载根目录
   - **请新建一个目录专门用于下载番剧**
   - 因为 AniMaid 会遍历该目录下所有文件，执行重命名和整理，如果包含非番剧文件，可能会产生意外的重命名和文件移动


### 字幕组信息的储存与添加

字幕组信息默认储存于 `data/source.json` 中，AniMaid 更新数据库时只查找这里定义过的字幕组。
所以在需要订阅某个字幕组的番剧之前，应在这个文件中添加字幕组信息。

AniMaid 也提供了命令行工具来快速添加字幕组信息:

1. 在 [bangumi.moe](https://bangumi.moe) 上打开某个字幕组的作品
2. **重要** 在打开的页面上点击作品标题，进入一个 url 类似于 `https://bangumi.moe/torrent/****` 的页面
   1. 这是因为在主页上打开的页面的 url 不包含该作品的 id
   2. 你需要点击作品标题进入作品页面，得到一个包含 `torrent` 的 url，其后显示了该作品的 id
3. 在命令行内使用如下命令快速添加一个作品对应的字幕组信息
   ```shell
   # 此处的 url 仅为样例，请替换为你找的的作品 url
   $ python3 animaid.py add-team -u https://bangumi.moe/torrent/606545e032f14c0007540c20
   ```
4. AniMaid 会自动获取该字幕组信息，并添加到数据库中
   - AniMaid 会尝试获取该字幕组的英文名称作为字幕组 id，但如果自动获取失败，会请用户手动输入一个 id
   - 你可以输入任意英文字符串 (可使用下划线) 作为字幕组 id，只要不与其他 id 冲突即可

### 番剧订阅

AniMaid 的番剧订阅规则位于 `config/follow.json`，你可以配置这个文件来订阅番剧。
你可以尝试使用 [AniMaid 预设的规则](./example/follow.json) 来学习其使用方式。

1. 在 `config/follow.json` 的 `track` 域内配置订阅规则，每一项对应一个字幕组的一些作品，每个字幕组可以有多项存在于 `track` 域内
   - 例如如下规则定义了
      - 需要从 `Sakurato` 字幕组获取番剧
         - 这里使用了 `config/source.json` 中的 `alias` 字段即字幕组 id
         - 你也可以使用其中的 `name` 字段即字幕组的全名而非 id
      - 番剧类型为 `ongoing`，类型说明见 [README](../README.md)
      - 应用一个默认的 filter `2021Winter` 来过滤 2021 年冬季番，过滤器稍后介绍
      - 订阅一个系列的番剧，其中包括
         - 订阅 `悠哉日常大王` 系列，通过正则表达式来精确匹配 (`"regex": true`)
         - 使用一个过滤器排除所有文件名内含 `繁日內嵌` 的项目，以避免重复下载此番剧的多个版本
    ```json
    {
        "team_name": "Sakurato",
        "type": "ongoing",
        "filter": [
            "2021Winter"
        ],
        "follow": [
            {
                "name": "悠哉日常大王.*1080[pP].*60FPS",
                "regex": true,
                "filter": [
                    {
                        "type": "exclude",
                        "word": [
                            "繁日內嵌"
                        ]
                    }
                ]
            }
        ]
    }
    ```
2. 同一字幕组可以有多个 `track` 内的规则，方便通过不同的过滤器订阅不同季度的番剧
3. 过滤器有两种定义方式
   1. 你可以在 `config/follow.json` 的 `filter` 字段内定义全局过滤器并赋予一个名称，之后使用此名称调用过滤器，避免重复编写过滤规则
   2. 你也可以在 `track` 内定义临时使用的过滤器
4. 过滤器的定义
   1. 每个过滤器由一个 JSON object 定义，也可以将多个 JSON object 加入一个 list 来 "串联" 几个过滤器
   2. 首先定义过滤器类型 `type`，可选 `include` 或 `exclude`
      - `include` 过滤器会输出符合过滤规则的项目，不符合规则的不会输出
      - `exclude` 会排除符合规则的项目
   3. 然后定义过滤规则，每个过滤器只有一个规则，你可以组合多个过滤器来应用多个规则
      - `word` 过滤器：检查目标文件名是否包含过滤器定义的字符串**其中之一**
      - `date` 过滤器：检查目标的发布日期是否在过滤器定义的日期范围
      - `extension` 过滤器：检查目标文件名的扩展名是否包含过滤器定义的扩展名**其中之一**
      - `filename` 过滤器：检查目标文件名是否包含过滤器定义字符串**其中之一**
5. 过滤器应用规则与顺序
   1. [隐式调用] 所有 `track` 内的目标都会默认调用 `default` 过滤器
   2. [隐式调用] `track` 目标会根据动画类型 `track.type` 调用相应过滤器，例如设置 `"type": "bundle"` 就会调用 `bundle` 过滤器
   3. [显式调用] `track` 接下来会调用用户指定的一组过滤器 `track.filter`
   4. [显式调用] `track` 最后会调用每个具体的规则自身的过滤器 `track.follow.filter`


### 文件重命名

各大字幕组在 [bangumi.moe](https://bangumi.moe) 上发布的作品的文件名都包含了一些标签，例如 `[1080p]` 或者 `[WebRip]` 等。
这些标签方便用户查看该文件的一些基础信息，但对于 PLEX 来讲，这些标签阻碍了 `HAMA` 插件自动获取番剧名，进一步导致番剧信息无法加载。

AniMaid 可以自动去除这些文件名内的标签，方便用户查看，也方便 PLEX 处理文件。
文件重命名规则位于 `config/rename.json`

1. `filter` 定义了一些文件名的过滤器，避免过度重命名（例如重命名字体文件等）
2. `file` 定义了是否重命名 "文件"，以及对 "文件" 默认使用的文件名过滤器
3. `dir` 定义了是否重命名 "目录"，以及对 "目录" 默认使用的文件名过滤器
4. `move_rule` 定义了文件移动过程中的重命名规则，例如如下规则可在一个文件的目标路径加入一个父目录，用于存放该文件对应的所有番剧
    ```json
    {
        "description": "Derive series name from media file name",
        "type": "add_parent",
        "file": "file",
        "regex": true,
        "entries": [
            {
                "source": "\\s*[v\\d]+\\.[a-zA-Z\\d\\.]+$",
                "target": ""
            }
        ]
        }
    ```
5. `rename_rule` 串联了一组重命名规则，具体的重命名效果可以查看命令行输出日志
