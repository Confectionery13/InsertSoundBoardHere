import os
import numpy as np
import yaml
import customtkinter as ctk
import CTkMessagebox as ctkm
import CTkListbox as ctkl
import CTkToolTip as ctkt
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
import threading

allDevices = [device for device in sd.query_devices()]

rateList = ["SELECT!","8000", "11025", "16000", "22050", "32000", "44100", "48000", "88200", "96000", "176400", "192000", "352800", "384000"]

extensionList = ["mp3", "wav", "flac", "aiff", "ogg"]


class fastThread:
      def __init__(self, function, arguments=()):
            self.thread = threading.Thread(target=function, args=arguments)
            self.thread.daemon = True
            self.thread.start()

class slowThread:
      def __init__(self, function, arguments=()):
            self.thread = threading.Thread(target=function, args=arguments)
            self.thread.start()
            self.thread.join()

class masterContainer:
      def __init__(self, inputDev, extraDev, outputDev, sampleRate):
            self.inputDev = inputDev
            self.extraDev = extraDev
            self.outputDev = outputDev
            self.sampleRate = sampleRate

            self.inputStream = streamContainer(inputDev, outputDev, sampleRate)
            self.extraStream = streamContainer(extraDev, outputDev, sampleRate)
            self.soundList = []
            self.keyListener = keyboardContainer(configFile[0]["abortBind"])
            self.unwantedList = []

            #loads files into soundList
            for x in range (1, len(configFile)):
                  if os.path.isfile(configFile[x]["path"]):
                        self.soundList.append(soundContainer(configFile[x]["name"],
                                                            configFile[x]["path"],
                                                            configFile[x]["keybind"],
                                                            configFile[x]["volume"],
                                                            configFile[x]["overlap"],
                                                            configFile[x]["pausable"],
                                                            configFile[x]["loopable"],
                                                            obtainDeviceID(configFile[0]["outputDev"], "max_output_channels", 0)))
                        if self.soundList[len(self.soundList)-1].keybind != None:
                              self.keyListener.keybindDict[configFile[x]["keybind"]] = self.soundList[len(self.soundList)-1].hotKeyEvent
                  else:
                        self.unwantedList.append(configFile[x]["name"])

            for unwanted in self.unwantedList:
                  for y in range (1, len(configFile)):
                        try:
                              if configFile[y]["name"] == unwanted:
                                    del configFile[y]
                        except IndexError:
                              pass
            saveToYaml()
      
      #stream methods
      def configureStreams(self, inputDev, extraDev, outputDev, sampleRate):
            self.inputDev = inputDev
            self.extraDev = extraDev
            self.outputDev = outputDev
            self.sampleRate = sampleRate

            fastThread(self.inputStream.configStream, (self.inputDev,self.outputDev,self.sampleRate))
            fastThread(self.extraStream.configStream, (self.extraDev,self.outputDev,self.sampleRate))
            
            for sound in self.soundList:
                  fastThread(sound.updateDevice, (self.outputDev,))
                  
      #sound methods
      def abortAllSounds(self):
            for sound in self.soundList:
                  fastThread(sound.abortSound,())

      #keyboard methods
      def startListener(self):
            self.keyListener.startListener(self.abortAllSounds)

