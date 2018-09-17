from m5stack import *
from retroPCCG import RetroPCCG
import gc
import uos
import random
import time

def on_AwasPressed():
    lcd.clear(lcd.WHITE)
    retroPCCGObj = RetroPCCG()
    fileList = uos.listdir('/sd/cgData')
    index = random.randrange(len(fileList))
    fileName = fileList[index]
    retroPCCGObj.executePaint("/sd/cgData/" + fileName)
    del retroPCCGObj
    gc.collect()
    
def on_BwasPressed():    
    while True:
        randomDraw()

def on_CwasPressed():
    #押してから3秒後にスタート
    lcd.clear(lcd.BLACK)
    lcd.setCursor(0,0)
    lcd.print("3\n")
    time.sleep(1)
    lcd.print("2\n")
    time.sleep(1)
    lcd.print("1\n")
    time.sleep(1)

    lcd.clear(lcd.WHITE)
    retroPCCGObj = RetroPCCG()
    retroPCCGObj.executePaint("/sd/test.dat")
    del retroPCCGObj
    gc.collect()


def randomDraw():
    fileList = uos.listdir('/sd/cgData')
    #random.shuffle(fileList) は使えないみたい。
    while len(fileList) > 0:
        lcd.clear(lcd.WHITE)
        retroPCCGObj = RetroPCCG()
        index = random.randrange(len(fileList))
        fileName = fileList[index]
        retroPCCGObj.executePaint("/sd/cgData/" + fileName)
        fileList.pop(index)
        del retroPCCGObj
        gc.collect()
        time.sleep(5)
    
def printManual():
    lcd.clear(lcd.BLACK)
    lcd.setCursor(0,0)
    lcd.print("A: Draw Shuffle Once [/sd/cgData/*]\n")
    lcd.print("B: Draw Shuffle Loop [/sd/cgData/*]\n")
    lcd.print("C: Draw [/sd/test.dat]\n")

random.seed(int(time.time()))
uos.mountsd()
lcd.clear(lcd.BLACK)
printManual()

buttonA.wasPressed(on_AwasPressed)
buttonB.wasPressed(on_BwasPressed)
buttonC.wasPressed(on_CwasPressed)


