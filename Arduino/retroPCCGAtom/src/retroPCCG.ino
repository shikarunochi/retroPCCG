#include <M5Unified.h>  
#include "FS.h"
#include <SPIFFS.h>
#include "lgfx.h"

#define PAINT_BUFFER 512
#define CG_DIRECTORY "/"
LGFX m5lcd;

const int DATA_END = -999;
const int STATUS_NONE = 0;//特に何もない状態。次に読んだ命令に従う
const int STATUS_LINE = 1;//LINE命令開始状態。次の2つを読み込んで、線を引く。
const int STATUS_LINE_NEXT = 2;//LINE途中状態。次の2つを読み込んで、前の続きで線を引く。最初に0が来たら、STATUS_LINE状態に戻る
const int STATUS_PAINT = 3;//色塗り
const int STATUS_PAINT_NEXT = 4;//色塗り継続
const int STATUS_LAST_PAINT = 5;//最後の描画

const int SCREEN_X = 320;
const int SCREEN_Y = 240;

const int LINE = -10;
const int PAINT = -20;
const int LAST_PAINT = -20;

boolean screenBuffer[SCREEN_X][SCREEN_Y];//実画面バッファ

//paintBuffer
struct GPoint {int lx,rx,y,oy;};
static GPoint buffer[PAINT_BUFFER];
static int bufferPoint;

void drawPicture(String fileName);

void drawline(int startX, int startY, int endX, int endY, long color);
bool paint(int paintX, int paintY, long color);
void scanLine(int leftX,int rightX,int y);
void lastPaint(int startX,int startY,int endX,int endY,long color);
long getData(File dataFile);
void Draw();
void randomDraw();
uint16_t rgb565( const unsigned long rgb);

#ifdef W240
M5Canvas canvas(&m5lcd);
#endif

#if defined(_M5ATOMS3)
#define BUTTON_A_PIN 41
#else
#define BUTTON_A_PIN 39
#endif

int wait = 1;
void setup() {
  auto cfg = M5.config();
  cfg.internal_imu=false;
  M5.begin(cfg);

  if (!SPIFFS.begin()) { 
    Serial.println("SPIFFS Mount Failed");
    return;
  }
  m5lcd.init();
  m5lcd.setRotation(1);
  //m5lcd.setRotation(3);
  m5lcd.setColorDepth(16);
  m5lcd.fillScreen(BLACK);     // CLEAR SCREEN
  //M5.Lcd.setRotation(0);        // SCREEN ROTATION = 0
  //wait= 1;
  #ifdef W240
   canvas.setColorDepth(8);
   canvas.createSprite(320,240); 
   canvas.fillScreen(BLACK); 
  #endif

  #ifdef _M5ATOMS3
  //GROVE接続外部LED点灯処理
  pinMode(1, OUTPUT); // 1番ピンを出力モードに変更
  #endif

  if(digitalRead(BUTTON_A_PIN) == 0) //ボタン押されてたら最速
  {
     wait = 0;
  }

  delay(1000);  
  randomDraw();
}

void randomDraw(){
  String fileNameList[100];
  //SDカード cgDataフォルダのファイル一覧取得
  File cgRoot;

  cgRoot = SPIFFS.open(CG_DIRECTORY);
  int fileCount = 0;
  while(1){
    File entry =  cgRoot.openNextFile();
    if(!entry){// no more files
      break;
    }
    //ファイルのみ取得
    if (!entry.isDirectory()) {
        fileNameList[fileCount] = entry.name();
        fileCount++;
    }
    entry.close();
  }
  cgRoot.close();
  
  if(fileCount == 0)
  {
    m5lcd.fillScreen(BLACK);
    m5lcd.setCursor(0, 0);
    m5lcd.printf("put CG Data \ninto :%s\n", CG_DIRECTORY );
    return;
  }
  //ソート
  sortList(fileNameList, fileCount);


  for(int index = 0;index < fileCount;index++){
    drawPicture(fileNameList[index]);
    if(wait == 0){
      delay(200);
    }else{
      for(int i = 0;i < 5;i++){
      #ifdef _M5ATOMS3
      digitalWrite(1, HIGH); // 1番ピンをHIGH（3.3V）に
      delay(200);
      digitalWrite(1, LOW); //1番ピンをLOW（0V）に
      delay(200);
      digitalWrite(1, HIGH); // 1番ピンをHIGH（3.3V）に
      delay(400);
      digitalWrite(1, LOW); //1番ピンをLOW（0V）に
      delay(200);
      #else
      delay(1000);
      #endif

     }
    }
  }

}

