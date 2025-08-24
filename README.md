# InsertSoundBoardHere

Hello and welcome!

Are you in need of a program that allows you to play sigma sounds through your mic?

Do you need an escape from Discords inbuilt soundboard?

...Or maybe you just want to micspam earrape on TF2 community servers XD

WELL, I'm not here to question what your needs are lol, instead, I'm here to introduce **InsertSoundBoardHere!**

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo.png?raw=true)

InsertSoundBoardHere is a free and open-source program that I've written using Python that allows users to 
play any sound they desire through their microphone! :D

## Installation and Requirements

To install this program, simply download the release from this repository
and extract all of the folders to a directory of your choice! :D

HOWEVER, this program can't run without the skibidi support of one of the following programs below:

* **Virtual Audio Cable**
* **VB-Cable**
* **Any software which has similar functionality to the two above**

This program relies on virtual audio devices in order to deliver all audio to your chosen application.
At the time of making this first version, I know no way of implementing a virtual audio device with the use of Python, 
so instead I decided to have it utilise programs like the ones listed above for audio delivery.

Once you install the required program of your choice, you will need to create at least one virtual audio device.
This virtual audio device should act as your primary output device. Once it's created, make that your default output device.

In my case below, I have made three virtual audio device with the use of Virtual Audio Cable, and I have set one of them to
be my primary output device.

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo1.png?raw=true)

Using "pip install" is NOT required for any of the external modules and libraries powering this program
since they come bundled with the program. ;D

After that is done, there are **two** methods of running this poggers program:

* **The EXE file**

**soundBoard.exe** is basically the compiled version of **soundBoard.py**, which is the source code for the program.
This means that Python does NOT have to be installed in order for this program to run.

* **The PY file**

If however you DO have a Python interpreter or IDE installed, **soundBoard.py** file is just as capable of performing
your needs too.

With all the hard stuff out of the way, I'll now introduce the program itself! ;D

## The Sound Tab

The sound tab allows you to upload/delete sounds, and change their volume and keybind, along with other properties!

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo.png?raw=true)

This will be your first sight upon loading the program. Looks beautiful, just like Pitou from HxH ;D

NOW, to **upload** a file to the program, click on the upload button and select the sound file of your choice.

**MP3**, **WAV**, **FLAC**, and **OGG** are the only supported file formats that the program will accept.

Here's how the window will look upon successful upload:

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo2.png?raw=true)

You can still see, that the menu on the right is still greyed out, and this is by design, since no sound is currently selected.

Once you select the sound that you desire, you can change its respective settings with the menu on the right:

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo3.png?raw=true)

Here is a small yet skibidi showcase on each of the settings:

* **The Name Entrybox**

Here, you can change the name of you sound as it appears in the menu.
To change it, type in any name you want, and press Enter to save. ;D

* **The Keybind Button**

With this, you can add or remove keybinds to your specific sounds!

**Left click** the button to start listening for keys to listen to.
The window will freeze while this is happening, this is normal.

Then, type in the keys you wish to bind to your sound.
Let go of one of the keys that you're assigning to the sound to save it! ;D

Press **Esc** while the listener is running to stop listening without changing
the existing keybind of the selected sound.

**Right click** the button to clear out any existing keybind the sound has!

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo4.png?raw=true)


* **The Volume Slider**

This one is self explanatory, it changes the volume of the selected sound, both on playback and passthrough.

* **The Overlap Switch**

This makes it so that whenever the keybind for that sound activates, it will immediately start playback from the beginning.

* **The Pausable Switch**

This makes the sound remember what point it was stopped at, allowing for playback to start at that point.

* **The Loopable Switch**

This makes it so that the sound restarts playback upon reaching the end of file.

* **The Delete Button**

This commits first degree murder on the selected sound... :*(

## The Settings Tab

The settings tab allows you to change your sound devices and configure an additional keybind! :D

You may notice that there's no "Start" or "Stop" button, this is because the program runs automatically as soon as a
valid input device, output device, and sample rate into the comboboxes below:

![image_alt](https://github.com/Confectionery13/InsertSoundBoardHere/blob/main/demo5.png?raw=true)

* **The Input Device**

This combobox selects the input device. You preferrably want to use your microphone for this.

* **The Extra Device**

This combobox selects ANOTHER input device. This is completely optional, and is sort of a novelty feature to this program XD
In my case, I use another virtual audio device and have my browser be the only application that uses said audio device.
I then select said audio device as the extra device to allow direct passthrough to the output device.

This can be used for MANY cases, such as routing discord call audio to a CS2 game lol

* **The Output Device**

This combobox selects the output device. You must use the virtual audio cable you set as a default device for this.

* **The Sample Rate**

This combobox selects the sample rate. If you want to be really funny and sound like someone on Xbox, set it all the way down XD

* **The Abort Hotkey**

This keybind stops all sounds that are currently playing. It ALSO sets all paused sounds all the way back to the start of their respective files.

The button functions exactly the same way as the **sound keybinds** you saw earlier. :D

## Let me know what you think!

For whatever purpose this is used for, I hope it makes you happy! :D

Consider donating to me here if you really want: https://ko-fi.com/confectionery13

