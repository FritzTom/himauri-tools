
import util

with open("701.him", "rb") as f: data = f.read()

decoded_data = util.find_possible_shitjis(data)

print(decoded_data)