void drawPicture(String fileName){
  for(int x = 0;x < 320;x++){
    for(int y = 0;y < 240;y++){
      screenBuffer[x][y]=false;
    }
  }

  File dataFile = SPIFFS.open("/" + fileName, FILE_READ);
  Serial.print("FileOpen:");
  Serial.println(fileName);
  if(!dataFile){
    Serial.println("File not exist");
    return;
  }
  
  long endCheckValue = -1;
  int widthScaleParam = 1;
  
  int sizeX = getData(dataFile);
  int sizeY = getData(dataFile);
  float rateX  = 320.0f / sizeX;
  float rateY = 240.0f / sizeY;

  if(rateX < rateY){
    rateY = rateX;
  }else{
    rateX  =rateY;
  }
  int bgColor = getData(dataFile);
  int frameColor = getData(dataFile);
  
  m5lcd.fillScreen(bgColor);     // CLEAR SCREEN
  #ifdef W240
      canvas.fillScreen(bgColor);
  #endif
  int offsetX = 0; 
  int offsetY = 0;

  int startX = 0;
  int endX = 0;
  int startY = 0;
  int endY = 0;
  int paintX = 0;
  int paintY = 0;
  
  long color = 0;
  int status = STATUS_NONE;
  boolean fileEnd = false;
  
  while(fileEnd == false){
    long nextData = getData(dataFile);
    if(nextData == DATA_END){
        break;
    }
    if(status == STATUS_NONE){
      if(nextData == -10){
        status = STATUS_LINE;
      }else if(nextData == -20){
        status = STATUS_PAINT;
      }else if(nextData == -30){
        status = STATUS_LAST_PAINT;
      }else{
        fileEnd = true;
      }
    }else if(status == STATUS_LINE){
      //wait= 1;
      if(nextData == -1){
        status = STATUS_NONE;
      }else{
        color = nextData;
        startX = getData(dataFile);
        if(startX == -1){
          status = STATUS_LINE;
        }else{
          startY = getData(dataFile);
          status = STATUS_LINE_NEXT;
        }
      }
    }else if(status == STATUS_LINE_NEXT){
      //wait= 1;
      if (nextData <= endCheckValue){
        status =STATUS_LINE;
      }else{
        endX = nextData;
        endY = getData(dataFile);
        drawline(int(startX * rateX) + offsetX, int(startY * rateY) + offsetY, 
        int(endX * rateX) + offsetX , int(endY * rateY) + offsetY,color);
        startX = endX;
        startY = endY;
      }
    }else if (status == STATUS_PAINT){
      //wait= 2;
      if (nextData <= endCheckValue){
        status =STATUS_NONE;
      }else{
        color = nextData;
        paintX = getData(dataFile);
        paintY = getData(dataFile);
        paint(int(paintX * rateX) + offsetX, int(paintY * rateY) + offsetY,color);
        status = STATUS_PAINT_NEXT;
      }
    }else if (status == STATUS_PAINT_NEXT){
      //wait= 2;
      if (nextData <= endCheckValue){
        status =STATUS_PAINT;
      }else{
        paintX = nextData;
        paintY = getData(dataFile);
        paint(int(paintX * rateX) + offsetX, int(paintY * rateY) + offsetY,color);
      }
    }else if(status == STATUS_LAST_PAINT){
      //wait= 2;
      if (nextData <= endCheckValue){
        status =STATUS_NONE;
      }else{
        color = nextData;
        startX = getData(dataFile);
        startY = getData(dataFile);
        endX = getData(dataFile);
        endY = getData(dataFile);
        lastPaint(int(startX * rateX) + offsetX, int(startY * rateY) + offsetY, 
        int(endX * rateX) + offsetX , int(endY * rateY) + offsetY,color);
      }
    }
  }
  dataFile.close();
  Serial.println("Draw End");
}


