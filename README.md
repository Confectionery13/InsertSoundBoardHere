Hello!

This video below demonstrates the functionality of the program on this repository:
https://youtu.be/TPlZZJuxMwg

IF you're going to download soundBoard.py instead of soundBoard.exe, be sure to run these commands in CMD/Powershell:

"pip install numpy"
"pip install yaml"
"pip install customtkinter"
"pip install CTkMessagebox"
"pip install CTkListbox"
"pip install CtkToolTip"
"pip install sounddevice"
"pip install soundfile"
"pip install pynput"

ALSO, wherever pynput is installed, go to "(Wherever your python libraries are)\pynput\keyboard\_win32.py"

and then append the following code inside class Key(enum.Enum):
    numpad0 = KeyCode.from_vk(VK.NUMPAD0)
    numpad1 = KeyCode.from_vk(VK.NUMPAD1)
    numpad2 = KeyCode.from_vk(VK.NUMPAD2)
    numpad3 = KeyCode.from_vk(VK.NUMPAD3)
    numpad4 = KeyCode.from_vk(VK.NUMPAD4)
    numpad5 = KeyCode.from_vk(VK.NUMPAD5)
    numpad6 = KeyCode.from_vk(VK.NUMPAD6)
    numpad7 = KeyCode.from_vk(VK.NUMPAD7)
    numpad8 = KeyCode.from_vk(VK.NUMPAD8)
    numpad9 = KeyCode.from_vk(VK.NUMPAD9)
    multiply = KeyCode.from_vk(VK.MULTIPLY)
    add = KeyCode.from_vk(VK.ADD)
    separator = KeyCode.from_vk(VK.SEPARATOR)
    subtract = KeyCode.from_vk(VK.SUBTRACT)
    decimal = KeyCode.from_vk(VK.DECIMAL)
    divide = KeyCode.from_vk(VK.DIVIDE)

If this is not done, then the program will not be able to bind keys to the numpad.

That aside, enjoy the program to the fullest!

Let me know if there's anything I need to fix!
