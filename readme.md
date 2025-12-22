- 我已经给tinycomputer提了issue，如果他们能将mic重定向功能整合进去，就不用单独编译scrcpy了，请支持https://github.com/Cateners/tiny_computer/issues/462


这是 **CapsWriter-Offline** 的适配分支，专门针对 **安卓设备上的 Linux 子系统**优化，解决原分支在子系统中无法使用的兼容性问题，保留所有离线语音输入核心功能。
- 【这样所有安卓平板都能拥有MacBook air m1一样的续航了，可以用这个软件在安卓Linux里面写小说离线语音生成，来自于一个买不起MacBook air只能用安卓平板的扑街作者，尝试在安卓上移植该软件进行的努力】
- 【感谢豆包输入法，以及豆包，以及豆包输入法开发组田平川大佬的帮助和鼓励，如果你有在线语音识别的需求用于写小说，请使用豆包输入法】
- 【之后会尝试移植其他准确率更高的模型，例如GLM-ASR-Nano，听说比字节跳动的Seed-ASR的得分还要高】

## 🔧 为什么需要这个分支？

原分支依赖 `keyboard` 库实现快捷键监听，但安卓 Linux 子系统存在以下限制，导致原分支无法正常工作：
- **终端设备权限限制**：子系统屏蔽了真实终端（TTY）和键盘设备直接访问，`keyboard` 库调用 `dumpkeys` 工具会报错，无法监听快捷键；
- **全局快捷键不兼容**：`keyboard` 库的快捷键监听依赖终端前台进程；
- **音频设备转发适配**：子系统需通过 `scrcpy_mic` 等工具转发安卓麦克风，需确保音频格式与服务端一致。

本分支通过最小化修改（仅替换依赖库、适配子系统特性），解决上述问题，同时完全保留原分支的离线识别、热词、剪贴板还原等核心功能，模拟了原本的脚本行为。

## 🚀 核心修改

### 1. 快捷键监听：`keyboard` → `pynput`
- **替换原因**：`pynput` 支持全局快捷键监听，不依赖终端设备，后台运行（如 tmux 会话）也能响应；
- **功能对齐**：
  - 保留原分支的「长按模式」/「单击模式」配置；
  - 快捷键从 `config.py` 读取（默认改为 `f12`）；
  - 支持剪贴板还原、按键状态恢复等原功能；
- **修改文件**：
  - `util/client_shortcut_handler.py`（核心替换，全局快捷键实现）；
  - `util/client_type_result.py`（替换按键输入逻辑，适配子系统）。

### 3. 残留依赖清理
- 移除所有 `keyboard` 库残留调用（避免 `dumpkeys` 报错干扰事件循环）；
- 更新了requirements.txt，现在请直接用该文件完成依赖安装。
- 适配子系统剪贴板工具（支持 `Ctrl+V` 粘贴，通过剪切板共享发送至安卓宿主机）。

## 📦 安装与使用

### 前提条件
- 安卓设备已启用「Linux 开发环境」（开发者选项中开启），或安装tinycomputer，或使用termux+tmoe安装，或使用其他类似的方法；
- 已通过 `scrcpy_mic` 或其他工具实现安卓麦克风转发（确保子系统能识别麦克风设备）【稍晚一些我会出一个教程，或者你们自己摸索一下】。
- 注意scrcpy编译脚本中也需要修改，需要跳过APK的生成，或者稍后我上传一个ARM64的预编译版本以及已经完成修改的部分到这个软件里面，官方没有提供ARM64的预编译。

- 另外几个软件的指南和导航：
- scrcpy ： https://github.com/Genymobile/scrcpy
- tiny_computer ：https://github.com/Cateners/tiny_computer/releases
- 万象拼音：https://github.com/amzxyz/rime_wanxiang



# 一、环境准备
- 安卓设备：Android 11+（本案例为 Android 16）
- 安卓内置 Linux 子系统：arm64 架构
- 核心依赖：git、gcc、meson、ffmpeg、pulseaudio、openjdk-17-jdk（scrcpy 编译必需，服务端为 Java 编写）