class keyboardContainer:
      def __init__(self, abortBind):
            self.keybindDict = {}
            self.rebindArray = []
            self.released = False
            self.abortBind = abortBind

      def startListener(self, abortCommand):
            if self.abortBind != None:
                  self.keybindDict[self.abortBind] = abortCommand
            self.keybindListener = keyboard.GlobalHotKeys(self.keybindDict)
            self.keybindListener.start()
      
      def stopListener(self):
            self.keybindListener.stop()
      
      def keybindRefresh(self):
            self.keybindDict = {}
            for x in range (len(mainContainer.soundList)):
                  if mainContainer.soundList[x].keybind != None:
                        self.keybindDict[mainContainer.soundList[x].keybind] = mainContainer.soundList[x].hotKeyEvent

      def rebindKey(self, index, abort):
            self.stopListener()
            self.released = False
            self.rebindArray = []

            self.keybindListener = keyboard.Listener(on_press=lambda key:self.pressRebind(self, key), on_release=lambda key:self.releaseRebind(self, key))
            self.keybindListener.start()

            while self.keybindListener.running:
                  if (self.released) and (len(self.rebindArray) > 0):
                        self.keybindListener.stop()

            if abort:
                  abortBindButton.configure(text="Add Keybind")
            else:
                  soundBindButton.configure(text="Add Keybind")
            
            if len(self.rebindArray) > 0:
                  stringProcess = ""
                  keybindUnique = True

                  for key in self.rebindArray:
                        if len(stringProcess) > 0:
                              stringProcess = stringProcess + "+"
                        if key == "<12>":
                              stringProcess = stringProcess + key
                        elif len(key) > 3:
                              stringProcess = stringProcess + "<" + key[4:] + ">"
                        else:
                              stringProcess = stringProcess + key[1:2]

                  if mainContainer.keyListener.abortBind == stringProcess:
                        keybindUnique = False
                        ctkm.CTkMessagebox(title="RUH ROH, RAGGY!", message="That keybind is already taken, much like Fiora :O", icon="cancel")

                  for sound in mainContainer.soundList:
                        if sound.keybind == stringProcess:
                              keybindUnique = False
                              ctkm.CTkMessagebox(title="RUH ROH, RAGGY!", message="That keybind is already taken, much like Fiora :O", icon="cancel")

                  if keybindUnique:
                        if abort:
                              self.abortBind = stringProcess
                              configFile[0]["abortBind"] = stringProcess
                        else:
                              mainContainer.soundList[index].keybind = stringProcess
                              configFile[index+1]["keybind"] = stringProcess
                        saveToYaml()

            self.keybindRefresh()
      
      def clearKey(self, index, abort):
            self.stopListener()

            if abort:
                  self.abortBind = None
                  configFile[0]["abortBind"] = None

            else:
                  mainContainer.soundList[index].keybind = None
                  configFile[index+1]["keybind"] = None

            saveToYaml()
            self.keybindRefresh()

      def pressRebind(self, O, key):
            fastThread(pressThread,(self,key))
            
      def releaseRebind(self, O, key):
            fastThread(releaseThread,(self,))

def pressThread(self, key):
      key = str(key)
      if key == "Key.esc":
            self.keybindListener.stop()
      elif str(key) not in self.rebindArray:
            self.rebindArray.append(key)

def releaseThread(self):
      self.released = True

class streamContainer:
      def __init__(self, inputDev, outputDev, sampleInsertion):
            self.active = False

            if ((inputDev < 0) or (outputDev < 0) or (sampleInsertion < 0)):
                  self.audioStream = None

            else:
                  self.audioStream = sd.Stream(device=(inputDev,outputDev), channels=2, samplerate=sampleInsertion, latency="low", blocksize=0, callback=passThrough)
                  self.audioStream.start()
                  self.active = True

      def configStream(self, inputDev, outputDev, sampleInsertion):
            if self.active == True:
                  self.audioStream.stop(ignore_errors=True)

            if ((inputDev < 0) or (outputDev < 0) or (sampleInsertion < 0)):
                  self.audioStream = None
                  self.active = False

            else:
                  self.audioStream = sd.Stream(device=(inputDev,outputDev), channels=2, samplerate=sampleInsertion, latency="low", blocksize=0, callback=passThrough)
                  self.active = True

            if self.active == True:
                  self.audioStream.start()