//次の１つを読む。なければ -999
long getData(File dataFile){
  String buf = "\0";
  while(dataFile.available()){
    char nextChar = char(dataFile.read());
    //"," か改行か"#"が出るまで読む。
    if(nextChar == ',' || nextChar == '\r' || nextChar == '\n' || nextChar == '#'){
      if(buf.length() == 0){ // バッファまだ0文字の場合、何もせずもう一度処理
        continue;
      }
      if(nextChar == '#'){ //#の場合は以降はコメントなので行末まで読み飛ばし
        while(dataFile.available()){
          if(char(dataFile.read()) == '\r'){
            break;
          }
        }
      }

      if(buf.length() != 0){
        if(buf.startsWith("0x")){
          //0xから始まる場合は16進数として扱う
          long lData = strtol(buf.substring(2).c_str(), NULL, 16);
          //Convert RGB565
          return (long)rgb565(lData);
        }else{
          return buf.toInt();      
        }
      }
    }
    buf += nextChar; 
  }
  //ここまで来たら終了
  return DATA_END;  
}

void loop() {
  // put your main code here, to run repeatedly:
  randomDraw();
}

int pushCount = 0;
void drawline(int startX, int startY, int endX, int endY, long color) {
  //Serial.print("drawLine:");
  //Serial.print(startX);Serial.print(",");Serial.print(startY);Serial.print(",");
  //Serial.print(endX);Serial.print(",");Serial.print(endY);Serial.print(",");Serial.println(color);

  int dx = abs(endX - startX);
  int sx = (startX < endX) ? 1 : -1;
  int dy = abs(endY - startY);
  int sy = (startY < endY) ? 1 : -1;
  int err = ((dx > dy) ? dx : -dy) / 2;
  int e2;
  while(true) {
    if(startX >= 0 && startX < 320 && startY >= 0 && startY < 240){
  #ifdef W240
      canvas.drawPixel(startX - 40, startY , color);
  #else
      m5lcd.drawPixel(startX - 40, startY , color);
  #endif
      screenBuffer[startX][startY] = true;
    }

    if(startX == endX && startY == endY) {
      break;
    }
    e2 = err;
    if(e2 > -dx) {
      err -= dy;
      startX += sx;
    }
    if(e2 < dy) {
      err += dx;
      startY += sy;
    }
  }
  #ifdef W240
  pushCount++;
  if(pushCount > 10){
        canvas.pushRotateZoomWithAA(160,120,0,0.85,1);
        pushCount = 0;
  }
      //canvas.pushSprite(0,0);
  #endif

  delay(wait);//ゆっくり描く

}

bool paint(int paintX, int paintY, long color){
  Serial.print("paint:");
  Serial.print(paintX);Serial.print(",");Serial.print(paintY);Serial.print(",");Serial.print(color);
  //バッファにある限りループ
  //int lx; /* 領域右端のX座標 */
  //int rx; /* 領域右端のX座標 */
  //int y;  /* 領域のY座標 */
  //int oy; /* 親ラインのY座標 */
  GPoint gPoint;
  gPoint.lx = paintX;
  gPoint.rx = paintX;
  gPoint.y = paintY; 
  gPoint.oy = paintY; 

  buffer[0] = gPoint;
  bufferPoint = 1;
  
  int curPaintCnt = 0;
  
  while(bufferPoint > 0)
  {
    GPoint checkPoint = buffer[bufferPoint - 1]; 
    bufferPoint--;
    int lx = checkPoint.lx;
    int rx = checkPoint.rx;
    int ly = checkPoint.y;
    int oy = checkPoint.oy;

    int lxsav = lx - 1;
    int rxsav = rx + 1;
    
    //すでに塗られていたらスキップ
    if( screenBuffer[lx][ly] ==  true)
    {
      continue;  
    }

    //右の境界を探す
    while(rx < 319){
      if( screenBuffer[rx + 1][ly] ==  true){
        break;
      }
      rx = rx + 1;
    }

    //左の境界を探す
    while(lx > 0){
      if( screenBuffer[lx - 1][ly] ==  true){
        break;
      }
      lx = lx - 1;
    }
    
    //左端から右端を塗る
     drawline(lx, ly, rx, ly, color);
     
    //真上のスキャンライン走査
    if(ly - 1 >= 0){
      if( ly - 1 == oy){
        scanLine(lx ,lxsav, ly - 1, ly );
        scanLine(rxsav ,rx, ly - 1, ly );
      }else{
        scanLine(lx ,rx, ly - 1, ly );
      }
    }
    //真下のスキャンライン走査
    if(ly + 1 <= 239){
      if( ly + 1 == oy){
        scanLine(lx ,lxsav, ly + 1, ly );
        scanLine(rxsav ,rx, ly + 1, ly );
      }else{
        scanLine(lx ,rx, ly + 1, ly );
      }
    }

    curPaintCnt++;
    Serial.println(curPaintCnt);
  }
  //APP_LOG(APP_LOG_LEVEL_DEBUG, "PaintEnd");
  
  if(bufferPoint == 0)
  {
    Serial.println(":END");
    return true;
  }
  Serial.println(":ErrorEND");
  return false;
  
}

