# coding: utf-8
# 替换原 keyboard 库为 pynput，保留原导入结构
from pynput import keyboard as pynput_keyboard
from util.client_cosmic import Cosmic, console
from config import ClientConfig as Config

import time
import asyncio
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from util.client_send_audio import send_audio
from util.my_status import Status

# 保留原有的全局变量（完全不变）
task = asyncio.Future()
status = Status('开始录音', spinner='point')
pool = ThreadPoolExecutor()
pressed = False
released = True
event = Event()

# ==================== 适配 pynput 的按键验证（替换原 shortcut_correct，逻辑不变）====================
def shortcut_correct(e: object) -> bool:
    """
    保留原逻辑：归一化按键名（处理 left/right 修饰键），验证是否匹配 Config.shortcut
    e：适配后的虚拟事件对象（模拟原 keyboard.KeyboardEvent 结构）
    """
    # 模拟原 keyboard.normalize_name 功能：归一化按键名
    def normalize_name(name: str) -> str:
        return name.lower().replace('left ', '').replace('right ', '')
    
    key_expect = normalize_name(Config.shortcut)
    key_actual = normalize_name(e.name)
    if key_expect != key_actual:
        return False
    return True

# ==================== 适配 pynput 的事件转换（新增：将 pynput 事件转为原代码兼容格式）====================
class VirtualKeyboardEvent:
    """虚拟事件对象，完全模拟原 keyboard.KeyboardEvent 的结构和属性，让原逻辑无需修改"""
    def __init__(self, event_type: str, key: object):
        self.event_type = event_type  # 'down' 或 'up'
        self.key = key                # pynput 按键对象
        # 模拟原 e.name 属性（归一化后的按键名）
        if key == pynput_keyboard.Key.f12:
            self.name = 'f12'
        elif key == pynput_keyboard.Key.caps_lock:
            self.name = 'caps lock'
        elif key == pynput_keyboard.Key.shift_l:
            self.name = 'left shift'
        elif key == pynput_keyboard.Key.shift_r:
            self.name = 'right shift'
        elif key == pynput_keyboard.Key.ctrl_l:
            self.name = 'left ctrl'
        elif key == pynput_keyboard.Key.ctrl_r:
            self.name = 'right ctrl'
        else:
            self.name = str(key).lower().replace("'", "")

# ==================== 保留原有的录音控制逻辑（100% 不变）====================
def launch_task():
    global task
    t1 = time.time()
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put({'type': 'begin', 'time': t1, 'data': None}),
        Cosmic.loop
    )
    Cosmic.on = t1
    status.start()
    task = asyncio.run_coroutine_threadsafe(
        send_audio(),
        Cosmic.loop,
    )

def cancel_task():
    Cosmic.on = False
    status.stop()
    task.cancel()

def finish_task():
    global task
    Cosmic.on = False
    status.stop()
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put(
            {'type': 'finish',
             'time': time.time(),
             'data': None
             },
        ),
        Cosmic.loop
    )

# ==================== 保留原有的单击模式逻辑（100% 不变）====================
def count_down(e: Event):
    time.sleep(Config.threshold)
    e.set()

def manage_task(e: Event):
    on = Cosmic.on
    if not on:
        launch_task()
    if e.wait(timeout=Config.threshold * 0.8):
        if Cosmic.on and on:
            finish_task()
    else:
        if not on:
            cancel_task()
        # 长按，发送按键（替换为 pynput 实现，保留原逻辑）
        send_shortcut()

def click_mode(e: VirtualKeyboardEvent):
    global pressed, released, event
    if e.event_type == 'down' and released:
        pressed, released = True, False
        event = Event()
        pool.submit(count_down, event)
        pool.submit(manage_task, event)
    elif e.event_type == 'up' and pressed:
        pressed, released = False, True
        event.set()

# ==================== 保留原有的长按模式逻辑（100% 不变）====================
def hold_mode(e: VirtualKeyboardEvent):
    """像对讲机一样，按下录音，松开停止"""
    global task
    if e.event_type == 'down' and not Cosmic.on:
        launch_task()
    elif e.event_type == 'up':
        if Cosmic.on:
            duration = time.time() - Cosmic.on
            if duration < Config.threshold:
                cancel_task()
            else:
                finish_task()
                if Config.restore_key:
                    time.sleep(0.01)
                    # 恢复按键状态（替换为 pynput 实现，保留原逻辑）
                    send_shortcut()