class soundContainer:
      def __init__(self, name, path, keybind, volume, overlap, pausable, loopable, outputDev):
            self.name = name
            self.keybind = keybind
            self.volume = volume
            self.overlap = overlap
            self.pausable = pausable
            self.loopable = loopable

            self.outputIndex = 0
            self.playbackIndex = 0

            self.data, self.fs = sf.read(path, dtype='float32')
            
            if self.data.ndim == 1:
                  self.data = np.column_stack((self.data, self.data))

            if (outputDev < 0):
                  self.outputStream = None 

            else:
                  self.outputStream = sd.OutputStream(channels=self.data.ndim,
                                                      samplerate=self.fs,
                                                      device=outputDev,
                                                      latency="low",
                                                      blocksize=0,
                                                      callback=lambda outdata, frames, time, status: outputPlayer(outdata, frames, time, status, self))
            
            self.playbackStream = sd.OutputStream(channels=self.data.ndim,
                                                samplerate=self.fs,
                                                latency="low",
                                                blocksize=0,
                                                callback=lambda outdata, frames, time, status: playbackPlayer(outdata, frames, time, status, self))

      def hotKeyEvent(self):
            if self.overlap:
                  if self.outputStream != None:
                        if self.outputStream.stopped:
                              fastThread(streamStarter,(self.outputStream,))
                              fastThread(streamStarter,(self.playbackStream,))

                        else:
                              if (self.outputIndex >= len(self.data)):

                                    slowThread(streamStopper,(self.outputStream,))
                                    slowThread(streamStopper,(self.playbackStream,))

                                    self.outputIndex = 0
                                    self.playbackIndex = self.outputIndex

                                    fastThread(streamStarter,(self.outputStream,))
                                    fastThread(streamStarter,(self.playbackStream,))
                              else:

                                    self.outputIndex = 0
                                    self.playbackIndex = self.outputIndex
                  else:
                        if self.playbackStream.stopped:
                              fastThread(streamStarter,(self.playbackStream,))

                        else:
                              if (self.playbackIndex >= len(self.data)):

                                    slowThread(streamStopper,(self.playbackStream,))
                                    self.playbackIndex = 0
                                    fastThread(streamStarter,(self.playbackStream,))
                              else:
                                    self.playbackIndex = 0

            elif self.overlap == False:
                  if self.outputStream != None:
                        if self.outputStream.stopped:

                              fastThread(streamStarter,(self.outputStream,))
                              fastThread(streamStarter,(self.playbackStream,))

                        elif (self.outputIndex > len(self.data)):

                              slowThread(streamStopper,(self.outputStream,))
                              slowThread(streamStopper,(self.playbackStream,))

                              self.outputIndex = 0
                              self.playbackIndex = 0

                              fastThread(streamStarter,(self.outputStream,))
                              fastThread(streamStarter,(self.playbackStream,))

                        else:
                              fastThread(streamStopper,(self.outputStream,))
                              fastThread(streamStopper,(self.playbackStream,))

                              self.playbackIndex = self.outputIndex
                              
                              if self.pausable == False:
                                    self.outputIndex = 0
                                    self.playbackIndex = 0

                  else:
                        if self.playbackStream.stopped:
                              fastThread(streamStarter,(self.playbackStream,))

                        elif (self.playbackIndex > len(self.data)):

                              slowThread(streamStopper,(self.playbackStream,))

                              self.playbackIndex = 0

                              fastThread(streamStarter,(self.playbackStream,))

                        else:
                              fastThread(streamStopper,(self.playbackStream,))

                              if self.pausable == False:
                                    self.playbackIndex = 0

      def abortSound(self):
            if self.outputStream != None:
                  if self.outputStream.stopped == False:
                        fastThread(streamStopper,(self.outputStream,))
                        fastThread(streamStopper,(self.playbackStream,))
                  self.outputIndex = 0
                  self.playbackIndex = 0
            else:
                  if self.playbackStream.stopped == False:
                        fastThread(streamStopper,(self.playbackStream,))
                  self.playbackIndex = 0

      def updateDevice(self, outputDev):
            if (outputDev > -1):
                  self.abortSound()
                  self.outputStream = sd.OutputStream(channels = self.data.shape[1],
                                                samplerate=self.fs,
                                                device=outputDev,
                                                latency="low",
                                                blocksize=0,
                                                callback=lambda outdata, frames, time, status: outputPlayer(outdata, frames, time, status, self))
            else:
                  self.abortSound()
                  self.outputStream = None