void scanLine(int lx,int rx,int y,int oy){
  int templx = 0;
  while(lx <=rx){
    while(lx < rx){
      if(screenBuffer[lx][y] == false){
        break;
      }
      lx = lx + 1;
    }
    if(screenBuffer[lx][y] == true){
      break;
    }
    templx = lx;

    while(lx <= rx){
      if(screenBuffer[lx][y] == true){
        break;
      }
      lx = lx + 1;
    }

    if(bufferPoint < PAINT_BUFFER){

      GPoint gPoint;
      gPoint.lx = templx;
      gPoint.rx = lx - 1;
      gPoint.y = y; 
      gPoint.oy = oy; 
  
      buffer[bufferPoint] = gPoint;
      bufferPoint++;
    }
  }
}

//指定された矩形で、まだ塗っていない部分だけ塗る
void lastPaint(int startX,int startY,int endX,int endY,long color){
  int y = startY;
  while (y <= endY){
    int x = startX;
    while (x <= endX){
      if (screenBuffer[x][y] == false){
  #ifdef W240
      canvas.drawPixel(x - 40, y , color);
  #else
        m5lcd.drawPixel(x - 40, y , color);
  #endif
      }
      x = x  + 1;
    }
    y = y + 1;
  }
  #ifdef W240
      canvas.pushRotateZoomWithAA(160,120,0,0.85,1);
  #endif
}


//https://forum.arduino.cc/index.php?topic=487698.0
uint16_t rgb565( const unsigned long rgb)
{
  uint16_t R = (rgb >> 16) & 0xFF;
  uint16_t G = (rgb >>  8) & 0xFF;
  uint16_t B = (rgb      ) & 0xFF;

  uint16_t ret  = (R & 0xF8) << 8;  // 5 bits
           ret |= (G & 0xFC) << 3;  // 6 bits
           ret |= (B & 0xF8) >> 3;  // 5 bits
       
  return( ret);
}

void testBuffer(){
    for(int x = 0;x < 320;x++){
      for(int y = 0;y < 240;y++){
        if(screenBuffer[x][y]==false){
          m5lcd.drawPixel((int16_t)x, (int16_t)y + 20, BLACK);
        }else{
          m5lcd.drawPixel((int16_t)x, (int16_t)y + 20, WHITE);
        }
      }
    }
}

/* bubble sort filenames */
//https://github.com/tobozo/M5Stack-SD-Updater/blob/master/examples/M5Stack-SD-Menu/M5Stack-SD-Menu.ino
void sortList(String fileList[], int fileListCount) { 
  bool swapped;
  String temp;
  String name1, name2;
  do {
    swapped = false;
    for(int i = 0; i < fileListCount-1; i++ ) {
      name1 = fileList[i];
      name1.toUpperCase();
      name2 = fileList[i+1];
      name2.toUpperCase();
      if (name1.compareTo(name2) > 0) {
        temp = fileList[i];
        fileList[i] = fileList[i+1];
        fileList[i+1] = temp;
        swapped = true;
      }
    }
  } while (swapped);
}