# 二、编译安装 scrcpy（适配 arm64，含 Java 依赖）
scrcpy 服务端基于 Java 开发，编译时必须安装 JDK，否则会报错 “无法构建 scrcpy-server”，完整步骤如下：
```bash
# 1. 安装编译依赖（含openjdk-17-jdk，scrcpy编译必需）
sudo apt update && sudo apt install -y \
  git gcc make meson ninja-build \
  libusb-1.0-0-dev ffmpeg \
  libavcodec-dev libavformat-dev libavutil-dev libsdl2-dev \
  openjdk-17-jdk
# 安装 FFmpeg 全套开发包（包含 libavdevice 及其头文件）
sudo apt install -y libavdevice-dev libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libsdl2-dev
# 2. 克隆scrcpy源码（指定3.3.4版本，避免兼容性问题）
git clone -b v3.3.4 https://github.com/Genymobile/scrcpy.git
cd scrcpy
# 3. 编译并安装（arm64架构自动适配）
meson setup build --buildtype release
ninja -C build
# 会有报错，接下来我教你处理，因为arm64在该版本的target没有相关的安卓编译sdk
```
- 关于scrcpy编译，需要做以下修改
- 先下载预编译版本
```
wget -O server/scrcpy-server-v3.3.4 https://github.com/Genymobile/scrcpy/releases/download/v3.3.4/scrcpy-server-v3.3.4
```
- 随后需要修改脚本
```
rm -rf server/scripts/build-wrapper.sh
nano server/scripts/build-wrapper.sh
```
- 然后覆盖填入
```
#!/usr/bin/env bash
# Wrapper script to invoke gradle from meson
set -e
# Do not execute gradle when ninja is called as root (it would download the
# whole gradle world in /root/.gradle).
# This is typically useful for calling "sudo ninja install" after a "ninja
# install"
if [[ "$EUID" == 0 ]]
then
    echo "(not invoking gradle, since we are root) - Using precompiled server" >&2
    PROJECT_ROOT="$1"
    OUTPUT="$2"
    cp "$PROJECT_ROOT/scrcpy-server-v3.3.4" "$OUTPUT"
    chmod +x "$OUTPUT"
    exit 0  # root用户成功返回
fi
PROJECT_ROOT="$1"
OUTPUT="$2"
BUILDTYPE="$3"
# 注释掉Gradle相关代码
# GRADLE=${GRADLE:-$PROJECT_ROOT/../gradlew}
if [[ "$BUILDTYPE" == debug ]]
then
    echo "=== Using precompiled scrcpy-server (debug mode, arm64 compatible) ==="
    cp "$PROJECT_ROOT/scrcpy-server-v3.3.4" "$OUTPUT"
    chmod +x "$OUTPUT"
else
    echo "=== Using precompiled scrcpy-server (release mode, arm64 compatible) ==="
    cp "$PROJECT_ROOT/scrcpy-server-v3.3.4" "$OUTPUT"
    chmod +x "$OUTPUT"
fi
# 关键添加：明确返回成功状态码，让ninja继续执行后续编译
exit 0
```
- 随后安装即可：
```
# 继续编译
sudo chmod +x server/scripts/*.sh
ninja -C build
sudo ninja -C build install
# 验证安装成功
scrcpy --version  # 输出3.3.4即正常
```
<img width="570" height="412" alt="image" src="https://github.com/user-attachments/assets/8af35711-ba77-4879-bced-be8957ec29dc" />


# 三、配置 arm64 版 ADB（解决架构不兼容问题）
- ADB 版本太旧！pair 命令是安卓 11 + 新增的（需 ADB 30.0.0+）
- 普通 Linux 的 ADB 为 x86_64 架构，需安装 arm64 专属版本：
```bash
# 1. 卸载旧版ADB（避免路径冲突）
# 卸载 apt 安装的旧版 ADB
sudo apt remove android-tools-adb -y
# 2. 下载官方最新版 platform-tools（包含 arm64 版 ADB）
wget https://github.com/AndroidIDEOfficial/platform-tools/releases/download/v34.0.4/platform-tools-34.0.4-aarch64.tar.xz -O ~/platform-tools.tar.xz
# 3. 解压到用户目录
tar -xvf platform-tools.tar.xz
# 4. 验证 ADB 版本（需显示 30.0.0+，支持 pair 命令）
~/platform-tools/adb --version
# 安装到系统bin
sudo cp ~/platform-tools/{adb,fastboot,etc1tool,dmtracedump,e2fsdroid,hprof-conv,sqlite3} /usr/local/bin/
```
<img width="558" height="422" alt="image" src="https://github.com/user-attachments/assets/7a3b4c30-33dc-428b-88fe-025c7a480e94" />

