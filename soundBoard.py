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
import time

allDevices = [device for device in sd.query_devices()]

allHostApis = [api["name"] for api in sd.query_hostapis()]

rateList = ["SELECT!","8000", "11025", "16000", "22050", "32000", "44100", "48000", "88200", "96000", "176400", "192000"]

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
      def __init__(self, inputDev, extraDev, playbackDev, outputDev, sampleRate):
            self.inputStream = streamContainer(inputDev, outputDev, sampleRate)
            self.extraStream = streamContainer(extraDev, outputDev, sampleRate)
            
            self.keyListener = keyboardContainer(configFile[0]["abortBind"])

            self.soundList = []
            self.unwantedList = []

            #loads files into soundList
            for x in range (0, len(containerFile)):
                  if os.path.isfile(containerFile[x]["path"]):
                        self.soundList.append(soundContainer(containerFile[x]["name"],
                                                            containerFile[x]["path"],
                                                            containerFile[x]["keybind"],
                                                            containerFile[x]["volume"],
                                                            containerFile[x]["overlap"],
                                                            containerFile[x]["pausable"],
                                                            containerFile[x]["loopable"],
                                                            playbackDev))
                        if self.soundList[x].keybind != None:
                              self.keyListener.keybindDict[containerFile[x]["keybind"]] = self.soundList[x].hotKeyEvent
                  else:
                        self.unwantedList.append(containerFile[x]["name"])

            for unwanted in self.unwantedList:
                  for y in range (0, len(containerFile)):
                        if containerFile[y]["name"] == unwanted:
                              del containerFile[y]

            saveToContainer()
      
      #stream methods
      def configureStreams(self, inputDev, extraDev, playbackDev, outputDev, sampleRate):
            fastThread(self.inputStream.configStream, (inputDev, outputDev, sampleRate))
            fastThread(self.extraStream.configStream, (extraDev, outputDev, sampleRate))
            
            for sound in self.soundList:
                  fastThread(sound.updateDevice, (playbackDev,))
                  
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

            keybindTimeout = time.time()

            while ((self.keybindListener.running) and (time.time() - keybindTimeout < 5)):
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
                        ctkm.CTkMessagebox(title="RUH ROH, RAGGY!", message="That keybind is already taken :O", icon="cancel")

                  for sound in mainContainer.soundList:
                        if sound.keybind == stringProcess:
                              keybindUnique = False
                              ctkm.CTkMessagebox(title="RUH ROH, RAGGY!", message="That keybind is already taken :O", icon="cancel")

                  if keybindUnique:
                        if abort:
                              self.abortBind = stringProcess
                              configFile[0]["abortBind"] = stringProcess
                              saveToConfig()
                        else:
                              mainContainer.soundList[index].keybind = stringProcess
                              containerFile[index]["keybind"] = stringProcess
                              saveToContainer()

            self.keybindRefresh()
      
      def clearKey(self, index, abort):
            self.stopListener()

            if abort:
                  self.abortBind = None
                  configFile[0]["abortBind"] = None
                  saveToConfig()
            else:
                  mainContainer.soundList[index].keybind = None
                  containerFile[index]["keybind"] = None
                  saveToContainer()

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
                  if obtainDeviceHostApi(inputDev) == "Windows WASAPI":
                        self.audioStream = sd.Stream(device=(inputDev,outputDev), channels=2, extra_settings=(sd.WasapiSettings(auto_convert=True)), samplerate=sampleInsertion, latency="low", blocksize=0, callback=passThrough)
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
                  if obtainDeviceHostApi(inputDev) == "Windows WASAPI":
                        self.audioStream = sd.Stream(device=(inputDev,outputDev), channels=2, extra_settings=(sd.WasapiSettings(auto_convert=True)), samplerate=sampleInsertion, latency="low", blocksize=0, callback=passThrough)
                  else:
                        self.audioStream = sd.Stream(device=(inputDev,outputDev), channels=2, samplerate=sampleInsertion, latency="low", blocksize=0, callback=passThrough)
                  self.active = True

            if self.active == True:
                  self.audioStream.start()

