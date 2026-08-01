# NimoOS-AppStore

**数据仓库,不是运行的服务。** 本仓库是 NimoOS 应用商店的静态数据源:存放应用定义(docker-compose 模板 + 元数据)、分类/推荐/精选清单、图标与截图素材,通过打包脚本生成 tar 包发布;运行时由 **NimoOS-AppManagement** 服务拉取并缓存到 `/var/lib/nimoos/appstore/` 目录使用。

本仓库 fork 自 CasaOS-AppStore(IceWhaleTech),保留了绝大多数原始 app 定义,在此基础上替换品牌标识并持续维护。

---

## 目录结构

| 路径 | 用途 |
|---|---|
| `Apps/` | 所有应用定义目录,每个子目录是一个独立应用(共 161 个;最新新增 `Arize-Phoenix`,agent 监控,Developer 类,主端口 6006) |
| `category-list.json` | 全局分类列表(Analytics / Media / AI / Network 等 28 个类别) |
| `featured-apps.json` | 精选应用列表(AppStore 首页 Banner 展示用) |
| `recommend-list.json` | 推荐应用列表(首页推荐位,目前约 9 个) |
| `package_appstore.sh` | 打包脚本:将 `Apps/`、`category-list.json`、`recommend-list.json` 打成 tar 包 |
| `build/` | 安装辅助文件:含 `scripts/setup/script.d/99-setup-appstore.sh`(解包后原子切换 appstore 目录) |
| `help/` | 维护辅助脚本(如 `action.sh`,用于批量提取 i18n 文本) |
| `psd-source/` | Photoshop 素材模板(`icon_template.psd`、`thumbnail_template.psd`、`screenshot_template.psd`) |
| `linux-all-appstore-v1.0.9.tar.gz` | 已打包的发布产物示例(命名规则:`linux-all-appstore-<version>.tar.gz`) |

---

## 单个应用目录的标准结构

以 `Apps/Jellyfin/` 为例:

```
Apps/Jellyfin/
├── docker-compose.yml   # Docker Compose 模板(含 x-casaos 扩展字段)
├── appfile.json         # v2.0 应用元数据(向后兼容旧格式)
├── icon.png             # 应用图标(本地备份,CDN 亦有)
├── thumbnail.png        # 缩略图
├── screenshot-1.png     # 截图(1~N 张)
├── screenshot-2.png
└── changelog.txt        # 更新日志
```

### `docker-compose.yml` 关键字段

标准 Docker Compose v3 格式,在 `services.<name>` 和顶层各加一个 `x-casaos` 扩展块:

```yaml
x-casaos:                       # 顶层:全局元数据
  architectures: [amd64, arm64]
  main: jellyfin                # 主服务名
  author: CasaOS Team
  category: Media
  description:
    en_US: "..."                # 多语言描述(支持 zh_CN / ja_JP / fr_FR 等)
  tagline:
    en_US: "The personal Media System"
    zh_CN: "个人媒体系统"
  icon: https://cdn.jsdelivr.net/...
  thumbnail: https://cdn.jsdelivr.net/...
  screenshot_link: [...]
  index: /                      # WebUI 入口路径
  port_map: "8097"              # 对外暴露的主端口

services:
  jellyfin:
    image: linuxserver/jellyfin:10.10.7
    network_mode: bridge
    ports: [...]
    volumes:
      - source: /DATA/AppData/$AppID/config  # $AppID 由 AppManagement 注入
        target: /config
    x-casaos:                   # 服务级:描述各端口/卷/环境变量的 i18n 标签
      ports:
        - container: "8096"
          description:
            en_us: WebUI HTTP Port
            zh_cn: WebUI HTTP端口
      volumes:
        - container: /config
          description:
            en_us: Jellyfin config directory.
```

`$AppID`、`$TZ`、`$PUID`、`$PGID` 等变量由 AppManagement 在安装时展开。

### `appfile.json` 格式(v2.0)

```json
{
  "version": "2.0",
  "title": "Jellyfin",
  "name": "jellyfin",           // appid(小写,唯一)
  "icon": "https://...",
  "tagline": "...",
  "overview": "...",
  "thumbnail": "https://...",
  "screenshots": ["https://..."],
  "category": ["Media"],
  "developer": { "name": "Jellyfin", "website": "https://jellyfin.org/" },
  "adaptor":   { "name": "CasaOS Team", "website": "https://www.casaos.io" },
  "container": {
    "image": "linuxserver/jellyfin:latest",
    "web_ui": { "http": "8096", "path": "/" },
    "envs":    [{ "key": "TZ", "value": "$TZ", "configurable": "no" }],
    "ports":   [{ "container": "8096", "host": "8096", "allocation": "preferred" }],
    "volumes": [{ "container": "/config", "host": "/DATA/AppData/$AppID/config" }],
    "constraints": { "min_memory": 256, "min_storage": 1024 }
  },
  "abilities": { "notification": false, "widgets": false }
}
```

