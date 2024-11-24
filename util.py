

def find_possible_shitjis(data):
    i = 0
    decoded = []
    try:
        while True:
            current = data[i:i + 4]
            if current[0] < 0x80:
                decoded.append(bytes([current[0]]))
            elif (((0xa0 > current[0] > 0x80)
                   or (0xf0 > current[0] >= 0xe0))
                  and ((0xfc >= current[1] >= 0x9f) if current[0] % 2 == 0 else ((0x40 <= current[1] <= 0x9e) and current[1] != 0x7f))):
                decoded.append(current[:2])
            i += 1
    except IndexError:
        pass
    return decoded

def decode_shitjis(value):
    pass