class comboBoxType:
        def __init__(self, targetWindow, inputWidth, inputText, inputValue):
              ctk.CTkLabel(targetWindow, text=inputText).pack(pady=1)
              self.ComboBox = ctk.CTkComboBox(targetWindow, width=inputWidth, values=inputValue, command=comboBoxChange)
              self.ComboBox.pack(pady=1)
              self.ComboBox.configure(state="readonly")

        def getComboBox(self):
              return self.ComboBox
        
        def setComboBox(self, Array):
              self.ComboBox.set("")
              self.ComboBox.configure(values=Array)

class frameType:
      def __init__(self, targetWindow, inputText, inputSide):
            self.frame = ctk.CTkFrame(targetWindow)
            self.frame.pack(fill="both", expand=True, padx=10, pady=10, side=inputSide)
            ctk.CTkLabel(self.frame, text=inputText).pack(pady=1)

def streamStarter(targetStream):
      targetStream.start()

def streamStopper(targetStream):
      targetStream.stop(ignore_errors=True)

def passThrough(indata, outdata, frames, time, status):
      outdata[:] = indata

def outputPlayer(outdata, frames, time, status, soundClass):
      try:
            outdata[:] = ((soundClass.data[soundClass.outputIndex:soundClass.outputIndex + frames])*soundClass.volume)
            soundClass.outputIndex += frames
      except ValueError:
            if soundClass.loopable:
                  soundClass.outputIndex = 0
            else:
                  soundClass.outputIndex *= 2
                  raise sd.CallbackStop

def playbackPlayer(outdata, frames, time, status, soundClass):
      try:
            outdata[:] = ((soundClass.data[soundClass.playbackIndex:soundClass.playbackIndex + frames])*soundClass.volume)
            soundClass.playbackIndex += frames
      except ValueError:
            if soundClass.loopable:
                  soundClass.playbackIndex = 0
            else:
                  soundClass.playbackIndex *= 2
                  raise sd.CallbackStop

def obtainDevices(deviceType, deviceApi):
        deviceList = []
        deviceList.append("Please select a device! ;D")
        for device in allDevices:
                if ((device[deviceType] > 0) and device["hostapi"] == deviceApi):
                    deviceList.append(device["name"])
        return deviceList

def obtainDeviceID(deviceName, deviceType, deviceApi):
      foundDevice = False
      for device in allDevices:
            if (deviceName == (device["name"]) and ((device[deviceType] > 0) and device["hostapi"] == deviceApi)):
                        foundDevice = True
                        return int(device["index"])
      if foundDevice == False:
            return -1

def comboBoxChange(event):
      configFile[0]["inputDev"] = inputSelection.getComboBox().get()
      configFile[0]["extraDev"] = extraSelection.getComboBox().get()
      configFile[0]["outputDev"] = outputSelection.getComboBox().get()
      configFile[0]["sampleRate"] = rateSelection.getComboBox().get()
      saveToYaml()

      try:
            freeSample = int(configFile[0]["sampleRate"])
      except ValueError:
            freeSample = -1

      mainContainer.configureStreams(obtainDeviceID(inputSelection.getComboBox().get(), "max_input_channels", 0),
                                     obtainDeviceID(extraSelection.getComboBox().get(), "max_input_channels", 0),
                                     obtainDeviceID(outputSelection.getComboBox().get(),"max_output_channels", 0),
                                     freeSample)

      for sound in mainContainer.soundList:
            fastThread(sound.updateDevice, (obtainDeviceID(outputSelection.getComboBox().get(),"max_output_channels", 0),))

