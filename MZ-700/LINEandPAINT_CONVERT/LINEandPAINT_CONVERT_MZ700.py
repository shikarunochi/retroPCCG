import sys
import os

#色が黒の線だけ、640x480→480x360に変換して描画。0.75倍

def linePixelSet(x1,y1,x2,y2):
    startX = x1
    startY = y1
    endX = x2
    endY = y2

    pixelSet = {(startX,startY)}
    dx = abs(endX - startX)
    sx = 1 if (startX < endX)else -1
    dy = abs(endY - startY)
    sy = 1 if (startY < endY)else -1
    err = int((dx if (dx > dy) else -dy) / 2)

    while True:
        pixelSet.add((startX,startY))
        
        if startX == endX and startY == endY:
            break
    
        e2 = err
        if e2 > -dx: 
            err = err -  dy
            startX = startX + sx
    
        if e2 < dy :
            err = err + dx
            startY = startY + sy
    return pixelSet

if len(sys.argv) > 1:
    fileName = sys.argv[1]
else:
    fileName = 'MagicalMirai2018.dat'
    #print("ファイル名を入力してください")
    #sys.exit()
    
cgData = open(fileName, encoding="utf-8")

file, ext = os.path.splitext(fileName)

mz700Data = open(file + "_mz700.bas", mode='w', encoding="utf-8")

line = cgData.readline() #1行目はタイトル

lineMode = False
mz700LineData = []

while line:
    line = cgData.readline()
    print("line:" + line)
    lineData = line.rstrip().split(',')
    #-10または-30から始まっていたら、LINEモード。LINEは1行1LINE
    if len(lineData) == 0:
        continue
    if lineMode == False:
        if line.startswith('-10') ==False and line.startswith('-30') ==False:
        #LINE描画以外は '-1'の行が出るまで読み込んでスルー
            while(1):
                if cgData.readline().rstrip() == '-1':
                    break
            continue
        else:
            lineData.pop(0) # -10 / -30 をPOPしておく
    else:
        if line.rstrip()== '-1': #LINE MODE の終わり
            lineMode == False
            continue
    
    lineMode = True
    #color が 0 以外の場合はスルー
    color = lineData.pop(0)
    if color != '0':
        continue
    #線のデータを作成
    index = 0
    while(1):
        if index + 5 >= len(lineData):#データ最後
            break
        #DATA削減処理を入れておく
		#(x1,y1)-(x2,y2)の傾きと、(x1,y1)-(x3,y3)の傾きが同じであれば(x2,y2)を削除できる。
        #(x1,y1)-(x2,y2)と(x2,y2)-(x3,y3)で塗るドットと、(x1,y1)-(x3,y3)で塗るドットが同一であれば(x2,y2)を削除できる。
        #0.75倍した状態で比較する
        quality=100 #データ量が大きくなりすぎたときは quality落としてみてください。
        x1 = int(int(lineData[index + 0])*0.75*quality/100)
        y1 = int(int(lineData[index + 1])*0.75*quality/100)
        x2 = int(int(lineData[index + 2])*0.75*quality/100)
        y2 = int(int(lineData[index + 3])*0.75*quality/100)
        x3 = int(int(lineData[index + 4])*0.75*quality/100)
        y3 = int(int(lineData[index + 5])*0.75*quality/100)
        
        oldPixelSet = linePixelSet(x1,y1,x2,y2)|linePixelSet(x2,y2,x3,y3)
        newPixelSet = linePixelSet(x1,y1,x3,y3)
            
        if oldPixelSet == newPixelSet: #集合の比較
            del lineData[index+2]
            del lineData[index+2] #詰まっているので同じINDEX
        else:    
            index = index + 2
	
    for lineInfo in lineData:
        if int(lineInfo) >= 0:
            mz700LineData.append(int(int(lineInfo) * 0.75)) #0.75倍した値を入れる
    mz700LineData.append(-1) #LINE終わりの-1
    
mz700LineData.append(-999) #DATA終わりの-999

#mz700LineData を DATA文で書きだす

mz700Data.write('10 MODE GR\n')
mz700Data.write('20 P=0\n')
mz700Data.write('30 READ X\n')
mz700Data.write('40 IF X=-999 THEN MODE TN:PRINT/P:SKIP5:END\n')
mz700Data.write('50 IF X=-1 THEN P=0:GOTO 30\n')
mz700Data.write('60 READ Y\n')
mz700Data.write('70 Y=360-Y\n')
mz700Data.write('80 IF P=0 THEN MOVE X,Y:P=1:GOTO 30\n')
mz700Data.write('90 LINE X,Y:GOTO 30\n')

lineNumber = 1000
for i in range(0,len(mz700LineData),15):
    mz700Data.write(str(lineNumber) + ' DATA ')
    mz700Data.write(','.join(map(str,(mz700LineData[i:i+15]))))
    mz700Data.write('\n')
    lineNumber = lineNumber + 10

mz700Data.close()
cgData.close()
