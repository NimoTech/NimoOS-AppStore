# Contributing to the NimoOS AppStore

This document describes how to contribute an app to the NimoOS AppStore.
Anyone can submit an app — you don't need to be a NimoOS developer.

**IMPORTANT**: Your PR must be *well tested* on your own NimoOS first. This is
the mandatory first step for your submission.

**NOTE**: Do not use the `latest` tag for `image`. [What's Wrong With The Docker `:latest` Tag?](https://github.com/IceWhaleTech/CasaOS-AppStore/issues/167)

## Compatibility with the CasaOS AppStore

This store is a fork of the CasaOS AppStore, and the app-definition format is
deliberately kept **identical** to it. An app definition written for CasaOS
works here unchanged, and one written here works there. We intend to keep it
that way: where CasaOS sets a rule for how apps are defined, our rule is the
same.

Concretely:

- The store-metadata extension key is `x-nimoos`, but `x-casaos` is accepted
  and normalised at load time, so either key works. If you're porting an app
  definition, you don't have to touch it.
- Every field, magic value and directory convention below behaves the same way
  it does upstream. Only the paths that name the product differ
  (`/etc/nimoos/env` rather than `/etc/casaos/env`).

If you maintain an app in both stores, submit the same `docker-compose.yml` to
both. If upstream changes a rule and we haven't caught up, open an issue — a
divergence is a bug on our side, not a decision.

## Submit process

App submission should be done via pull request. Fork this repository, prepare
the app per the guidelines below, and open the PR against `main`. CI validates
the app definition and checks that the referenced artwork exists; a maintainer
reviews from there.

## Guidelines

### Project structure

```shell
NimoOS-AppStore
├─ category-list.json   # Configuration file for category list
├─ recommend-list.json  # Configuration file for recommended apps list
├─ featured-apps.json   # Featured apps shown at the store front
├─ help                 # Help script for old version app store
├─ Apps                 # Apps Store files
├─ build                # Installation script for Apps Store
├─ package_appstore.sh  # Builds the store archive that ships with NimoOS
└─ psd-source           # Icon thumbnail screenshot PSD Templates
```

### A NimoOS App typically includes the following files

```shell
App-Name
├─ docker-compose.yml   # (Required) A valid Docker Compose file
├─ icon.png             # (Required) App icon
├─ screenshot-1.png     # (Required) At least one screenshot is needed, to demonstrate the app runs on NimoOS successfully.
├─ screenshot-2.png     # (Optional) More screenshots to demonstrate different functionalities is highly recommended.
├─ screenshot-3.png     # (Optional) ...
└─ thumbnail.png        # (Optional) A thumbnail file is needed only if you want it to be featured in AppStore front. (see specification at bottom)
```

Many existing apps also carry a legacy `appfile.json`, kept for compatibility
with older clients. New submissions don't need one — `docker-compose.yml` is
the source of truth.

#### A NimoOS App is a Docker Compose app, or a *compose app*

Each directory under [Apps](Apps) corresponds to a NimoOS App. The directory
should contain at least a `docker-compose.yml` file:

- It should be a valid [Docker Compose file](https://docs.docker.com/compose/compose-file/). Here are some requirements (but not limited to):

  - `name` must contain only lower case letters, numbers, underscore "`_`" and hyphen "`-`" (in other words, must match `^[a-z0-9][a-z0-9_-]*$`)

- Image tag should be specific, e.g. `:0.1.2`, instead of `:latest`.

  > [What's Wrong With The Docker `:latest` Tag?](https://github.com/IceWhaleTech/CasaOS-AppStore/issues/167)

- The `name` property is used as the *store App ID*, which should be unique across all apps.

    For example, in the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml#L1), its store App ID is `syncthing`:

    ```yaml
    name: syncthing
    services:
        syncthing:
            image: linuxserver/syncthing:<specific version>
    ...
    ```

- Language codes are case sensitive and should use the standard format, e.g. en_US, zh_CN.

- There are a few system wide variables that can be used in `environment` and `volumes`:

    ```yaml
    environment:
      PGID: $PGID                           # Preset Group ID
      PUID: $PUID                           # Preset User ID
      TZ: $TZ                               # Current system timezone
    ...
    volumes:
      - type: bind
        source: /DATA/AppData/$AppID/config # $AppID = app name, e.g. syncthing
    ```

- Store metadata, also called *store info*, is stored under the [extension](https://docs.docker.com/compose/compose-file/#extension) property `x-nimoos` (or `x-casaos` — see the compatibility note above) at two positions.

    1. Service level

        A `docker-compose.yml` file can contain one or more `services`. Each [service](https://docs.docker.com/compose/compose-file/#services-top-level-element) can have its own store info.

        For the same example, at the bottom of the `syncthing` service in the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml)

        ```yaml
        x-nimoos:
            envs:                           # description of each environment variable
                ...
              - container: PUID
                description:
                    en_US: Run Syncthing as specified uid.
            ports:                          # description of each port
              - container: "8384"
                description:
                    en_US: WebUI HTTP Port
                ...
            volumes:                        # description of each volume
                - container: /config
                  description:
                      en_US: Syncthing config directory.
                - container: /DATA
                  description:
                    en_US: Syncthing Accessible Directory.
        ```

    2. Compose app level

        For the same example, at the bottom of the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml)

        ```yaml
        x-nimoos:
            architectures:                  # a list of architectures that the app supports
                - amd64
                - arm
                - arm64
            main: syncthing                 # the name of the main service under `services`
            author: CasaOS Team
            category: Backup
            description:                    # multiple locales are supported
                en_US: Syncthing is a continuous file synchronization program. It synchronizes files between two or more computers in real time, safely protected from prying eyes. Your data is your data alone and you deserve to choose where it is stored, whether it is shared with some third party, and how it's transmitted over the internet.
            developer: Syncthing
            icon: https://get.nimotech.ai/nimoos/appstore/Apps/Syncthing/icon.png
            tagline:                        # multiple locales are supported
                en_US: Free, secure, and distributed file synchronisation tool.
            thumbnail: ""
            title:                          # multiple locales are supported
                en_US: Syncthing
            tips:
                before_install:
                    en_US: |
                        (some notes for user to read prior to installation, such as preset `username` and `password` - markdown is supported!)
            index: /                        # the index page for web UI, e.g. index.html
            port_map: "8384"                # the port for web UI
        ```

        The `author` field names whoever wrote and maintains the app
        definition. Existing entries credit `CasaOS Team` or an individual
        community contributor; leave those as they are, and put your own name
        there for an app you contribute.

    3. Magic Value

        For resolving some cases, NimoOS provides some magic values to power your application:

        - Environment variable

            Your application can read an environment variable that the user set, such as `OPENAI_API_KEY`. It is stored in `/etc/nimoos/env`. The user sets it once and it can be used anywhere. It can be changed by API; after a change, all applications are re-upped to inject the new env var.

            **Note**: changing the config does not change the env var of the current container. To set an env var, you should use the CLI.

        - `WEBUI_PORT`

            Your `docker-compose.yml` can use `WEBUI_PORT` to set the WebUI port. NimoOS will assign an available port for your application. You can use it like this:

            ```yaml
            ...
            ports:
                - target: 5230
                published: ${WEBUI_PORT}
                protocol: tcp
            ...
            x-nimoos:
                architectures:
                    - amd64
                    - arm64
                    - arm
            ...
                port_map: ${WEBUI_PORT}
            ```

            or

            ```yaml
            ...
            ports:
                - target: 5230
                published: ${WEBUI_PORT:-5230}
                protocol: tcp
            ...
            x-nimoos:
                architectures:
                    - amd64
                    - arm64
                    - arm
            ...
                port_map: ${WEBUI_PORT:-5230}
            ```

            **Note**: `WEBUI_PORT` is allocated once. It guarantees the port is available when allocated. If the port is later used by another application, it is not reallocated.

## Requirements for Featured Apps

Once in a while, we pick certain apps as featured apps and display them at the AppStore front. The standard for apps to be featured is a bit higher than the rest of the apps:

- Icon image should be a transparent background PNG image with a size of 192x192 pixels.
- Thumbnail image should be 784x442 pixels, with a rounded corner mask. It is recommended to be saved as a PNG image with a transparent background.
- Screenshot image should be 1280x720 pixels and can be saved in either PNG or JPG format. Please try to keep the file size as small as possible.

Please find the prepared [PSD template files](psd-source), to quickly create the above images if you need.

## Anything else

The general contribution rules for NimoOS repositories — the DCO sign-off, pull
request conventions, the code of conduct — are in the
[organisation-wide contributing guide](https://github.com/NimoTech/.github/blob/main/CONTRIBUTING.md).

If you have any feedback or suggestions about this contributing process, please
let us know via Discord or Issues immediately. Thanks!