# ==================== 保留原有的 handler 逻辑（100% 不变）====================
def hold_handler(e: VirtualKeyboardEvent) -> None:
    if not shortcut_correct(e):
        return
    hold_mode(e)

def click_handler(e: VirtualKeyboardEvent) -> None:
    if not shortcut_correct(e):
        return
    click_mode(e)

# ==================== pynput 适配工具函数（新增：替换原 keyboard.send）====================
def send_shortcut():
    """模拟发送 Config.shortcut 配置的按键（替换原 keyboard.send）"""
    keyboard = pynput_keyboard.Controller()
    shortcut = Config.shortcut.lower()
    try:
        # 根据配置的快捷键名发送对应按键
        if shortcut == 'f12':
            keyboard.press(pynput_keyboard.Key.f12)
            keyboard.release(pynput_keyboard.Key.f12)
        elif shortcut == 'caps lock':
            keyboard.press(pynput_keyboard.Key.caps_lock)
            keyboard.release(pynput_keyboard.Key.caps_lock)
        elif shortcut == 'left shift' or shortcut == 'shift':
            keyboard.press(pynput_keyboard.Key.shift_l)
            keyboard.release(pynput_keyboard.Key.shift_l)
        elif shortcut == 'right shift':
            keyboard.press(pynput_keyboard.Key.shift_r)
            keyboard.release(pynput_keyboard.Key.shift_r)
        elif shortcut == 'left ctrl' or shortcut == 'ctrl':
            keyboard.press(pynput_keyboard.Key.ctrl_l)
            keyboard.release(pynput_keyboard.Key.ctrl_l)
        # 可扩展其他按键（如 'a'、'f5' 等）
        else:
            keyboard.press(shortcut)
            keyboard.release(shortcut)
    except Exception as e:
        console.print(f"发送快捷键失败：{e}")

# ==================== pynput 全局快捷键绑定（核心修复：非阻塞，模拟原 keyboard.hook_key）====================
def on_pynput_press(key):
    """pynput 按下事件：转换为虚拟事件，调用原 handler"""
    try:
        virtual_event = VirtualKeyboardEvent('down', key)
        if Config.hold_mode:
            hold_handler(virtual_event)
        else:
            click_handler(virtual_event)
    except Exception as e:
        pass  # 忽略无关按键错误

def on_pynput_release(key):
    """pynput 释放事件：转换为虚拟事件，调用原 handler"""
    try:
        virtual_event = VirtualKeyboardEvent('up', key)
        if Config.hold_mode:
            hold_handler(virtual_event)
        else:
            click_handler(virtual_event)
    except Exception as e:
        pass  # 忽略无关按键错误

def bond_shortcut():
    """
    核心修复：去掉 listener.join()，设置守护线程，完全模拟原 keyboard.hook_key 的非阻塞行为
    原 keyboard.hook_key 是异步非阻塞的，pynput 需保持一致，不阻塞事件循环
    """
    try:
        # 启动 pynput 全局监听（关键修改：daemon=True 设为守护线程，非阻塞）
        listener = pynput_keyboard.Listener(
            on_press=on_pynput_press,
            on_release=on_pynput_release,
            suppress=Config.suppress  # 保留原 suppress 配置
        )
        listener.daemon = True  # 模拟原 keyboard 库：守护线程，不阻塞主程序
        listener.start()  # 非阻塞启动，和原 keyboard.hook_key 行为一致
        console.print(f"✅ 全局快捷键已绑定：{Config.shortcut}（{'长按' if Config.hold_mode else '单击'}模式）")
        console.print(f"📌 操作方式：{'按住 ' + Config.shortcut + ' 录音，松开停止' if Config.hold_mode else '按 ' + Config.shortcut + ' 启动录音，再按一次停止'}")
        
        # 移除 listener.join()！ 此句是阻塞元凶，原 keyboard 库无此阻塞行为
    except Exception as e:
        console.print(f"❌ 绑定快捷键失败：{e}")
        input("按回车退出"); sys.exit()