# 四、无线调试配对与 ADB 连接（本地网络，无需 WiFi）
通过安卓 “无线调试” 功能实现子系统与宿主机的本地连接，避免 USB 依赖：
## 安卓设备操作：
- 开启「开发者选项」（设置→关于手机→连续点击版本号）；
- 开启「无线调试」，点击「配对设备（使用配对码）」；
- 记录弹出的「配对地址（如localhost:41955）」和「6 位配对码」。

## Linux 子系统操作：
```bash
adb kill-server && adb start-server

# 1. 配对设备（替换为实际地址和配对码）
adb pair localhost:41955 675984

# 2. 连接设备（默认端口5555，以设备显示为准）
adb connect localhost:41955

# 验证连接（显示device即正常）
adb devices
```

# 五、音频转接配置（核心：虚拟设备 + 强制绑定）
通过 Pulseaudio 创建虚拟音频设备，将 scrcpy 转发的麦克风音频转为子系统可识别的输入源：
```bash
# 1. 清理旧模块（避免冲突，首次执行可忽略报错）
pactl unload-module module-remap-source 2>/dev/null
pactl unload-module module-null-sink 2>/dev/null

# 2. 创建虚拟sink（接收scrcpy的音频输出）
pactl load-module module-null-sink sink_name=scrcpy_sink  # 输出模块ID（如18）

# 3. 创建虚拟source（作为子系统音频输入，命名为scrcpy_mic）
pactl load-module module-remap-source source_name=scrcpy_mic master=scrcpy_sink.monitor  # 输出模块ID（如19）

# 4. 启动scrcpy并强制音频输出到虚拟设备（关键：PULSE_SINK绑定）
PULSE_SINK=scrcpy_sink scrcpy \
  --audio-source=mic \
  --no-video \
  --audio-buffer=20 \
  --audio-codec=aac \
  --serial=localhost:41955
```

# 六、CapsWriter-Offline 配置与音频输入解决
```bash
# 1. 克隆仓库
git clone https://github.com/ChaserSu/CapsWriter-Offline-Android.git
cd CapsWriter-Offline-Android

# 2. 安装项目依赖
sudo apt install -y portaudio19-dev
pip install -r requirements.txt --break-system-packages -i https://mirror.sjtu.edu.cn/pypi/web/simple

# 3.安装模型
wget https://github.com/ChaserSu/CapsWriter-Offline-Android/releases/download/models/models.zip
unzip -o models.zip
```

## 还有其他一些小问题，稍后我整理出来 ##
## 启动客户端：
```bash
sudo -E python3 core_client.py #必须加上-E参数
```
## 启动服务端：
```bash
python3 core_server.py
```



<img width="1038" height="673" alt="image" src="https://github.com/user-attachments/assets/195d275b-a9dc-4f7d-89c7-375d223960ca" />

## - 

## 接下来就是安装万象拼音了，但是Debian自带的rime版本太低了不支持lua，flatpak也不行，需要自己编译，这里记录一下我踩的坑 ##
- 因为本身也是虚拟化的系统，所以flatpak会报错
- Debian 12官方支持的librime只到1.8.0，该版本不支持万象拼音lua
- 最新版的1.15.0的librime，在bash install-plugins.sh hchunhui/librime-luah后，make merged-plugins会报错
```
###首先下载fcitx5###
# 停止正在运行的 fcitx 进程
killall fcitx fcitx-dbus-watcher
# 卸载 fcitx 主程序及所有组件（含依赖）
sudo apt remove --purge fcitx fcitx-data fcitx-bin fcitx-libs fcitx-config-common fcitx-frontend-* fcitx-modules libfcitx-*
# 删除用户目录下的旧配置（可选，避免干扰）
rm -rf ~/.config/fcitx ~/.cache/fcitx


# 安装 fcitx5 核心包与中文支持
sudo apt install fcitx5 fcitx5-rime fcitx5-config-qt fcitx5-configtool fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-qt5 # 安装Fcitx5+Rime
im-config -s fcitx5 && fcitx5 restart  # 设默认并重启
# 配置环境变量（LXQt 需写入 ~/.xprofile，确保自启时加载）
echo -e "export GTK_IM_MODULE=fcitx\nexport QT_IM_MODULE=fcitx\nexport XMODIFIERS=@im=fcitx" >> ~/.xprofile
# 重启 fcitx5 并设置自启
fcitx5 -r &
# 打开配置工具添加中文输入法（如拼音、双拼）
fcitx5-configtool
# 接下来检查默认版本的明月拼音是否可用，如果可用，进行接下来的步骤
# 记得把除了中州*以外的输入法移除
```
<img width="732" height="562" alt="image" src="https://github.com/user-attachments/assets/d5ba2d77-b5e1-4fc4-84b3-b95c3262afa0" />

