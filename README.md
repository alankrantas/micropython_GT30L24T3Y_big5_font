# 從 GT30L24T3Y/ER3303-1 SPI 字庫芯片讀取 BIG-5 漢字的簡易 MicroPython 驅動程式

![IMG_0001](https://user-images.githubusercontent.com/44191076/129242480-861ec0a6-f84e-44bd-9a00-d1b0b5d3048f.JPG)

GT30L24T3Y/ER3303-1 是高通 (Genitop，不是那個 Qualcomm) 生產的[眾多字庫晶片](http://www.mitsutech.com.tw/vision_T/product_genitop0.htm)之一，如今還可以買到，但似乎沒有人真的懂要怎麼操作它，原始文件也寫得不是很清楚。花了一番功夫，總算搞懂是怎麼運作的了。

![0117021043](https://user-images.githubusercontent.com/44191076/129241611-219bcaa0-8109-4579-b90f-2b75e650b112.jpg)

| 腳位 | 意義 |
| --- | --- |
| GND | GND |
| 3.3-5V | 3.3V 或 5V |
| CS | CS (chip select) |
| SI | MOSI/SPI Tx |
| SO | MISO/SPI Rx |
| SCK | SCK |

儘管官方文件指出 GT30L24T3Y 通訊速度可達 80 MHz，但在此測試只能在 40 MHz 穩定運作。

## 使用

把 [big5.py](https://github.com/alankrantas/micropython_Big5_GT30L24T3Y_ER3303-1/blob/main/big5.py) 內的 getBig5Font 函式拷貝到你的程式中即可。其呼叫參數如下：

```python
getBig5Font(spi, cs, font_code, font_size, raw=False, printout=False)
```

| 參數 | 意義 |
| --- | --- |
| spi | SPI 物件 (machine.SPI 或 machine.SoftSPI) |
| cs | CS 腳位物件 (machine.Pin) |
| font_code | BIG-5 字碼 (字串或數值, 如 'A140' 或 0xA140, 參閱[字碼表](http://www.mitsutech.com.tw/vision_T/product_genitop0.htm)) |
| font_size | BIG-5 字體大小 (12, 16 或 24) |
| raw | 設為 True 時直接傳回 bytes 陣列, 否則預設傳回 framebuf.FrameBuffer |
| printout | 設為 True 時會在 REPL 印出該字的文字圖檔 |

傳入不正確的引數會使它拋出錯誤。

預設下 getBig5Font 會傳回 MicroPython 的 framebuf.FrameBuffer 物件，讓你能把它直接貼在某些顯示器模組上。據我所知 [SSD1306 OLED](https://github.com/stlehmann/micropython-ssd1306) 及 [PCD8544/Nokia 5110 LCD](https://github.com/mcauser/micropython-pcd8544) 的驅動程式都支援 FrameBuffer。

## BIG-5 字體

GT30L24T3Y 支援 GB、BIG-5 和 Unicode 三種中文字，以及幾種 ASCII 英數字形。目前我只實作 BIG-5。Unicode 字庫似乎跟 BIG-5 是共用的，只不過是改成讓你用 Unicode 字碼來查詢而已，但我並不清楚此晶片使用的 Unicode 編碼順序 (用 ```ord()``` 取得的字碼跟晶片用的似乎不同)。

GT30L24T3Y 將字庫的順序一併存在晶片中，所以查詢時其實會有兩次 SPI 讀寫，第一次是用字碼表的順序去查字在晶片裡的 offset 位置，第二次才是把字讀出來。問題就在於，這個已經有點歷史的晶片的 BIG-5 字碼和你在現代軟體得到的結果 (包括用正規 Python 的 ```codecs.encode()```) 會有出入，有很多後面的非中文字並不存在於晶片中，所以還是乖乖用舊的字碼表吧。

另外就文件的說法，24x24 字體只支援基本中文字，所以字碼不能超過 E1BC。

## 測試

我在圖中用的是 Raspberry Pi Pico 與 SSD1306，但這應該也適用於 ESP8266/ESP32。我用的 MicroPython 版本為 v1.16。

你可以先查詢你要使用的字，並建一個 Python 字典當對照表。不過在連續印出文字時，由於 MicroPython 是基於 Python 3.4，字典內容不會照元素的存入順序排列，所以你仍得用另外的方式 (比如一個串列) 來走訪之。

```python
    # 字碼對照表    
    data = {
        '我': 'A7DA',
        '要': 'AD6E',
        '代': 'A54E',
        '替': 'B4C0',
        '月': 'A4EB',
        '亮': 'AB47',
        '懲': 'C367',
        '罰': 'BB40',
        '你': 'A741',
        }

    # 要顯示的文字
    text = '我要代替月亮懲罰你'

    from machine import Pin, I2C, SPI
    from ssd1306 import SSD1306_I2C

    spi = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    cs = Pin(17, Pin.OUT, value=1)
    
    display = SSD1306_I2C(128, 64, I2C(1, scl=Pin(27), sda=Pin(26)))
    display.fill(0)
    
    pos = 0
    for t in text:
        display.blit(getBig5Font(spi, cs, data[t], 12), pos, 0)
        pos += 12
    
    pos = 0
    for t in text:
        display.blit(getBig5Font(spi, cs, data[t], 16), pos, 18)
        pos += 16
        
    pos = 0
    for t in text:
        display.blit(getBig5Font(spi, cs, data[t], 24), pos, 40)
        pos += 24
    
    display.show()
    
    getBig5Font(spi, cs, data['月'], 24, printout=True)
```

最後一行會在主控台印出

```
------------------------
------------------------
------------------------
#-----------------------
-#----------------------
-##---------------------
--###-------------------
---####################-
-----#################--
----------#-----#----#--
----------#-----#----#--
----------#-----#----#--
----------#-----#----#--
----------#-----#----#--
--#-------#-----#----#--
--#-------#-----#----#--
###-------#-----#----#--
-######################-
--#####################-
---------------------#--
------------------------
------------------------
------------------------
------------------------
                        
```
