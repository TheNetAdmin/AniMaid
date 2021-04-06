# AniMaid - Animation Maid

AniMaid 是一个番剧自动下载与整理的工具。AniMaid 可以读取 [bangumi.moe](https://bangumi.moe) 提供的 [API](https://github.com/BangumiMoe) 来获取各个字幕组最新发布的番剧，然后通过用户预先定义的规则筛选番剧，自动加入 qBittorrent 下载，并在下载完成后进行重命名和归档整理，方便本地观看或者在 PLEX 等媒体服务器上观看。

## 使用

1. 安装 qBittorrent 与 Python 3 环境，具体说明参见[安装文档](.docs/README.md)
2. 一些设置工作
   1. **配置**：在 `config/config.json` 内设置番剧的存放地址 `"path"` 字段
      - 预设的配置文件里定义了两种番剧类型 `ongoing` 即当季正在播放的番剧，以及 `bundle` 即合集版番剧
      - 两种番剧对应了不同的文件路径与番剧名筛选规则（比如 `ongoing` 会屏蔽文件名含有 `合集` 的番剧，这是因为字幕组往往会在季末发布一个合集版，屏蔽合集版可以避免重复下载）
   2. **关注**：在 `data/source.json` 内设置要关注的字幕组的信息
      - 预设的文件内已经包含了一些字幕组，AniMaid 也提供了一个命令来自动添加字幕组，参见[详细使用说明]()
   3. **追番**：在 `config/follow.json` 内设置番剧名过滤规则
      - AniMaid 可以通过这些规则筛选各字幕组的番剧
      - 预设的文件内已包含了一些规则，你也可以根据[使用文档]()添加更多的规则
      - 请浏览 [bangumi.moe](https://bangumi.moe) 的主页确定番剧名与相关的字幕组信息
3. 配置得当之后，通过如下命令更新 AniMaid 的数据库
   ```shell
   # 仅从 bangumi.moe 更新数据库并发现新番剧，不新建下载任务
   $ python3 animaid.py update
   # 通过以上命令的输出确定自动发现的番剧没有问题后，通过如下命令更新数据库
   # 并自动新建下载任务（仅新建任务，没有送入 qBittorrent 也没有开始下载）
   $ python3 animaid.py update -a
   ```
4. 开始下载
   ```shell
   # 连接 qBittorrent 客户端，执行下载任务
   $ python3 animaid.py download
   ```
5. 下载完成后，通过如下命令整理文件，重命名并移出下载目录 (`config/config.json: "path.source"`)，移入媒体目录`config/config.json: "path.target"`)
   ```shell
   # 整理归档
   $ python3 animaid.py organize
   ```
   - 重命名的过程可以去掉文件名内的多余信息（例如清晰度 `[1080p]` 或者视频格式 `[MKV]` 等标签，方便查看也方便媒体服务器读取相关信息）
   - 一个重命名样例输出
    ```shell
    origin: [KTXP][LOG_HORIZON_Entaku_Houkai][01][BIG5][X264_AAC][720p](48920FFC).mp4 
        --> Log Horizon S3 01.mp4
    ```



## 开源协议

本项目代码基于 MIT 协议开源。

本项目所使用的 bangumi.moe 站点的 [API](https://github.com/BangumiMoe) 版权归原作者所有。
**请合理使用 API，不要过度请求，以免给 bangumi.moe 站点带来不必要的访问压力。**
