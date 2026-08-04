# NimoOS-AppStore

**A data repository, not a running service.** This repo is the static data source for the NimoOS App Store: app definitions (docker-compose templates + metadata), category/recommended/featured lists, icon and screenshot assets — packaged into a tarball for release via the packaging script. At runtime, the **NimoOS-AppManagement** service fetches and caches it under `/var/lib/nimoos/appstore/`.

This repo is forked from CasaOS-AppStore (IceWhaleTech); it keeps the vast majority of the original app definitions, with the branding swapped and ongoing maintenance on top.

---

## Directory Layout

| Path | Purpose |
|---|---|
| `Apps/` | directory of all app definitions, one subdirectory per app (161 total; latest addition is `Arize-Phoenix`, an agent-monitoring app in the Developer category, main port 6006) |
| `category-list.json` | the global category list (28 categories: Analytics / Media / AI / Network, etc.) |
| `featured-apps.json` | the featured apps list (used for the AppStore homepage banner) |
| `recommend-list.json` | the recommended apps list (homepage recommendation slot, currently ~9 apps) |
| `package_appstore.sh` | packaging script: bundles `Apps/`, `category-list.json`, `recommend-list.json` into a tarball |
| `build/` | install-time helper files, incl. `scripts/setup/script.d/99-setup-appstore.sh` (atomic appstore directory switch after unpacking) |
| `help/` | maintenance helper scripts (e.g. `action.sh`, for bulk-extracting i18n text) |
| `psd-source/` | Photoshop asset templates (`icon_template.psd`, `thumbnail_template.psd`, `screenshot_template.psd`) |
| `linux-all-appstore-v1.0.9.tar.gz` | a sample packaged release artifact (naming convention: `linux-all-appstore-<version>.tar.gz`) |

---

## Standard Layout of a Single App Directory

Using `Apps/Jellyfin/` as an example:

```
Apps/Jellyfin/
├── docker-compose.yml   # Docker Compose template (with x-casaos extension fields)
├── appfile.json         # v2.0 app metadata (backward-compat with the old format)
├── icon.png             # app icon (local backup; also served from CDN)
├── thumbnail.png        # thumbnail
├── screenshot-1.png     # screenshots (1 to N)
├── screenshot-2.png
└── changelog.txt        # changelog
```

### Key `docker-compose.yml` fields

Standard Docker Compose v3 format, with an `x-casaos` extension block added both at the top level and under `services.<name>`:

