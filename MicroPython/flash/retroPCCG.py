from m5stack import *
import barray
import gc

class Status:
    (NONE,LINE,LINE_NEXT,PAINT,PAINT_NEXT,LAST_PAINT) = range(6)
    

class RetroPCCG:
    
    PAINT_BUFFER = 250
    DATA_END = -999

    def __init__(self):
        self.endCheckValue = -1
        self.widthScaleParam = 1 

    def setParam(self, widthScale, endCheck):
        self.widthScaleParam = widthScale
        self.endCheckValue =  endCheck

    def executePaint(self, fileName):
        print(fileName)
        #PaintBuffer
        self.screenBuffer = barray.BARRAY(76800)
        self.dataFile = open(fileName, "r") 
        self.currentFileLine = ""

        sizeX = self.readData() #データの横ピクセル数
        sizeY = self.readData() #データの縦ピクセル数
        
        rateX = 320 / sizeX  
        rateY = 240 / sizeY 
        
        #入りきる側の倍率に合わせる
        if rateX < rateY:
            rateY = rateX / self.widthScaleParam
        else:
            rateX = rateY
        
        bgColor = self.readData()
        frameColor = self.readData()

        #X, Y, backGroundColor,FrameColor
        lcd.clear(bgColor)
        
        self.offsetX = int((320 - sizeX * rateX) / 2)
        self.offsetY = int((240 - sizeY * rateY) / 2)
        
        #画面サイズより小さい場合、枠を描く
        if self.offsetX > 0:
            self.drawLine(self.offsetX, 0 + self.offsetY , self.offsetX,sizeY + self.offsetY, frameColor)
            self.drawLine(sizeX + self.offsetX, 0 + self.offsetY, sizeX + self.offsetX , sizeY + self.offsetY, frameColor)
        
        if self.offsetY > 0:
            self.drawLine(0 + self.offsetX, self.offsetY, sizeX + self.offsetX, self.offsetY, frameColor)
            self.drawLine(0 + self.offsetX, sizeY + self.offsetY, sizeX + self.offsetX , sizeY + self.offsetY , frameColor)
        
        startX = 0
        endX = 0
        startY = 0
        endY = 0  
        color = 0
        
        fileEnd = False
        status = Status.NONE
        while fileEnd == False:
            nextData = self.readData()
            if nextData == self.DATA_END:
                break;
            if status == Status.NONE:
                if nextData == -10:
                    status = Status.LINE
                elif nextData == -20:
                    status = Status.PAINT
                elif nextData == -30:
                    status = Status.LAST_PAINT
                else:
                    fileEnd = True
            elif status == Status.LINE:
                if nextData == -1:
                    status = Status.NONE
                else:
                    color = nextData
                    startX = self.readData()
                    if startX == -1:
                        status = Status.LINE # 0,-1 で来るパターンがある
                    else:
                        startY = self.readData()
                        #TODO:１ドット打つ
                        status = Status.LINE_NEXT
            elif status == Status.LINE_NEXT:
                if nextData <= self.endCheckValue:
                    status = Status.LINE
                else:
                    endX = nextData
                    endY = self.readData()
                    self.drawLine(int(startX * rateX) + self.offsetX, int(startY * rateY) + self.offsetY, int(endX * rateX) + self.offsetX,int(endY * rateY) + self.offsetY, color)
                    startX = endX
                    startY = endY
            elif status == Status.PAINT:
                if nextData <= self.endCheckValue:
                    status = Status.NONE
                else:
                    color = nextData
                    paintX = self.readData()
                    paintY = self.readData()
                    self.paint(int(paintX * rateX) + self.offsetX,int(paintY * rateY) + self.offsetY ,color)
                    status = Status.PAINT_NEXT

            elif status == Status.PAINT_NEXT:
                if nextData <= self.endCheckValue:
                    status = Status.PAINT
                else:
                    paintX = nextData
                    paintY = self.readData()
                    self.paint(int(paintX * rateX) + self.offsetX,int(paintY * rateY) + self.offsetY ,color)
            elif status == Status.LAST_PAINT:
                if nextData <= self.endCheckValue:
                    status = Status.NONE
                else:
                    color = nextData
                    startX = self.readData()
                    startY = self.readData()
                    endX = self.readData()
                    endY = self.readData()
                    self.lastPaint(int(startX * rateX) + self.offsetX,int(startY * rateY) + self.offsetY, \
                    int(endX * rateX) + self.offsetX,int(endY * rateY) + self.offsetY ,color)
                
            gc.collect()
            
        #self.testBuffer()    
        self.dataFile.close()
        if self.offsetX > 0:
            self.paint(0, 120, frameColor)
            self.paint(319, 120, frameColor)

        if  self.offsetY > 0:
            self.paint(160, 0, frameColor)
            self.paint(160, 239, frameColor)

        del self.currentFileLine
        del self.screenBuffer
        del self.dataFile
        gc.collect()

        
    def readData(self):
        while True: #値設定While
            while True: #ファイル１行読みこみWhile
                if len(self.currentFileLine) == 0:
                    self.currentFileLine = self.dataFile.readline().strip()
                    if self.currentFileLine :
                        #  "#"以降はコメント
                        commentIndex = self.currentFileLine.find("#")
                        if commentIndex != -1:
                            self.currentFileLine = self.currentFileLine[:commentIndex].strip()
                        if len(self.currentFileLine) > 1:
                            break
                    else:
                        return self.DATA_END
                else:
                    break
            #次のカンマの位置までを切り出す
            index = self.currentFileLine.find(",")
        
            if index == -1: #カンマ見つからず
                result = self.currentFileLine.strip()
                del self.currentFileLine
                gc.collect()    
                self.currentFileLine = ""
                if len(result) > 0:
                    return int(result,0)
            else:
                result = self.currentFileLine[:index].strip()
                self.currentFileLine = self.currentFileLine[index+1:].strip()
                if len(result) > 0:
                    return int(result,0)
                
    def drawLine(self,startX,startY,endX,endY,color):
        realStartX = startX
        realStartY = startY
        realEndX = endX
        realEndY = endY

        dx = abs(realEndX - realStartX)
        sx = 1 if realStartX < realEndX else -1
        dy = abs(realEndY - realStartY)
        sy = 1 if realStartY < realEndY else -1
        err = int((dx if dx > dy else -dy) / 2)
        
        while True:
            if realStartX >= 0 and realStartX < 320 and realStartY >=0 and realStartY < 240:
                lcd.pixel(realStartX,realStartY,color)
                self.screenBuffer.put(realStartX + realStartY * 320, True)
            
            if realStartX == realEndX and realStartY == realEndY:
                break
            
            e2 = err
            if e2 > -dx:
                err -= dy
                realStartX += sx
            
            if e2 < dy:
                err += dx
                realStartY += sy

    def paint(self,pixelX, pixelY, color):
        #バッファにある限りループ
          #int lx; /* 領域右端のX座標 */
          #int rx; /* 領域右端のX座標 */
          #int y;  /* 領域のY座標 */
          #int oy; /* 親ラインのY座標 */
          
        gPoint = {"lx":pixelX, "rx":pixelX ,"y":pixelY, "oy":pixelY}
        
        self.bufferList = [gPoint]

        while len(self.bufferList) > 0:
            checkPoint = self.bufferList.pop(0)
            lx = checkPoint["lx"]
            rx = checkPoint["rx"]
            ly = checkPoint["y"]
            oy = checkPoint["oy"]

            lxsav = lx - 1
            rxsav = rx + 1

            ##処理済みなら飛ばす
            if self.screenBuffer.get(lx + ly * 320) == True:
                continue
            
            ##右の境界を探す
            while rx < 319:
                if self.screenBuffer.get(rx + 1 + ly * 320) == True:
                    break
                rx = rx + 1

            ##左の境界を探す
            while lx > 0:
                if self.screenBuffer.get(lx - 1 + ly * 320) == True:
                    break
                lx = lx - 1

            ##lx から rx まで線を引く
            self.drawLine(lx, ly, rx, ly, color)
            gc.collect()

            ##真上のスキャンライン走査
            if ly - 1 >= 0:
                if ly - 1 == oy:
                    self.scanLine( lx, lxsav, ly -1 ,ly )
                    self.scanLine( rxsav, rx, ly -1 ,ly )
                else:
                    self.scanLine( lx, rx, ly -1 ,ly )
            
            ##真下のスキャンライン走査
            if ly + 1 <= 239:
                if ly + 1 == oy:
                    self.scanLine( lx, lxsav, ly + 1, ly)
                    self.scanLine( rxsav, rx, ly + 1, ly)
                else:
                    self.scanLine( lx, rx, ly +1, ly)

    def scanLine(self, lx, rx, y, oy):
        templx = 0
        while lx <= rx:
            while lx < rx:
                if self.screenBuffer.get(lx + y * 320) == False:
                    break
                lx = lx + 1
                
            if self.screenBuffer.get(lx + y * 320) == True:
                break
            templx = lx

            while lx <= rx:
                if self.screenBuffer.get(lx + y * 320) == True:
                    break
                lx = lx + 1

            gPoint = {"lx":templx, "rx":lx - 1 ,"y":y, "oy":oy}
            if len(self.bufferList) < self.PAINT_BUFFER:
                self.bufferList.append(gPoint)

    #指定された矩形で、まだ塗っていない部分だけ塗る
    def lastPaint(self, startX, startY, endX, endY, color):
        print("lastPaint:" + str(startX) + ":"+ str(startY) +":"+  str(endX) +":"+  str(endY) )
        y = startY
        while y <= endY:
            x = startX            
            while x <= endX:
                if self.screenBuffer.get(x + y * 320) == False: 
                    lcd.pixel(x,y,color)
                x = x  + 1
            y = y + 1

    def testBuffer(self):
        for x in range(0,320):
            for y in range(0,240):
                if self.screenBuffer.get(x + y * 320) == True:
                     lcd.pixel(x,y,lcd.WHITE)
                else:                 
                     lcd.pixel(x,y,lcd.BLACK)