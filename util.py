
def try_decode_utf8(data):
    i = 0
    decoded = []
    try:
        while True:
            current = data[i:i + 4]
            if (current[0] & 128) == 0:
                decoded.append(current[0])
                i += 1
            elif (((current[0] >> 5) ^ 0b110) == 0) and (((current[1] >> 6) ^ 10) == 0):
                decoded.append(current[:2])
                i += 2
            elif ((current[0] >> 4) ^ 0b1110) == 0 and (((current[1] >> 6) ^ 10) == 0) and (((current[2] >> 6) ^ 10) == 0):
                decoded.append(current[:3])
                i += 3
            elif ((current[0] >> 3) ^ 0b110) == 0 and (((current[1] >> 6) ^ 10) == 0) and (((current[2] >> 6) ^ 10) == 0) and (((current[3] >> 6) ^ 10) == 0):
                decoded.append(current)
                i += 4
            else:
                i += 1
    except IndexError:
        pass
    return decoded



