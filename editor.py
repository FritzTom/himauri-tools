
import json, os

def check_file(content):
    file_length = int.from_bytes(content[0x8:0x8 + 3], "big")
    if file_length != len(content):
        print("Invalid file length!")
        return False
    return True

def fix_file_length(content):
    file_length = len(content).to_bytes(3, "big")
    content = content[:0x8] + file_length + content[0x8 + 3:]
    return content

def get_id(data):
    return data[0]

def create_content(values):
    header_size = 16
    data = create_data(values)
    content = bytearray()
    content.extend([0x48, 0x69, 0x6D, 0x61, 0x75, 0x72, 0x69, 0x00])
    content.extend((len(data) + header_size).to_bytes(3, "big"))
    content.extend([0 for _ in range(5)])

    content.extend(data)

    return bytes(content)

def split_content(content):
    beginning_data = 0x10
    return content[:beginning_data], content[beginning_data:]

def parse_data(data):
    if not data.startswith(b"\x0a\x0d"):
        raise Exception("Invalid start for data")
    entries = data[2:].split(b"\x0a\x0d")
    return entries

def create_data(values):
    data = b"\x0a\x0d".join(values)
    return b"\x0a\x0d" + data





def main(prefix = None):
    while True:
        #file_path = "701.him"
        file_path = input("Enter the path to your binary file: ")  # Prompt for file path
        if prefix:
            file_path = os.path.join(prefix, file_path)
        if not os.path.isfile(file_path):
            print("The specified file does not exist, please check the path and try again.")
            continue
        break

    with open(file_path, "rb") as f:
        content = f.read()

    headers, data = split_content(content)
    values = parse_data(data)

    strings = extract_strings(values)

    string_object = []
    for i in strings:
        name, text = i[1].split(b"\x81\x5e", 1)
        status = 0
        try:
            name = name.decode("shift-jis")
        except UnicodeDecodeError:
            status |= 1
            name = name.hex(" ")
        try:
            text = text.decode("shift-jis")
        except UnicodeDecodeError:
            status |= 2
            text = text.hex(" ")

        string_object.append([i[0], status, name, text])

    if len(input("Export?: ")) > 0:
        with open("strings", "w") as f: f.write(json.dumps(string_object, ensure_ascii=False, indent=4))

    if len(input("Import?: ")) > 0:
        with open("strings", "r") as f: string_object = json.loads(f.read())
        new_strings = []
        lo = -1
        for i in string_object:
            if i[0] > 0:
                lo = i[0]
                break
        if lo == -1:
            raise Exception("Missing index values!")
        for i in string_object:
            o, s, n, t = i
            if s & 1:
                n = bytes([int(i, 16) for i in n.split(" ")])
            else:
                n = n.encode("shift-jis", errors="ignore")
            if s & 2:
                t = bytes([int(i, 16) for i in t.split(" ")])
            else:
                t = t.encode("shift-jis", errors="ignore")
            if o > 0: lo = o

            new_strings.append((lo, n + b"\x81\x5e" + t))

        values = update_data_with_new_strings(values, new_strings)
    else:
        print("Quitting.")
        return


    content = create_content(values)


    print("Quitting.")

    with open(file_path, "wb") as f:
        f.write(content)

    print("Changes saved to sub file.")


# def filter_data(data):
#     filtered_data = []
#     for item in data:
#         if len(item) > 0 and len(item[0]) > 1:
#             if item[0][1][0] not in [0x36, 0x32]:
#                 filtered_data.append(item)
#     return filtered_data

def extract_strings(values):
    strings = []
    for i in range(len(values)):
        value = values[i]
        if get_id(value) == 0x34:
            value = value[value.index(b"\x00\x01") + 2:]
            value = value[:value.index(b"\x00")]
            strings.append((i, value))

    return strings

def update_data_with_new_strings(values, new_strings):

    new_values = []
    for i in new_strings:
        p, v = i
        ov = values[p]

        start = ov.index(b"\x00\x01", 1) + 2
        end = ov.index(b"\x00", start)

        nv = ov[:start] + v + ov[end:]
        new_values.append((p, nv))

    final_values = []
    for i in range(len(values)):
        found = False
        for j in new_values:
            if j[0] == i:
                found = True
                break
        if not found:
            final_values.append(values[i])
        else:
            for j in new_values:
                if j[0] == i:
                    final_values.append(j[1])

    return final_values


if __name__ == "__main__":
    main()