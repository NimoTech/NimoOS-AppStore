#!/bin/bash
set -e

# 版本号优先级: 命令行参数 > APPSTORE_VERSION 环境变量 > 默认值
# (供 nimo_os_docs/release/release.sh 从 versions.conf 注入)
VERSION="${1:-${APPSTORE_VERSION:-v1.0.9}}"
ARCHIVE_NAME="linux-all-appstore-${VERSION}.tar.gz"
TMP_DIR=$(mktemp -d)
BUILD_ROOT="${TMP_DIR}/build"

echo "Creating build directories..."
mkdir -p "${BUILD_ROOT}/sysroot/var/lib/nimoos/appstore/default.new"

echo "Copying files..."
cp -R build/* "${BUILD_ROOT}/"
cp -R Apps "${BUILD_ROOT}/sysroot/var/lib/nimoos/appstore/default.new/"
cp category-list.json "${BUILD_ROOT}/sysroot/var/lib/nimoos/appstore/default.new/"
cp recommend-list.json "${BUILD_ROOT}/sysroot/var/lib/nimoos/appstore/default.new/"
cp README.md "${BUILD_ROOT}/sysroot/var/lib/nimoos/appstore/default.new/"

echo "Removing unnecessary files (screenshots, etc.)..."
find "${BUILD_ROOT}" -iname "screenshot*" -type f -exec rm -f {} +
find "${BUILD_ROOT}" -iname "thumbnail*" -type f -exec rm -f {} +
find "${BUILD_ROOT}" -iname "icon.png" -type f -exec rm -f {} +
find "${BUILD_ROOT}" -iname "appfile.json" -type f -exec rm -f {} +

echo "Creating tarball..."
pushd "${TMP_DIR}" > /dev/null
tar zcf "${ARCHIVE_NAME}" build
popd > /dev/null

mv "${TMP_DIR}/${ARCHIVE_NAME}" ./
rm -rf "${TMP_DIR}"

echo "Package created at $(pwd)/${ARCHIVE_NAME}"