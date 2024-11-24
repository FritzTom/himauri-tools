
import util

with open("current.hxp", "rb") as f: data = f.read()

decoded_data = util.try_decode_utf8(data)



