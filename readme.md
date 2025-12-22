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
git clone https://github.com/HaujetZhao/CapsWriter-Offline.git
cd CapsWriter-Offline

# 2. 安装项目依赖
pip install -r requirements.txt --break-system-packages -i https://mirror.sjtu.edu.cn/pypi/web/simple
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


## 配置好了之后，每次启动还需要重新打开adb，以下是我的启动脚本##
## 启动音频服务1.sh：
```bash
adb kill-server && adb start-server
adb connect localhost:41955
pactl unload-module module-remap-source 2>/dev/null
pactl unload-module module-null-sink 2>/dev/null
pactl load-module module-null-sink sink_name=scrcpy_sink
pactl load-module module-remap-source source_name=scrcpy_mic master=scrcpy_sink.monitor
PULSE_SINK=scrcpy_sink scrcpy --audio-source=mic --no-video --audio-buffer=20 --serial=localhost:41955
```
## 启动客户端2.sh：
```bash
sudo -E python3 core_client.py
```
## 启动服务端3.sh：
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

###接下来需要安装万象拼音，你也可以手动安装###
# 这个方法就有很多了
# 获得下载器，注意你可以检查一下最新版，我在使用的时候是6.2.4
wget https://github.com/rimeinn/rime-wanxiang-update-tools/releases/download/v6.2.4/rime-wanxiang-update-linux
# 安装万象拼音fcitx5-rime版本
sudo apt install jq
bash rime-wanxiang-update-linux --inputime fcitx5 --schema base --fuzhu base --dict --gram --depdir "$HOME/.local/share/fcitx5/rime"

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



- 
## 以下是官方原本的文档
## CapsWriter-Offline

![image-20240108115946521](assets/image-20240108115946521.png)  

这是 `CapsWriter-Offline` ，一个 PC 端的语音输入、字幕转录工具。

两个功能：

1. 按下键盘上的 `大写锁定键`，录音开始，当松开 `大写锁定键` 时，就会识别你的录音，并将识别结果立刻输入
2. 将音视频文件拖动到客户端打开，即可转录生成 srt 字幕