def saveToYaml():
      with open('soundSettings.yaml', 'w') as yamlFile:
            yaml.safe_dump_all(configFile, yamlFile, sort_keys=False)

def bindListen(abortion):
      if abortion:

            itemDisabler(abortion)

            mainContainer.keyListener.rebindKey(None, abortion)
            abortBindButton.configure(text=mainContainer.keyListener.abortBind)

            itemEnabler(abortion)

      else:

            targetIndex = soundListBox.curselection()
            
            itemDisabler(abortion)
            mainContainer.keyListener.rebindKey(targetIndex, abortion)
            
            soundFiller()
            soundListBox.select(targetIndex)

      mainContainer.keyListener.startListener(mainContainer.abortAllSounds)

def bindClear(bind, abortion):
      try:
            if abortion:
                  abortBindButton.configure(text="Add Keybind")
                  mainContainer.keyListener.clearKey(-1, abortion)
            else:
                  soundBindButton.configure(text="Add Keybind")
                  mainContainer.keyListener.clearKey(soundListBox.curselection(), abortion)
            mainContainer.keyListener.startListener(mainContainer.abortAllSounds)
      except TypeError:
            pass

def soundFiller():
      for x in range (0, len(mainContainer.soundList)):
            soundListBox.insert(x, mainContainer.soundList[x].name)

def createSound():
      targetFile = ctk.filedialog.askopenfilename()

      if targetFile:
            fileName, fileExtension = os.path.basename(targetFile).rsplit('.', 1)
            if fileExtension.lower() in extensionList:
                  newSound = soundContainer(fileName, targetFile, None, 1, False, False, False, mainContainer.outputDev)
                  mainContainer.soundList.append(newSound)
                  configFile.append({"name": fileName,
                                     "path": targetFile,
                                     "keybind": None,
                                     "volume": 1,
                                     "overlap": False,
                                     "pausable": False,
                                     "loopable": False})
                  soundFiller()
                  saveToYaml()
            else:
                  ctkm.CTkMessagebox(title="Uhh... Mr. White?", message="Only MP3, WAV, FLAC, OGG, and AIFF files are supported ;D", icon="cancel")

def deleteSound():
      youSURE = ctkm.CTkMessagebox(title="YOU SURE???", message="Do you want to delete this sound? \nJUST SAYING, if you click Yes, you're a murderer ;O",
                        icon="question", option_1="No.... murder is wrong! :D", option_2="YES!!1 NO MERCY!!!1 >:)")
      if youSURE.get() == "YES!!1 NO MERCY!!!1 >:)":

            if mainContainer.soundList[soundListBox.curselection()].outputStream != None:
                  mainContainer.soundList[soundListBox.curselection()].outputStream.stop(ignore_errors=True)
                  mainContainer.soundList[soundListBox.curselection()].outputStream.close()
            mainContainer.soundList[soundListBox.curselection()].playbackStream.stop(ignore_errors=True)
            mainContainer.soundList[soundListBox.curselection()].playbackStream.close()

            soundBindButton.configure(text="Add Keybind")
            mainContainer.keyListener.clearKey(soundListBox.curselection(), False)

            mainContainer.soundList.pop(soundListBox.curselection())
            configFile.pop(soundListBox.curselection()+1)
            soundSettingsName.delete(0,ctk.END)
            soundVolumeSlider.set(0)
            overlapSwitch.deselect()
            pausableSwitch.deselect() 
            loopableSwitch.deselect() 
            itemDisabler(False)
            saveToYaml()
            mainContainer.keyListener.startListener(mainContainer.abortAllSounds)
            soundFiller()
      soundVolumeTip.configure(message=0)

