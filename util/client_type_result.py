from config import ClientConfig as Config
# 替换 keyboard 库为 pynput（核心修改）
from pynput import keyboard as pynput_keyboard
import pyclip
import platform
import asyncio


async def type_result(text):
    # 模拟粘贴（原逻辑不变）
    if Config.paste:
        # 保存剪切板原有内容（原逻辑不变）
        try:
            temp = pyclip.paste().decode('utf-8')
        except:
            temp = ''

        # 复制识别结果到剪贴板（原逻辑不变）
        pyclip.copy(text)

        # 粘贴结果（替换 keyboard 为 pynput，行为完全一致）
        keyboard = pynput_keyboard.Controller()
        if platform.system() == 'Darwin':  # Mac 系统（原 keycode 55=Cmd，9=V）
            # 原逻辑：keyboard.press(55) → 左 Cmd 键
            keyboard.press(pynput_keyboard.Key.cmd_l)
            # 原逻辑：keyboard.press(9) → V 键
            keyboard.press('v')
            # 原逻辑：释放顺序不变
            keyboard.release('v')
            keyboard.release(pynput_keyboard.Key.cmd_l)
        else:  # Windows/Linux 系统（原逻辑：keyboard.send('ctrl + v')）
            # 模拟 Ctrl+V 组合键（pynput 标准写法，和原行为一致）
            with keyboard.pressed(pynput_keyboard.Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')

        # 还原剪贴板（原逻辑不变）
        if Config.restore_clip:
            await asyncio.sleep(0.1)
            pyclip.copy(temp)

    # 模拟直接输入（原逻辑不变）
    else:
        # 原逻辑：keyboard.write(text) → 替换为 pynput 的 type 方法（功能完全一致）
        keyboard = pynput_keyboard.Controller()
        keyboard.type(text)