class soundContainer:
      def __init__(self, name, path, keybind, volume, overlap, pausable, loopable, playbackDev):
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

            if (playbackDev < 0):
                  self.outputStream = None 

            else:
                  self.outputStream = sd.OutputStream(channels=self.data.ndim,
                                                      samplerate=self.fs,
                                                      device=playbackDev,
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

      def updateDevice(self, playbackDev):
            if (playbackDev > -1):
                  self.abortSound()
                  self.outputStream = sd.OutputStream(channels = self.data.ndim,
                                                samplerate=self.fs,
                                                device=playbackDev,
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
            self.frame.pack(fill="both", expand=True, padx=5, pady=5, side=inputSide)
            ctk.CTkLabel(self.frame, text=inputText, font=("TkDefaultFont", 18, "bold")).pack(pady=1)

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

def obtainHostApiList():
      hostApiList = ["Select an API! ;D"]
      for api in sd.query_hostapis():
            hostApiList.append(api['name'])
      
      if "Windows WDM-KS" in hostApiList:
            hostApiList.remove("Windows WDM-KS")
      return hostApiList

def obtainPlayBackDevice(targetApi):
      for hostApi in sd.query_hostapis():
            if hostApi['name'] == targetApi:
                  return (int(hostApi['default_output_device']))

def obtainDeviceHostApi(deviceIndex):
      return allHostApis[allDevices[deviceIndex]["hostapi"]]

def obtainDeviceList(deviceType, deviceApi):
        deviceList = ["Please select a device! ;D"]
        if deviceApi == None:
              deviceApi = "MME"
        for device in allDevices:
                if ((device[deviceType] > 0) and allHostApis[device["hostapi"]] == deviceApi):
                    deviceList.append(device["name"])
        return deviceList

def obtainDeviceID(deviceName, deviceType, deviceApi):
      foundDevice = False
      if deviceApi == None:
              deviceApi = "MME"
      for device in allDevices:
            if (deviceName == (device["name"]) and ((device[deviceType] > 0) and allHostApis[device["hostapi"]] == deviceApi)):
                        foundDevice = True
                        return int(device["index"])
      if foundDevice == False:
            return -1

def comboBoxChange(event):

      configFile[0]["sampleRate"] = rateSelection.getComboBox().get()

      try:
            freeSample = int(configFile[0]["sampleRate"])
      except ValueError:
            freeSample = -1

      if apiSelection.getComboBox().get() != configFile[0]["hostApi"]:

            configFile[0]["hostApi"] = apiSelection.getComboBox().get()
            configFile[0]["inputDev"] = "Please select a device! ;D"
            configFile[0]["extraDev"] = "Please select a device! ;D"
            configFile[0]["outputDev"] = "Please select a device! ;D"

            inputSelection.setComboBox(obtainDeviceList("max_input_channels", configFile[0].get("hostApi")))
            extraSelection.setComboBox(obtainDeviceList("max_input_channels", configFile[0].get("hostApi")))
            outputSelection.setComboBox(obtainDeviceList("max_output_channels", configFile[0].get("hostApi")))

            inputSelection.ComboBox.set("Please select a device! ;D")
            extraSelection.ComboBox.set("Please select a device! ;D")
            outputSelection.ComboBox.set("Please select a device! ;D")

            mainContainer.configureStreams(-1, -1, obtainDeviceID(configFile[0]["playbackDev"], "max_output_channels", None), -1, freeSample)
      
      else:
            configFile[0]["inputDev"] = inputSelection.getComboBox().get()
            configFile[0]["extraDev"] = extraSelection.getComboBox().get()
            configFile[0]["playbackDev"] = playbackSelection.getComboBox().get()
            configFile[0]["outputDev"] = outputSelection.getComboBox().get()

            mainContainer.configureStreams(obtainDeviceID(configFile[0]["inputDev"], "max_input_channels", configFile[0].get("hostApi")),
                                      obtainDeviceID(configFile[0]["extraDev"], "max_input_channels", configFile[0].get("hostApi")),
                                      obtainDeviceID(configFile[0]["playbackDev"], "max_output_channels", None),
                                      obtainDeviceID(configFile[0]["outputDev"], "max_output_channels", configFile[0].get("hostApi")),
                                      freeSample)
                                     
      for sound in mainContainer.soundList:
            fastThread(sound.updateDevice, (obtainDeviceID(playbackSelection.getComboBox().get(),"max_output_channels", None),))
      
      saveToConfig()
      fastThread(checkStatus,())

def saveToConfig():
      with open('configSettings.yaml', 'w') as yamlFile:
            yaml.safe_dump_all(configFile, yamlFile, sort_keys=False)

def saveToContainer():
      with open('containerSettings.yaml', 'w') as yamlFile:
            yaml.safe_dump_all(containerFile, yamlFile, sort_keys=False)

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
                  newSound = soundContainer(fileName, targetFile, None, 1, False, False, False, obtainDeviceID(playbackSelection.getComboBox().get(),"max_output_channels", None))
                  mainContainer.soundList.append(newSound)
                  containerFile.append({"name": fileName,
                                     "path": targetFile,
                                     "keybind": None,
                                     "volume": 1,
                                     "overlap": False,
                                     "pausable": False,
                                     "loopable": False})
                  soundFiller()
                  saveToContainer()
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
            containerFile.pop(soundListBox.curselection())
            soundSettingsName.delete(0,ctk.END)
            soundVolumeSlider.set(0)

            overlapSwitch.deselect()
            pausableSwitch.deselect() 
            loopableSwitch.deselect() 
            
            itemDisabler(False)
            saveToContainer()
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

            containerFile[soundListBox.curselection()]["overlap"] = True
            containerFile[soundListBox.curselection()]["pausable"] = False
            containerFile[soundListBox.curselection()]["loopable"] = False

      else:
           
            pausableSwitch.configure(state="normal")
            loopableSwitch.configure(state="normal")
           
            mainContainer.soundList[soundListBox.curselection()].overlap = False
            containerFile[soundListBox.curselection()]["overlap"] = False
           
            if (pausableVar.get() == 1):
                 mainContainer.soundList[soundListBox.curselection()].pausable = True
                 containerFile[soundListBox.curselection()]["pausable"] = True

            else:
                 mainContainer.soundList[soundListBox.curselection()].pausable = False
                 containerFile[soundListBox.curselection()]["pausable"] = False

            if (loopableVar.get() == 1):
                 mainContainer.soundList[soundListBox.curselection()].loopable = True
                 containerFile[soundListBox.curselection()]["loopable"] = True

            else:
                 mainContainer.soundList[soundListBox.curselection()].loopable = False
                 containerFile[soundListBox.curselection()]["loopable"] = False
      
      saveToContainer()

def volumeUpdate(slider):
      mainContainer.soundList[soundListBox.curselection()].volume = slider
      containerFile[soundListBox.curselection()]["volume"] = slider
      soundVolumeTip.configure(message=int(slider*100))
      saveToContainer()

def nameUpdate(text):
      index = soundListBox.curselection()
      mainContainer.soundList[index].name = soundSettingsName.get()
      containerFile[index]["name"] = soundSettingsName.get()
      
      soundListBox.delete("all")
      soundFiller()
      soundListBox.select(index)
      saveToContainer()

def checkStatus():
      time.sleep(0.2)

      if mainContainer.inputStream.audioStream != None:
            status1.configure(fg_color="#00FF00", text_color_disabled="black")
      else:
            status1.configure(fg_color="#FF0000", text_color_disabled="white")

      if mainContainer.extraStream.audioStream != None:
            status2.configure(fg_color="#00FF00", text_color_disabled="black")
      else:
            status2.configure(fg_color="#FF0000", text_color_disabled="white")

      try:
            if mainContainer.soundList[0].outputStream != None:
                  status3.configure(fg_color="#00FF00", text_color_disabled="black")
            else:
                  status3.configure(fg_color="#FF0000", text_color_disabled="white")
      except IndexError:
            status3.configure(fg_color="#FF0000", text_color_disabled="white")

#load existing presets from sound container yaml
if os.path.isfile("containerSettings.yaml"):
      with open('containerSettings.yaml', 'r') as yamlFileB:
            containerFile = list(yaml.safe_load_all(yamlFileB))
            
else:
      containerFile = []

saveToContainer()

#load existing presets from config yaml
if os.path.isfile("configSettings.yaml"):

      with open('configSettings.yaml', 'r') as yamlFileA:
            configFile = list(yaml.safe_load_all(yamlFileA))

      freeSample = None

      try:
            freeSample = int(configFile[0]["sampleRate"])
      except ValueError:
            freeSample = -1
            
      mainContainer = masterContainer(obtainDeviceID(configFile[0]["inputDev"], "max_input_channels", configFile[0].get("hostApi")),
                                      obtainDeviceID(configFile[0]["extraDev"], "max_input_channels", configFile[0].get("hostApi")),
                                      obtainDeviceID(configFile[0]["playbackDev"], "max_output_channels", None),
                                      obtainDeviceID(configFile[0]["outputDev"], "max_output_channels", configFile[0].get("hostApi")),
                                      freeSample)

#create a new config yaml file if none exists
else:
     configFile = [{'hostApi': "Select an API! ;D",
                     'inputDev': "Please select a device! ;D",
                      'extraDev': 'Please select a device! ;D',
                      'playbackDev': 'Please select a device! ;D',
                        'outputDev': 'Please select a device! ;D',
                         'sampleRate': 'SELECT!',
                          'abortBind': None}] 
     mainContainer = masterContainer(-1, -1, -1, -1, -1)

mainContainer.keyListener.startListener(mainContainer.abortAllSounds)

saveToConfig()

#the main window
mainWindow = ctk.CTk()
mainWindow.title("InsertSoundBoardHere")
mainWindow.geometry("650x600")

masterFrame = frameType(mainWindow, "InsertSoundBoardHere", ctk.TOP)

tabContainer = ctk.CTkTabview(master=masterFrame.frame)
tabContainer.pack(fill="both")

soundBoardTab = tabContainer.add("Soundboard")
settingsTab = tabContainer.add("Settings")

# #the soundboard tab
soundListFrame = frameType(soundBoardTab, "Sound List", ctk.LEFT)
soundSettingsFrame = frameType(soundBoardTab, "Sound Settings", ctk.RIGHT)

#sound list frame
soundListBox = ctkl.CTkListbox(soundListFrame.frame, height=232)
soundListBox.pack(fill="both", expand=True, padx=1, pady=1, side=ctk.TOP)
soundListBox.bind("<<ListboxSelect>>", listSelection)

#upload button
uploadButton = ctk.CTkButton(soundListFrame.frame, text="Upload", command=createSound)
uploadButton.pack(pady=10, side=ctk.TOP)
ctkt.CTkToolTip(uploadButton, delay=0.25, message="Upload a brand new sound... :D")

#sound name editor
soundSettingsName = ctk.CTkEntry(soundSettingsFrame.frame, state="disabled")
soundSettingsName.pack(pady=1, fill="both")
soundSettingsName.bind("<Return>", nameUpdate)
ctkt.CTkToolTip(soundSettingsName, delay=0.25, message="Type in a name for your beloved sound! ;D\nPress 'Enter' to apply the changes made!")

#sound keybind button
soundBindButton = ctk.CTkButton(soundSettingsFrame.frame, text="Add Keybind", command=lambda:bindListen(False), state="disabled")
soundBindButton.pack(fill=ctk.X, expand=True, pady=1)
soundBindButton.bind("<Button-3>", lambda bind: bindClear(bind, False))
ctkt.CTkToolTip(soundBindButton, delay=0.25, message="Left Click to listen for a new keybind!\nWill listen for 5 seconds before stopping!\nPress 'Esc' while listening to cancel!\nRight Click to clear its existing keybind!")

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
deviceFrame1 = frameType(settingsTab, "Stream Settings", ctk.LEFT)
deviceFrame2 = frameType(settingsTab, "Soundboard Settings", ctk.RIGHT)

#comboboxes for the devices
apiSelection = comboBoxType(deviceFrame1.frame, 175,"Sound API (Mandatory)", obtainHostApiList())
inputSelection = comboBoxType(deviceFrame1.frame, 225,"Input Device (Mandatory)", obtainDeviceList("max_input_channels", configFile[0].get("hostApi")))
extraSelection = comboBoxType(deviceFrame1.frame, 225,"Extra Device (Optional)", obtainDeviceList("max_input_channels", configFile[0].get("hostApi")))
outputSelection = comboBoxType(deviceFrame1.frame, 225,"Output Device (Mandatory)", obtainDeviceList("max_output_channels", configFile[0].get("hostApi")))
rateSelection = comboBoxType(deviceFrame1.frame, 100,"Sample Rate (Mandatory)", rateList)

apiSelection.ComboBox.set(configFile[0].get("hostApi"))
inputSelection.ComboBox.set(configFile[0].get("inputDev"))
extraSelection.ComboBox.set(configFile[0].get("extraDev"))
outputSelection.ComboBox.set(configFile[0].get("outputDev"))
rateSelection.ComboBox.set(configFile[0].get("sampleRate"))

playbackSelection = comboBoxType(deviceFrame2.frame, 225,"Soundboard Device (Mandatory)", obtainDeviceList("max_output_channels", None))
playbackSelection.ComboBox.set(configFile[0].get("playbackDev"))

#sound abortion hotkey
ctk.CTkLabel(deviceFrame2.frame, text="Sound Stopper Hotkey (Optional)").pack(pady=1)
abortBindButton = ctk.CTkButton(deviceFrame2.frame, text="Add Keybind", command=lambda:bindListen(True))
abortBindButton.pack(padx=1, pady=1)
abortBindButton.bind("<Button-3>", lambda bind: bindClear(bind, True))

if mainContainer.keyListener.abortBind != None:
      abortBindButton.configure(text=mainContainer.keyListener.abortBind)
ctkt.CTkToolTip(abortBindButton, delay=0.25, message="Left Click to listen for a new keybind!\nWill listen for 5 seconds before stopping!\nPress 'Esc' while listening to cancel!\nRight Click to clear its existing keybind!")


ctk.CTkLabel(deviceFrame2.frame, text="About this program:\nInsertSoundBoardHere v1.1\nWritten by Confectionery").pack(pady=10)

statusFrame = frameType(mainWindow, "Program Status", ctk.BOTTOM)

status1 = ctk.CTkButton(statusFrame.frame, text="Main Stream Status", state="disabled", fg_color="#FF0000", text_color_disabled="black", font=("TkDefaultFont", 12, "bold"))
status1.pack(pady=5, side=ctk.TOP)
ctkt.CTkToolTip(status1, delay=0.25, message="RED means the main stream is inactive!\nGREEN means the main stream is active!")

status2 = ctk.CTkButton(statusFrame.frame, text="Extra Stream Status", state="disabled", fg_color="#FF0000", text_color_disabled="black", font=("TkDefaultFont", 12, "bold"))
status2.pack(pady=5, side=ctk.TOP)
ctkt.CTkToolTip(status2, delay=0.25, message="RED means the extra stream is inactive!\nGREEN means the extra stream is active!")

status3 = ctk.CTkButton(statusFrame.frame, text="Soundboard Status", state="disabled", fg_color="#FF0000", text_color_disabled="black", font=("TkDefaultFont", 12, "bold"))
status3.pack(pady=5, side=ctk.TOP)
ctkt.CTkToolTip(status3, delay=0.25, message="RED means the soundboard is inactive!\nGREEN means the soundboard is active!")

soundFiller()
fastThread(checkStatus,())

mainWindow.mainloop()