def itemEnabler(abortion):
      if abortion:
            inputSelection.ComboBox.configure(state="readonly")
            extraSelection.ComboBox.configure(state="readonly")
            outputSelection.ComboBox.configure(state="readonly")
            rateSelection.ComboBox.configure(state="readonly")

      else:
            uploadButton.configure(state="normal")
            soundSettingsName.configure(state="normal")
            soundVolumeSlider.configure(state="normal")
            overlapSwitch.configure(state="normal")
            pausableSwitch.configure(state="normal")
            loopableSwitch.configure(state="normal")
            deleteButton.configure(state="normal")
        
def itemDisabler(abortion):
      if abortion:
            inputSelection.ComboBox.configure(state="disabled")
            extraSelection.ComboBox.configure(state="disabled")
            outputSelection.ComboBox.configure(state="disabled")
            rateSelection.ComboBox.configure(state="disabled")

      else:
            soundBindButton.configure(state="disabled")
            soundListBox.delete("all")
            soundSettingsName.configure(state="disabled")
            soundVolumeSlider.configure(state="disabled")
            overlapSwitch.configure(state="disabled")
            pausableSwitch.configure(state="disabled")
            loopableSwitch.configure(state="disabled")
            deleteButton.configure(state="disabled")

def listSelection(listBox):

      itemEnabler(False)

      soundBindButton.configure(state="normal")

      soundSettingsName.delete(0, ctk.END)
      soundSettingsName.insert(0,mainContainer.soundList[soundListBox.curselection()].name)
      
      soundVolumeSlider.set(mainContainer.soundList[soundListBox.curselection()].volume)

      if mainContainer.soundList[soundListBox.curselection()].keybind == None:
            soundBindButton.configure(text="Add Keybind")
      else:
            soundBindButton.configure(text=mainContainer.soundList[soundListBox.curselection()].keybind)
      
      if (mainContainer.soundList[soundListBox.curselection()].overlap):
            overlapSwitch.select()
            pausableSwitch.deselect() 
            loopableSwitch.deselect() 
            pausableSwitch.configure(state="disabled")
            loopableSwitch.configure(state="disabled")
      else:
           overlapSwitch.deselect() 
           pausableSwitch.configure(state="normal")
           loopableSwitch.configure(state="normal")

           if (mainContainer.soundList[soundListBox.curselection()].pausable):
                 pausableSwitch.select()
           else:
                pausableSwitch.deselect() 

           if (mainContainer.soundList[soundListBox.curselection()].loopable):
                 loopableSwitch.select()
           else:
                 loopableSwitch.deselect()
      soundVolumeTip.configure(message=int((mainContainer.soundList[soundListBox.curselection()].volume)*100))
                 
def switchSelection():
      if (overlapVar.get() == 1):

            pausableSwitch.deselect() 
            loopableSwitch.deselect() 
            pausableSwitch.configure(state="disabled")
            loopableSwitch.configure(state="disabled")

            mainContainer.soundList[soundListBox.curselection()].overlap = True
            mainContainer.soundList[soundListBox.curselection()].pausable = False
            mainContainer.soundList[soundListBox.curselection()].loopable = False

            configFile[soundListBox.curselection()+1]["overlap"] = True
            configFile[soundListBox.curselection()+1]["pausable"] = False
            configFile[soundListBox.curselection()+1]["loopable"] = False

            saveToYaml()

      else:
           
           pausableSwitch.configure(state="normal")
           loopableSwitch.configure(state="normal")
           
           mainContainer.soundList[soundListBox.curselection()].overlap = False
           configFile[soundListBox.curselection()+1]["overlap"] = False
           
           if (pausableVar.get() == 1):
                 mainContainer.soundList[soundListBox.curselection()].pausable = True
                 configFile[soundListBox.curselection()+1]["pausable"] = True
                 saveToYaml()
           else:
                 mainContainer.soundList[soundListBox.curselection()].pausable = False
                 configFile[soundListBox.curselection()+1]["pausable"] = False
                 saveToYaml()

           if (loopableVar.get() == 1):
                 mainContainer.soundList[soundListBox.curselection()].loopable = True
                 configFile[soundListBox.curselection()+1]["loopable"] = True
                 saveToYaml()
           else:
                 mainContainer.soundList[soundListBox.curselection()].loopable = False
                 configFile[soundListBox.curselection()+1]["loopable"] = False
                 saveToYaml()

