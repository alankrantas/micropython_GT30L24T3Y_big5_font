def getBig5Font(spi, cs, font_code, font_size=12, raw=False, printout=False):
    """
    For reading BIG-5 Chinese fonts from GT30L24T3Y/ER3303-1 SPI module.
    """
    
    def cmd(address):
        return bytes([0x0b, address >> 16 & 0xff, address >> 8 & 0xff, address & 0xff, 0xff])

    if isinstance(font_code, str) and len(font_code) == 4:
        msb, lsb = int(font_code[:2], 16), int(font_code[2:], 16)
    elif isinstance(font_code, int):
        msb, lsb = font_code >> 8, font_code & 0xff
    else:
        raise ValueError('font_code has to be str (ex. \'A140\') or int (ex. 0xa140)')
    
    if font_size == 12:
        base_addr = 0x0000
        buf_size = 24
    elif font_size == 16:
        base_addr = 0x5f4c0
        buf_size = 32
    elif font_size == 24:
        base_addr = 0xde5c0
        buf_size = 72
    else:
        raise ValueError('font_size has to be 12, 16 or 24')

    index = 0
    if 0xa1 <= msb <= 0xf9:
        if 0x40 <= lsb <= 0x7e:
            index = (msb - 0xa1) * 157 + (lsb - 0x40)
        elif 0xa1 <= lsb <= 0xfe:
            index = (msb - 0xa1) * 157 + 63 + (lsb - 0xa1)
        else:
            raise ValueError('invalid big-5 font code')
    else:
        raise ValueError('invalid big-5 font code')
    
    if font_size == 24 and index >= 10139:
        raise ValueError('font size 24 has no characters beyond font code E1BC')

    cs.off()
    spi.write(cmd(0x193f06 + index * 2))
    buf = spi.read(2)
    cs.on()
    
    address = buf[0] << 8 | buf[1]
    
    cs.off()
    spi.write(cmd(base_addr + address * buf_size))
    buf = spi.read(buf_size)
    cs.on()
    
    if printout:
        for i in range((buf_size - font_size), buf_size):
            line = []
            for j in range(buf_size // font_size):
                line.append('{:08b}'.format(buf[i - j * font_size]).replace('0', '-').replace('1', '#'))
            print(''.join(line))
                
    if raw:
        return buf
    else:
        from framebuf import FrameBuffer, MONO_VLSB
        return FrameBuffer(bytearray(buf), font_size if font_size == 24 else (font_size - 1), font_size, MONO_VLSB)


# ========================================================================================================================


if __name__ == '__main__':
    
    # big-5 字碼表:
    # http://web.tnu.edu.tw/me/study/moodle/tutor/vb6/tutor/r05/index.htm
    
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
    
    from machine import Pin, I2C, SPI
    from ssd1306 import SSD1306_I2C  # https://github.com/stlehmann/micropython-ssd1306

    spi = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    cs = Pin(17, Pin.OUT, value=1)
    
    buf = getBig5Font(spi, cs, data['月'], font_size=24, raw=True, printout=True)
    print(buf)