> `appfile.json` 是旧版兼容格式;新版 AppManagement 优先读取 `docker-compose.yml` 中的 `x-casaos` 字段。打包时 `appfile.json`、图标、截图等体积较大的素材**均被脚本剔除**,不进入发布 tar 包。因此新增应用可以只提供 `docker-compose.yml` + `icon.png` 的最小结构(如 2026-07 新增的 `Apps/Arize-Phoenix/`)。

---

## 三个 JSON 清单

### `category-list.json`

全局分类定义,AppStore UI 的侧边栏分类由此驱动。每项格式:

```json
{ "name": "Media", "font": "play-circle-outline", "description": "Media Apps" }
```

共 28 个类别,包括 Analytics、Backup、Blog、Chat、Cloud、Developer、CRM、Documents、Email、File Sync、Finance、Gallery、Games、Learning、Media、Notes、Project Management、VPN、WEB、WiKi、Dapps、Downloader、Utilities、Home Automation、Network、Database、AI 等。

### `featured-apps.json`

精选列表,用于 AppStore 首页 Banner/Featured 区域展示。格式:

```json
[
  { "appid": "homeassistant" },
  { "appid": "jellyfin" },
  ...
]
```

目前收录约 51 个应用,涵盖媒体、网络、AI、监控、下载等热门应用。

### `recommend-list.json`

推荐列表,用于 AppStore 首页推荐位(与 featured 不同,数量少、更新频率高)。格式与 `featured-apps.json` 相同:

```json
[
  { "appid": "weknora" },
  { "appid": "immich" },
  { "appid": "n8n" },
  ...
]
```

---

## 打包与分发

### 打包流程(`package_appstore.sh`)

```bash
bash package_appstore.sh [version]
# 版本优先级: 命令行参数 > $APPSTORE_VERSION 环境变量 > 默认值 v1.0.9
```

脚本执行步骤:

1. 创建临时构建目录 `<tmp>/build/sysroot/var/lib/nimoos/appstore/default.new/`
2. 将 `build/`(含安装脚本)、`Apps/`、`category-list.json`、`recommend-list.json`、`README.md` 复制进去
3. **剔除素材文件**:删除所有 `screenshot*`、`thumbnail*`、`icon.png`、`appfile.json`(减小包体积)
4. 打包成 `linux-all-appstore-<version>.tar.gz`

产物命名规则:`linux-all-appstore-<version>.tar.gz`,例如 `linux-all-appstore-v1.0.9.tar.gz`。

### 安装脚本(`build/scripts/setup/script.d/99-setup-appstore.sh`)

tar 包解包后,安装脚本执行原子目录切换:

```
/var/lib/nimoos/appstore/default      (当前生效目录)
/var/lib/nimoos/appstore/default.new  (新版解包目标)
/var/lib/nimoos/appstore/default.old  (旧版备份,切换成功后删除)
```

切换逻辑:备份 `default` → 将 `default.new` 重命名为 `default` → 删除备份。若重命名失败,自动恢复旧版。

### 发布渠道

发布链路从 `versions.conf` 注入 `APPSTORE_VERSION`(见公开仓 [NimoOS-Build](https://github.com/NimoTech/NimoOS-Build) 的 `release/`),打包后上传到 OSS,配合安装脚本一键部署。

---

## 与 NimoOS-AppManagement 的运行时关系

```
NimoOS-AppStore (本仓库)
  └── package_appstore.sh
        └── linux-all-appstore-<ver>.tar.gz  (发布到 OSS)
                │
                ▼ (安装/更新时解包)
  /var/lib/nimoos/appstore/default/
    ├── Apps/                    ← NimoOS-AppManagement 读取应用定义
    ├── category-list.json       ← AppStore UI 分类
    └── recommend-list.json      ← AppStore UI 推荐列表
                │
                ▼
  NimoOS-AppManagement.service
    - 读取 Apps/<name>/docker-compose.yml 安装/卸载应用
    - 通过 MessageBus 推送安装进度事件到前端
    - 应用工作目录落到 /data/Apps/<name>/
    - AppData 挂载到 /DATA/AppData/<AppID>/
```

AppManagement 将 `default/` 视为「官方商店」数据源,读取 `docker-compose.yml` 中的 `x-casaos` 扩展字段渲染 UI,并在用户点击安装时展开 `$AppID`、`$TZ`、`$PUID`、`$PGID` 变量后执行 `docker compose up -d`。

> **注意**:`featured-apps.json` 目前仅保存于本仓库根目录,**未被打包脚本收入 tar**,如需 AppManagement 读取需额外处理。