def volumeUpdate(slider):
      mainContainer.soundList[soundListBox.curselection()].volume = slider
      configFile[soundListBox.curselection()+1]["volume"] = slider
      soundVolumeTip.configure(message=int(slider*100))
      saveToYaml()

def nameUpdate(text):
      index = soundListBox.curselection()
      mainContainer.soundList[index].name = soundSettingsName.get()
      configFile[index+1]["name"] = soundSettingsName.get()
      
      soundListBox.delete("all")
      soundFiller()
      soundListBox.select(index)
      saveToYaml()

#load existing presets from yaml
if os.path.isfile("soundSettings.yaml"):
      with open('soundSettings.yaml', 'r') as yamlFile:
            configFile = list(yaml.safe_load_all(yamlFile))
      freeSample = None

      try:
            freeSample = int(configFile[0]["sampleRate"])
      except ValueError:
            freeSample = -1
            
      mainContainer = masterContainer(obtainDeviceID(configFile[0]["inputDev"], "max_input_channels", 0),
                                      obtainDeviceID(configFile[0]["extraDev"], "max_input_channels", 0),
                                      obtainDeviceID(configFile[0]["outputDev"], "max_output_channels", 0),
                                      freeSample)

#create a new yaml file if none exists
else:
     configFile = [{'inputDev': "Please select a device! ;D",
                     'extraDev': 'Please select a device! ;D',
                       'outputDev': 'Please select a device! ;D',
                         'sampleRate': 'SELECT!',
                         'abortBind': None}] 
     mainContainer = masterContainer(-1, -1, -1, -1)

mainContainer.keyListener.startListener(mainContainer.abortAllSounds)

saveToYaml()

#the main window
mainWindow = ctk.CTk()
mainWindow.title("InsertSoundBoardHere")
mainWindow.geometry("600x400")

tabContainer = ctk.CTkTabview(master=mainWindow)
tabContainer.pack(expand=1, fill="both")

soundBoardTab = tabContainer.add("Sounds")
settingsTab = tabContainer.add("Settings")

# #the soundboard tab

#sound list frame
soundListFrame = frameType(soundBoardTab, "Sound List", ctk.LEFT)
soundListBox = ctkl.CTkListbox(soundListFrame.frame)
soundListBox.pack(fill="both", expand=True, padx=1, pady=1, side=ctk.TOP)
soundListBox.bind("<<ListboxSelect>>", listSelection)

#upload button
uploadButton = ctk.CTkButton(soundListFrame.frame, text="Upload", command=createSound)
uploadButton.pack(pady=10, side=ctk.TOP)
ctkt.CTkToolTip(uploadButton, delay=0.25, message="Upload a brand new sound... :D")

#sound settings frame
soundSettingsFrame = frameType(soundBoardTab, "Sound Settings", ctk.RIGHT)

#sound name editor
soundSettingsName = ctk.CTkEntry(soundSettingsFrame.frame, state="disabled")
soundSettingsName.pack(pady=1, fill="both")
soundSettingsName.bind("<Return>", nameUpdate)
ctkt.CTkToolTip(soundSettingsName, delay=0.25, message="Type in a name for your beloved sound! ;D\nPress 'Enter' to apply the changes made!")

#sound keybind button
soundBindButton = ctk.CTkButton(soundSettingsFrame.frame, text="Add Keybind", command=lambda:bindListen(False), state="disabled")
soundBindButton.pack(fill=ctk.X, expand=True, pady=1)
soundBindButton.bind("<Button-3>", lambda bind: bindClear(bind, False))
ctkt.CTkToolTip(soundBindButton, delay=0.25, message="Left Click to listen for keybinds!\nPress 'Esc' while listening to cancel!\nRight Click to clear its existing keybind!")
#sound volume slider

