import sys
import os

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
    #fileName = 'MagicalMirai2018.dat'
    print("LINEandPAINT_CONVERT_MZ700.py fileName [quality=100] [addLineColor1 addLineColor2 addLineColor3...]")
    print("ex1: LINEandPAINT_CONVERT_MZ700.py MagicalMirai2018.dat")
    print("ex2: LINEandPAINT_CONVERT_MZ700.py MagicalMirai2018.dat 80")
    print("ex3: LINEandPAINT_CONVERT_MZ700.py MagicalMirai2018.dat 100 0x1d1328 0x4e2f4f")
    print("データ量が大きくなりすぎたときは qualityを小さくしてみてください。")
    print("追加カラー指定時は quality 項目も必須となります。")
    print("DumpListEditorのMZ-1500モードで変換する前提で、PMODE/PMOVE/PLINE命令を用いています")
    sys.exit()

if len(sys.argv) > 2:
    quality= int(sys.argv[2]) 
else:
    quality = 100

addLineColor=['0']

if len(sys.argv) > 3:
    for index in range(3,len(sys.argv)):
        addLineColor.append(sys.argv[index])

cgData = open(fileName, encoding="utf-8")

file, ext = os.path.splitext(fileName)

mz700Data = open(file + "_mz700.bas", mode='w', encoding="utf-8")

line = cgData.readline() #1行目はタイトル

lineMode = False
mz700LineData = []

while line:
    line = cgData.readline()
    if line=='':
        continue
    print("line:" + line)
    lineData = line.rstrip().split(',')
    #-10から始まっていたら、LINEモード。LINEは1行1LINE

    if len(lineData) == 0:
        continue
    if lineMode == False:
        if line.startswith('-10,')==False:
        #LINE描画以外は '-1'の行が出るまで読み込んでスルー
            while(1):
                if cgData.readline().rstrip() == '-1':
                    lineData = ""
                    break
            continue
        else:
            lineData.pop(0) # -10 をPOPしておく
    else:
        if line.rstrip() == '-1': #LINE MODE の終わり
            lineMode = False
            lineData = ""
            continue
    
    lineMode = True
    #color が 0 または指定カラー以外の場合はスルー
    color = lineData.pop(0)
    drawFlag = False
    for checkColor in addLineColor:
        if checkColor == color:
            drawFlag = True
            break
        
    if drawFlag == False:
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
            if(int(lineInfo) >= 640):
                mz700LineData.append(480) #たまに640をちょっと超えた数値が入ってるので念のため上限チェック
            else:
                mz700LineData.append(int(int(lineInfo) * 0.75)) #0.75倍した値を入れる
    mz700LineData.append(-1) #LINE終わりの-1
    
mz700LineData.append(-999) #DATA終わりの-999

#mz700LineData を DATA文で書きだす
mz1500mode='P'
#MZ-1500の場合、MODE->PMODE MOVE->PMOVE LINE->PLINEとなります。MZ-700の MODE/MOVE/LINE とBASIC中間コードは同じものになります。
#DumpListEditorのMZ-1500 MODEでMZTを生成すると、MZ-700読み込み時には中間コード変換されるため、MODE/MOVE/LINEとして読み込んでくれます。
#MZ-80Kモードだと、MODE/MOVE/LINEが中間コードに変換されず、テキスト書き出しで、実機読み込み時に変換処理が発生してしまうので、MZ-1500モードがオススメです。

mz700Data.write('5 REM Q=' + str(quality) + ' C='+ ",".join(addLineColor).upper() +'\n')
mz700Data.write('10 ' + mz1500mode + 'MODE GR\n')
mz700Data.write('20 P=0\n')
mz700Data.write('30 READ X\n')
mz700Data.write('40 IF X=-999 THEN ' + mz1500mode + 'MOVE 0,-450:' + mz1500mode + 'MODE TN:END\n')
mz700Data.write('50 IF X=-1 THEN P=0:GOTO 30\n')
mz700Data.write('60 READ Y\n')
mz700Data.write('70 Y=-Y\n')
mz700Data.write('80 IF P=0 THEN ' + mz1500mode + 'MOVE X,Y:P=1:GOTO 30\n')
mz700Data.write('90 ' + mz1500mode + 'LINE X,Y:GOTO 30\n')

lineNumber = 1000
for i in range(0,len(mz700LineData),15):
    mz700Data.write(str(lineNumber) + ' DATA ')
    mz700Data.write(','.join(map(str,(mz700LineData[i:i+15]))))
    mz700Data.write('\n')
    lineNumber = lineNumber + 10

mz700Data.close()
cgData.close()