视频教程：[CapsWriter-Offline 电脑端离线语音输入工具](https://www.bilibili.com/video/BV1tt4y1d75s/)  

## 特性

1. 完全离线、无限时长、低延迟、高准确率、中英混输、自动阿拉伯数字、自动调整中英间隔
2. 热词功能：可以在 `hot-en.txt hot-zh.txt hot-rule.txt` 中添加三种热词，客户端动态载入
3. 日记功能：默认每次录音识别后，识别结果记录在 `年份/月份/日期.md` ，录音文件保存在 `年份/月份/assets` 
4. 关键词日记：识别结果若以关键词开头，会被记录在 `年份/月份/关键词-日期.md`，关键词在 `keywords.txt` 中定义
5. 转录功能：将音视频文件拖动到客户端打开，即可转录生成 srt 字幕
6. 服务端、客户端分离，可以服务多台客户端
7. 编辑 `config.py` ，可以配置服务端地址、快捷键、录音开关……

## 懒人包

对 Windows 端：

1. 请确保电脑上安装了 [Microsoft Visual C++ Redistributable 运行库](https://learn.microsoft.com/zh-cn/cpp/windows/latest-supported-vc-redist)
2. 服务端载入模型所用的 onnxruntime 只能在 Windows 10 及以上版本的系统使用
3. 服务端载入模型需要系统内存 4G，只能在 64 位系统上使用
4. 额外打包了 32 位系统可用的客户端，在 Windows 7 及以上版本的系统可用
5. 模型文件较大，单独打包，解压模型后请放入软件目录的 `models` 文件夹中

其它系统：

1. 其它系统，可以下载模型、安装依赖后从 Python 源码运行。
2. 由于我没有 Mac 电脑，无法打包 Mac 版本，只能从源码运行，可能会有诸多问题要解决。（由于系统限制，客户端需要 sudo 启动，且默认快捷键为 `right shift`）

模型说明：

1. 由于模型文件太大，为了方便更新，单独打包
2. 解压模型后请放入软件目录的 `models` 文件夹中

下载地址：

- 百度盘: https://pan.baidu.com/s/1zNHstoWZDJVynCBz2yS9vg 提取码: eu4c 
- GitHub Release: [Releases · HaujetZhao/CapsWriter-Offline](https://github.com/HaujetZhao/CapsWriter-Offline/releases) 

（百度网盘容易掉链接，补链接太麻烦了，我不一定会补链接。GitHub Releases 界面下载是最可靠的。）

![image-20240108114351535](assets/image-20240108114351535.png) 



## 功能：热词

如果你有专用名词需要替换，可以加入热词文件。规则文件中以 `#` 开头的行以及空行会被忽略，可以用作注释。

- 中文热词请写到 `hot-zh.txt` 文件，每行一个，替换依据为拼音，实测每 1 万条热词约引入 3ms 延迟

- 英文热词请写到 `hot-en.txt` 文件，每行一个，替换依据为字母拼写

- 自定义规则热词请写到 `hot-rule.txt` 文件，每行一个，将搜索和替换词以等号隔开，如 `毫安时  =  mAh` 

你可以在 `core_client.py` 文件中配置是否匹配中文多音字，是否严格匹配拼音声调。

检测到修改后，客户端会动态载入热词，效果示例：

1. 例如 `hot-zh.txt` 有热词「我家鸽鸽」，则所有识别结果中的「我家哥哥」都会被替换成「我家鸽鸽」
2. 例如 `hot-en.txt` 有热词「ChatGPT」，则所有识别结果中的「chat gpt」都会被替换成「ChatGPT」
3. 例如 `hot-rule.txt` 有热词「毫安时 = mAh」，则所有识别结果中的「毫安时」都会被替换成「mAh」

![image-20230531221314983](assets/image-20230531221314983.png)



## 功能：日记、关键词

默认每次语音识别结束后，会以年、月为分类，保存录音文件和识别结果：

- 录音文件存放在「年/月/assets」文件夹下
- 识别结果存放在「年/月/日.md」Markdown 文件中

例如今天是2023年6月5号，示例：

1. 语音输入任一句话后，录音就会被保存到 `2023/06/assets` 路径下，以时间和识别结果命名，并将识别结果保存到 `2023/06/05.md` 文件中，方便我日后查阅
2. 例如我在 `keywords.txt` 中定义了关键词「健康」，用于随时记录自己的身体状况，吃完饭后我可以按住 `CapsLock` 说「健康今天中午吃了大米炒饭」，由于识别结果以「健康」关键词开头，这条识别记录就会被保存到 `2023/06/05-健康.md` 中
3. 例如我在 `keywords.txt` 中定义了关键词「重要」，用于随时记录突然的灵感，有想法时我就可以按住 `CapsLock` 说「重要，xx问题可以用xxxx方法解决」，由于识别结果以「重要」关键词开头，这条识别记录就会被保存到 `2023/06/05-重要.md` 中

![image-20230604144824341](assets/image-20230604144824341.png)  

## 功能：转录文件

在服务端运行后，将音视频文件拖动到客户端打开，即可转录生成四个同名文件：

- `json` 文件，包含了字级时间戳
- `txt` 文件，包含了分行结果
- `merge.txt` 文件，包含了带标点的整段结果
- `srt` 文件，字幕文件

如果生成的字幕有微小错误，可以在分行的 `txt` 文件中修改，然后将 `txt` 文件拖动到客户端打开，客户端检测到输入的是 `txt` 文件，就会查到同名的 `json`  文件，结合 `json` 文件中的字级时间戳和 `txt` 文件中修正结果，更新 `srt` 字幕文件。

## 注意事项

1. 当用户安装了 `FFmpeg` 时，会以 `mp3` 格式保存录音；当用户没有装 `FFmpeg` 时，会以 `wav` 格式保存录音
2. 音视频文件转录功能依赖于 `FFmpeg`，打包版本已内置 `FFmpeg` 
3. 默认的快捷键是 `caps lock`，你可以打开 `core_client.py` 进行修改
4. MacOS 无法监测到 `caps lock` 按键，可改为 `right shift` 按键

## 修改配置

你可以编辑 `config.py` ，在开头部分有注释，指导你修改服务端、客户端的：

- 连接的地址和端口，默认是 `127.0.0.1` 和 `6006` 
- 键盘快捷键
- 是否要保存录音文件
- 要移除识别结果末尾的哪些标点，（如果你想把句尾的问号也删除掉，可以在这边加上）

![image-20240108114558762](assets/image-20240108114558762.png)  




## 下载模型

服务端使用了 [sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/index.html) ，载入阿里巴巴开源的 [Paraformer](https://www.modelscope.cn/models/damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch) 模型（[转为量化的onnx格式](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-paraformer/paraformer-models.html)），来作语音识别，整个模型约 230MB 大小。下载有已转换好的模型文件：

- [csukuangfj/sherpa-onnx-paraformer-zh-2023-09-14](https://huggingface.co/csukuangfj/sherpa-onnx-paraformer-zh-2023-09-14) 

另外，还使用了阿里巴巴的标点符号模型，大小约 1GB：

- [CT-Transformer标点-中英文-通用-large-onnx](https://www.modelscope.cn/models/damo/punc_ct-transformer_cn-en-common-vocab471067-large-onnx/summary)

**模型文件太大，并没有包含在 GitHub 库里面，你可以从百度网盘或者 GitHub Releases 界面下载已经转换好的模型文件，解压后，将 `models` 文件夹放到软件根目录** 

## 自启动、隐藏窗口、拖盘图标、Docker

Windows 隐藏黑窗口启动，见 [\#49](https://github.com/HaujetZhao/CapsWriter-Offline/issues/49)，将下述内容保存为 vbs 运行：

```
CreateObject("Wscript.Shell").Run "start_server.exe",0,True
CreateObject("Wscript.Shell").Run "start_client.exe",0,True
```

Windows 自启动，新建快捷方式，放到 `shell:startup` 目录下即可。

带拖盘图标的 GUI 版，见 [H1DDENADM1N/CapsWriter-Offline](https://github.com/H1DDENADM1N/CapsWriter-Offline/tree/GUI-(PySide6)-and-Portable-(PyStand)) 

Docker 版，见 [Garonix/CapsWriter-Offline at docker-support ](https://github.com/Garonix/CapsWriter-Offline/tree/docker-support) 


## 源码安装依赖

### \[New\] Linux 端
```bash
# for core_server.py
pip install -r requirements-server.txt  -i https://mirror.sjtu.edu.cn/pypi/web/simple
# [NOTE]: kaldi-native-fbank==1.17(使用1.18及以上会报错`lib/python3.10/site-packages/_kaldi_native_fbank.cpython-310-x86_64-linux-gnu.so: undefined symbol: _ZN3knf24OnlineGenericBaseFeatureINS_22WhisperFeatureComputerEE13InputFinishedEv`)

# for core_client.py
pip install -r requirements-client.txt  -i https://mirror.sjtu.edu.cn/pypi/web/simple
sudo apt-get install xclip   # 让core_client.py正常运行
```
**运行方式**
`core_server.py`   # 无需以 root 权限运行
`core_client.py`   # 注意: 必须以 root 权限运行!!

### Windows 端

```powershell
pip install -r requirements-server.txt
pip install -r requirements-client.txt
```

有些依赖在 `Python 3.11` 还暂时不无法安装，建议使用 `Python 3.8 - Python3.10`  

### Mac 端

在 Arm 芯片的 MacOS 电脑上（如 MacBook M1）无法使用 pip 安装 `sherpa_onnx` ，需要手动从源代码安装：

```
git clone https://github.com/k2-fsa/sherpa-onnx
cd sherpa-onnx
python3 setup.py install
```

在 MacOS 上，安装 `funasr_onnx` 依赖的时候可能会报错，缺失 `protobuf compiler`，可以通过 `brew install protobuf` 解决。

## 源码运行

1. 运行 `core_server.py` 脚本，会载入 Paraformer 模型识别模型和标点模型（这会占用2GB的内存，载入时长约 50 秒）
2. 运行 `core_client.py` 脚本，它会打开系统默认麦克风，开始监听按键（`MacOS` 端需要 `sudo`）
3. 按住 `CapsLock` 键，录音开始，松开 `CapsLock` 键，录音结束，识别结果立马被输入（录音时长短于0.3秒不算）

MacOS 端注意事项：

- MacOS 上监听 `CapsLock` 键可能会出错，需要快捷键修改为其他按键，如 `right shift` 

## 打包方法
Windows/MacOS/Linux均使用如下命令完成打包:
`pyinstaller build.spec`

## 运行方式
### Linux 
双击 `run.sh` 自动输入sudo密码且实现左右分屏展示
![](./assets/run-sh.png)





