ctk.CTkLabel(soundSettingsFrame.frame, text="Volume").pack(pady=1)
soundVolumeSlider = ctk.CTkSlider(soundSettingsFrame.frame, from_=0, to=1, command=volumeUpdate, state="disabled")
soundVolumeSlider.pack(fill=ctk.X, expand=True, pady=1)
soundVolumeSlider.set(0)
soundVolumeTip = ctkt.CTkToolTip(soundVolumeSlider, delay=0.25, message=0)

#overlap switch
overlapVar = ctk.IntVar(value=0)
overlapSwitch = ctk.CTkSwitch(soundSettingsFrame.frame, text="Overlap", command=switchSelection, variable= overlapVar, offvalue=0, onvalue=1, state="disabled")
overlapSwitch.pack(fill=ctk.X, expand=True, pady=1)
ctkt.CTkToolTip(overlapSwitch, delay=0.25, message="Allows the sound to be played back IMMEDIATELY! :D")
#pausable switch
pausableVar = ctk.IntVar(value=0)
pausableSwitch = ctk.CTkSwitch(soundSettingsFrame.frame, text="Pausable", command=switchSelection, variable= pausableVar, offvalue=0, onvalue=1, state="disabled")
pausableSwitch.pack(fill=ctk.X, expand=True, pady=1)
ctkt.CTkToolTip(pausableSwitch, delay=0.25, message="Allows the sound to remember the point where it stopped! :D")
#loop switch
loopableVar = ctk.IntVar(value=0)
loopableSwitch = ctk.CTkSwitch(soundSettingsFrame.frame, text="Loopable", command=switchSelection, variable= loopableVar, offvalue=0, onvalue=1, state="disabled")
loopableSwitch.pack(fill=ctk.X, expand=True, pady=1)
ctkt.CTkToolTip(loopableSwitch, delay=0.25, message="Allows the sound to INSTANTLY start playback once finished! :D")
#sound delete button

deleteButton = ctk.CTkButton(soundSettingsFrame.frame, text="Delete", command=deleteSound,state="disabled")
deleteButton.pack(pady=10, side=ctk.TOP)
ctkt.CTkToolTip(deleteButton, delay=0.25, message="Delete the currently selected sound... :*(")

# #the settings tab

#comboboxes for the devices
inputSelection = comboBoxType(settingsTab, 225,"Input Device (Mandatory)", obtainDevices("max_input_channels", 0))
extraSelection = comboBoxType(settingsTab, 225,"Extra Device (Optional)", obtainDevices("max_input_channels", 0))
outputSelection = comboBoxType(settingsTab, 225,"Output Device (Mandatory)", obtainDevices("max_output_channels", 0))
rateSelection = comboBoxType(settingsTab, 100,"Sample Rate (Mandatory)", rateList)
inputSelection.ComboBox.set(configFile[0].get("inputDev"))
extraSelection.ComboBox.set(configFile[0].get("extraDev"))
outputSelection.ComboBox.set(configFile[0].get("outputDev"))
rateSelection.ComboBox.set(configFile[0].get("sampleRate"))

ctk.CTkLabel(settingsTab, text="Sound Abortion Hotkey").pack(pady=1)
abortBindButton = ctk.CTkButton(settingsTab, text="Add Keybind", command=lambda:bindListen(True))
abortBindButton.pack(padx=1, pady=1)
abortBindButton.bind("<Button-3>", lambda bind: bindClear(bind, True))
if mainContainer.keyListener.abortBind != None:
      abortBindButton.configure(text=mainContainer.keyListener.abortBind)
ctkt.CTkToolTip(abortBindButton, delay=0.25, message="Left Click to listen for keybinds!\nPress 'Esc' while listening to cancel!\nRight Click to clear its existing keybind!")

soundFiller()

mainWindow.mainloop()