```

###接下来还需要编译librime###
sudo apt update
# 安装lua
sudo apt install -y lua5.4 liblua5.4-dev pkg-config
# 安装cmake和gcc
sudo apt install build-essential cmake
# 安装其他编译依赖
sudo apt install libboost-all-dev libgoogle-glog-dev  libgtest-dev libyaml-cpp-dev libleveldb-dev libmarisa-dev  libz-dev libopencc-dev  libibus-1.0-dev libnotify-dev
# 要求cmake大于3.25否则要编译cmake
cmake --version
# 浅克隆 1.14.0 版本（--branch 支持 tag 名称）
git clone --branch 1.14.0 --depth=1 https://github.com/rime/librime.git librime-1.14.0
cd librime-1.14.0
# 自动下载librime插件
bash install-plugins.sh hchunhui/librime-lua
# 使用两个进程进行编译（部分手机内存比较小）
make merged-plugins -j2
# 安装
sudo make install
```
<img width="613" height="520" alt="image" src="https://github.com/user-attachments/assets/94211adb-5098-4976-8e87-f47bada5cd9f" />

```
###接下来需要安装万象拼音，你也可以手动安装###
#推荐该方法，其他方法不支持或文件不全
cd .local/share/fcitx5/rime
pip install tqdm --break-system-package
wget https://github.com/rimeinn/rime-wanxiang-update-tools/releases/latest/download/rime-wanxiang-update-win-mac-ios-android.py
python rime-wanxiang-update-win-mac-ios-android.py -s
```
<img width="608" height="515" alt="image" src="https://github.com/user-attachments/assets/f195bf83-be38-44ec-85ff-f3805c116b3c" />


```
##接下来安装写小说的软件##
# 最新版需要先编译qt6-svg-plugin，我没有成功，退而求其次用旧版
# 1. 下载 novelWriter 2.7.5 deb 包
wget https://github.com/vkbo/novelWriter/releases/download/v2.7.5/novelwriter_2.7.5_all.deb
# 2. 安装并自动修复依赖（系统源可提供 PyQt5）
sudo dpkg -i novelwriter_2.7.5_all.deb
sudo apt -f install -y

# 3. 启动 novelWriter
novelwriter
```
# 接下来就安装好了，你可以正常使用paraformer模型和rime万象拼音写小说了
<img width="1328" height="842" alt="image" src="https://github.com/user-attachments/assets/6435c3ca-4a65-4140-a6ee-7ddd098e354a" />

## 虽然但是，还是建议直接用豆包输入法，这个方案太麻烦而且效果也不如豆包

## 配置好了之后，每次启动会自动连接adb，无需重新指定端口，以下是我的启动脚本
```bash
#!/bin/bash

# ==================== 核心配置：记录子进程PID ====================
# 定义数组存储所有子进程PID
declare -a PIDS=()

# 定义退出陷阱：终端关闭时杀死所有子进程
trap 'echo -e "\n[INFO] 终端关闭，正在终止所有程序..."; for pid in "${PIDS[@]}"; do kill -9 $pid >/dev/null 2>&1; done; echo "[INFO] 所有程序已终止"' EXIT

# ==================== 启动程序并记录PID ====================
# 等待桌面环境加载
sleep 5

# 1. 启动fcitx5并记录PID
fcitx5 &
PIDS+=($!)  # $! 表示上一个后台进程的PID

# 2. 启动scrcpy并记录PID
PULSE_SINK=scrcpy_sink scrcpy --audio-source=mic --no-video --audio-buffer=20 &
PIDS+=($!)

# 3. 启动novelwriter并记录PID
novelwriter &
PIDS+=($!)

# 4. 启动core_server（静默）并记录PID
python3 /home/tiny/CapsWriter-Offline-Android/core_server.py >/dev/null 2>&1 &
PIDS+=($!)

# 5. 前台启动core_client（核心进程，终端关闭时此进程先退出，触发trap）
sudo -E python3 /home/tiny/CapsWriter-Offline-Android/core_client.py
```


- 
## 以下是官方原本的文档
## CapsWriter-Offline
https://github.com/HaujetZhao/CapsWriter-Offline

