```yaml
x-casaos:                       # top level: global metadata
  architectures: [amd64, arm64]
  main: jellyfin                # main service name
  author: CasaOS Team
  category: Media
  description:
    en_US: "..."                # multilingual description (zh_CN / ja_JP / fr_FR etc. supported)
  tagline:
    en_US: "The personal Media System"
    zh_CN: "个人媒体系统"
  icon: https://cdn.jsdelivr.net/...
  thumbnail: https://cdn.jsdelivr.net/...
  screenshot_link: [...]
  index: /                      # WebUI entry path
  port_map: "8097"              # main port exposed externally

services:
  jellyfin:
    image: linuxserver/jellyfin:10.10.7
    network_mode: bridge
    ports: [...]
    volumes:
      - source: /DATA/AppData/$AppID/config  # $AppID is injected by AppManagement
        target: /config
    x-casaos:                   # service level: i18n labels describing ports/volumes/env vars
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

`$AppID`, `$TZ`, `$PUID`, `$PGID` and similar variables are expanded by AppManagement at install time.

### `appfile.json` format (v2.0)

```json
{
  "version": "2.0",
  "title": "Jellyfin",
  "name": "jellyfin",           // appid (lowercase, unique)
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

> `appfile.json` is the legacy compat format; the newer AppManagement prefers to read the `x-casaos` fields inside `docker-compose.yml`. During packaging, `appfile.json`, icons, screenshots and other bulky assets **are all stripped out by the script** and never make it into the release tarball. So new apps can ship with just a minimal `docker-compose.yml` + `icon.png` (as with `Apps/Arize-Phoenix/`, added 2026-07).

---

## The Three JSON Manifests

### `category-list.json`

The global category definitions; the AppStore UI's sidebar categories are driven from this. Entry format:

```json
{ "name": "Media", "font": "play-circle-outline", "description": "Media Apps" }
```

28 categories in total, including Analytics, Backup, Blog, Chat, Cloud, Developer, CRM, Documents, Email, File Sync, Finance, Gallery, Games, Learning, Media, Notes, Project Management, VPN, WEB, WiKi, Dapps, Downloader, Utilities, Home Automation, Network, Database, AI, and more.

### `featured-apps.json`

The featured list, used for the AppStore homepage banner/featured section. Format:

```json
[
  { "appid": "homeassistant" },
  { "appid": "jellyfin" },
  ...
]
```

Currently holds about 51 apps, spanning popular media, networking, AI, monitoring, and download apps.

### `recommend-list.json`

The recommended list, used for the AppStore homepage recommendation slot (unlike featured, it's shorter and refreshed more often). Same format as `featured-apps.json`:

```json
[
  { "appid": "weknora" },
  { "appid": "immich" },
  { "appid": "n8n" },
  ...
]
```

---

## Packaging & Distribution

### Packaging flow (`package_appstore.sh`)

```bash
bash package_appstore.sh [version]
# Version precedence: CLI argument > $APPSTORE_VERSION env var > default v1.0.9
```

Steps the script performs:

1. Create a temporary build directory `<tmp>/build/sysroot/var/lib/nimoos/appstore/default.new/`
2. Copy `build/` (containing install scripts), `Apps/`, `category-list.json`, `recommend-list.json`, `README.md` into it
3. **Strip asset files**: remove all `screenshot*`, `thumbnail*`, `icon.png`, `appfile.json` (to shrink the package)
4. Package into `linux-all-appstore-<version>.tar.gz`

Artifact naming convention: `linux-all-appstore-<version>.tar.gz`, e.g. `linux-all-appstore-v1.0.9.tar.gz`.

### Install script (`build/scripts/setup/script.d/99-setup-appstore.sh`)

After the tarball is unpacked, the install script performs an atomic directory switch:

```
/var/lib/nimoos/appstore/default      (currently active directory)
/var/lib/nimoos/appstore/default.new  (unpack target for the new version)
/var/lib/nimoos/appstore/default.old  (backup of the old version, removed once the switch succeeds)
```

Switch logic: back up `default` → rename `default.new` to `default` → delete the backup. If the rename fails, the old version is restored automatically.

### Release channel

The release pipeline injects `APPSTORE_VERSION` from `versions.conf` (see `release/` in the public [NimoOS-Build](https://github.com/NimoTech/NimoOS-Build) repo); after packaging, it's uploaded to OSS, paired with the install script for one-shot deployment.

---

## Runtime Relationship with NimoOS-AppManagement

```
NimoOS-AppStore (this repo)
  └── package_appstore.sh
        └── linux-all-appstore-<ver>.tar.gz  (published to OSS)
                │
                ▼ (unpacked on install/update)
  /var/lib/nimoos/appstore/default/
    ├── Apps/                    ← app definitions read by NimoOS-AppManagement
    ├── category-list.json       ← AppStore UI categories
    └── recommend-list.json      ← AppStore UI recommended list
                │
                ▼
  NimoOS-AppManagement.service
    - reads Apps/<name>/docker-compose.yml to install/uninstall apps
    - pushes install-progress events to the frontend via MessageBus
    - app working directory lands at /data/Apps/<name>/
    - AppData is mounted at /DATA/AppData/<AppID>/
```

AppManagement treats `default/` as the "official store" data source: it renders the UI from the `x-casaos` extension fields in `docker-compose.yml`, and when a user clicks install, it expands the `$AppID`, `$TZ`, `$PUID`, `$PGID` variables and runs `docker compose up -d`.

> **Note**: `featured-apps.json` currently only lives at the repo root and **is not included in the tarball by the packaging script** — AppManagement would need extra handling to read it.
