
import json, os

def ex_import_texts(values, titles = None, ignore_titles = False):
    while True:
        inp = input("\x1b[42mi\x1b[0mmport, \x1b[42me\x1b[0mxport, \x1b[42mq\x1b[0muit ?: ")
        if len(inp) < 1: continue
        inp = inp.lower()
        inp = inp[0]
        if not inp in "qie":
            print("Invalid input.")
            continue
        break
    if inp == "q": return None
    if inp == "e":
        ng = 0
        data = ""
        for i in range(len(values)):
            data += f"{i}: "
            for j in range(len(values[i])):
                if titles and titles[i][j]:
                    name = titles[i][j]
                else:
                    name = ng
                    ng += 1
                data += f";N;{name};O;"
                data += f"{values[i][j].decode('shift-jis', errors='ignore')};A;"
            if data.endswith(";A;"):
                data = data[:-3]
            data += ";B;\n"
        data = data[:-4]
        with open("exported", "w", encoding="utf-8") as f:
            f.write(data)
        return None
    ov = values
    with open("exported", "r", encoding="utf-8") as f:
        data = f.read()
    data = data.split(";B;\n")
    values = []
    for i in range(len(data)):
        if i != int(data[i].split(": ", 1)[0]):
            print("Improperly ordered file.\nAborting!")
            exit(1)
        values.append([])
        current_values = data[i].split(": ", 1)[1]
        if len(current_values) > 0:
            current_values = current_values.split(";A;")
        else:
            current_values = []
        for j in range(len(current_values)):
            value = current_values[j]
            if not ignore_titles:
                if value.startswith(";N;"):
                    if not (titles and len(titles) > i and len(titles[i]) > j):
                        print("Too many names.\nAborting!")
                        exit(1)
                    if value[3:].split(";O;")[0] != titles[i][j]:
                        print("Invalid name.\nAborting!")
                        exit(1)
                elif titles and len(titles) > i and len(titles[i]) > j:
                    print("Missing name.\nAborting!")
                    exit(1)
            if value.startswith(";N;"):
                value = value.split(";O;", 1)[1]
            values[i].append(value.encode("shift-jis"))
        if i >= len(ov):
            print("Too many entries.\nAborting!")
            exit(1)
        if len(values[i]) != len(ov[i]):
            print("Invalid sub entry amount.\nAborting!")
            exit(1)
    if len(values) != len(ov):
        print("Invalid length.\nAborting!")
        exit(1)
    return values

def check_file(content):
    file_length = int.from_bytes(content[0x8:0x8 + 3], "big")
    if file_length != len(content):
        print("Invalid file length!")
        return False

    scenario_data_offset = int.from_bytes(content[0x17:0x17 + 2], "big")

    number_offsets = content[0x1c:0x1c + 2]
    number_offsets = int.from_bytes(number_offsets, "big")

    string_offsets_raw = content[0x1e:scenario_data_offset]
    if len(string_offsets_raw) % 3 != 0:
        print("Offset misalignment!")
        return False

    offsets = []
    for i in range(len(string_offsets_raw) // 3):
        offsets.append(int.from_bytes(string_offsets_raw[i * 3:(i + 1) * 3], "big"))

    if len(offsets) != number_offsets:
        print("Incorrect number of offsets!")
        return False

    return True

def parse_offsets(values):
    offsets = []
    for i in values:
        if get_id(i[0]) == 0x33:
            offsets.append(i[1])
    return offsets

def adjust_value_segment_offsets(values, offset_offset):
    for i in range(len(values)):
        values[i][1] = values[i][1] + offset_offset
    return values

def get_offsets(content):

    scenario_data_offset = int.from_bytes(content[0x17:0x17 + 2], "big")

    string_offsets_raw = content[0x1e:scenario_data_offset]
    if len(string_offsets_raw) % 3 != 0:
        print("Offset misalignment!")
        return False

    offsets = []
    for i in range(len(string_offsets_raw) // 3):
        offsets.append(int.from_bytes(string_offsets_raw[i * 3:(i + 1) * 3], "big"))

    return offsets

def get_segment_offsets(values):
    offsets = []
    for i in values:
        offsets.append(i[1])
    return offsets

def set_offsets(content, offsets):
    offsets_raw = create_offsets(offsets)

    scenario_data_offset = int.from_bytes(content[0x17:0x17 + 2], "big")

    if len(offsets_raw) != (scenario_data_offset - 0x1e):
        raise Exception("Changing amount of offsets.")

    content = content[:0x1e] + offsets_raw + content[scenario_data_offset:]

    return content

def create_offsets(offsets):
    offsets_raw = b""
    for i in offsets:
        offsets_raw = offsets_raw + i.to_bytes(3, "big")
    return offsets_raw

def fix_file_length(content):
    file_length = len(content).to_bytes(3, "big")
    content = content[:0x8] + file_length + content[0x8 + 3:]
    return content

def create_data(values, offset_offset):
    data = bytearray()
    pointers = {}
    for i in range(len(values)):
        offsets = pointers.pop(i, None)
        if offsets:
            for offset in offsets:
                data[offset:offset + 3] = (len(data) + offset_offset).to_bytes(3, "big")
        for j in values[i][0]:
            if type(j) == bytes:
                data.extend(j)
            elif type(j) == tuple:
                s = j[0] # Global
                o = j[1] # Offset
                ci = len(data)
                if not s:
                    data.extend((ci + o + offset_offset).to_bytes(3))
                    continue
                o += i
                data.extend(b"\xA5" * 3)
                if pointers.get(o, None) is None: pointers[o] = []
                pointers[o].append(ci)
            else:
                raise Exception("Invalid data!")
    values = parse_data(bytes(data), offset_offset)
    for k,v in pointers:
        for target in v:
            data[target:target + 3] = values[k][1].to_bytes(3, "big")
    return bytes(data)



def create_content(offsets, values):
    header_size = 30
    this_header_size = len(offsets) * 3 + header_size
    data = create_data(values, this_header_size)
    content = bytearray()
    content.extend([0x48, 0x69, 0x6D, 0x61, 0x75, 0x72, 0x69, 0x00])
    content.extend((len(data) + len(offsets) * 3 + header_size).to_bytes(3, "big"))
    content.extend([0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1E, 0xFF, 0x00, 0x54, 0xFF, 0x00])
    content.extend((len(offsets) * 3 + header_size).to_bytes(2, "big"))
    content.extend([0x05, 0x10, 0xFF])
    content.extend(len(offsets).to_bytes(2, "big"))

    content.extend(create_offsets(offsets))

    content.extend(data)

    return bytes(content)

def split_content(content):
    beginning_data = int.from_bytes(content[0x17:0x17 + 2], "big")
    return content[:beginning_data], content[beginning_data:], beginning_data

def parse_data(data, offset_offset):
    if not data.startswith(b"\x0a\x0d"):
        raise Exception("Invalid start for data")
    entries = []
    index = 0
    ol = len(data)
    while index < ol:
        try:
            length = data.index(b"\x0a\x0d", 2)
        except ValueError:
            length = -1
        if length == -1:
            entry = [[data], index + offset_offset]
            entries.append(entry)
            break
        entry = [[data[:length]], index + offset_offset]
        data = data[length:]
        index += length
        entries.append(entry)
    return entries

def get_id(data):
    if not data[0].startswith(b"\x0a\x0d"):
        raise Exception("Invalid start of packet.")
    return data[0][2]

def add_pointers(values):
    segment_offsets = get_segment_offsets(values)
    segment_offsets_lookup = {}
    for i in range(len(segment_offsets)): segment_offsets_lookup[segment_offsets[i]] = i

    for i in range(len(values)):
        current = values[i][0]
        orig = current[0]
        match get_id(current):
            case 0x36:
                if current[0].startswith(b"\x0A\x0D\x36\xFF\x02\x05\xFF\x00\x15\x00\xFF\x03\x1A\x0E\x03\xE8\x52\xFF"):
                    current[0] = current[0][:-3]
                    current.append((True, 2))
                if current[0].startswith(b"\x0A\x0D\x36\xFF\x02\x05\xFF\x00\x04"):
                    current[0] = current[0][:-3]
                    offset = int.from_bytes(orig[-3:], "big")
                    #print(segment_offsets_lookup[offset] - i)
                    current.append((True, segment_offsets_lookup[offset] - i))
            case 0x34:
                if current[0].startswith(b"\x0A\x0D\x34\xFF\x02\x02\xFF\x00"):
                    current[0] = b"\x0A\x0D\x34\xFF\x02\x02\xFF\x00"
                    j = 0
                    while True:
                        current.append(b"\x03\x10")
                        current.append(bytes([j + 1]))
                        current.append(b"\x50\xFF")
                        current.append((False, 14))
                        current.append(b"\x00\x3F\x02")
                        current.append(bytes([orig[8 + j * 19 + 11]])) # Does this just always work or break something?
                        current.append(b"\x01\x40\xFF\x04")
                        offset = int.from_bytes(orig[8 + j * 19 + 16:8 + j * 19 + 16 + 3], "big")
                        current.append((True, segment_offsets_lookup[offset] - i))
                        j += 1
                        if j > 2: break

    return values

def main(prefix = None):
    while True:
        file_path = "701.him"
        #file_path = input("Enter the path to your binary file: ")  # Prompt for file path
        if prefix:
            file_path = os.path.join(prefix, file_path)
        if not os.path.isfile(file_path):
            print("The specified file does not exist, please check the path and try again.")
            continue
        break

    with open(file_path, "rb") as f:
        content = f.read()

    headers, data, header_size = split_content(content)
    values = parse_data(data, header_size)
    values = add_pointers(values)

    strings = extract_strings(values)

    string_object = []
    for i in range(len(strings)):
        try:
            decoded = strings[i][1].decode("shift-jis")
        except UnicodeDecodeError:
            continue
        string_object.append([i, strings[i][0], decoded])

    if len(input("Export?: ")) > 0:
        with open("strings", "w") as f: f.write(json.dumps(string_object, ensure_ascii=False))

    if len(input("Import?: ")) > 0:
        with open("strings", "r") as f: string_object = json.loads(f.read())
        for i in string_object:
            strings[i[0]] = [i[1], i[2].encode("shift-jis")]
    else:
        print("Quitting.")
        return

    values = update_data_with_new_strings(values, strings)

    offsets = parse_offsets(values)
    orig_offsets_count = len(get_offsets(headers))
    new_offset_count = len(offsets)
    if orig_offsets_count != new_offset_count:
        print("Warning: Changing amount of offsets.")
    content = create_content(offsets, values)


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

def extract_strings(data):
    strings = []
    for i in data:
        if i[0][0].startswith(b"\x0A\x0D\x34\xFF\x02\x01\xFF\x01"):
            strings.append(i)
        if get_id(i[0]) == 0x33:
            strings.append(i)
    new_strings = []

    for current in strings:
        # if len(current) < 2:
        #     continue
        value = current[0][0]
        if get_id(current[0]) == 0x33:
            value = value[value.index(b"\\n") + 2:]
            value = value[:value.index(b"\x00")]
            value = [0, value]
        else:
            value = value[value.index(b"\x01\xff\x01") + 3:]
            value = value[:value.index(b"\x00")]
            value = [1, value]
        new_strings.append(value)

    return new_strings

def update_data_with_new_strings(data, new_strings):
    offsets = {}
    new_string = new_strings.pop(0)
    for i in range(len(data)):
        current = data[i][0]
        value = current[0]
        orig_len = len(value)
        if new_string[0] == 0 and get_id(current) == 0x33:

            start = value.index(b"\\n", 1) + 2
            end = value.index(b"\x00", start)

            value = value[:start] + new_string + value[end:]
            new_len = len(value)
            data[i][0][0] = value
            offsets[i] = new_len - orig_len

            new_string = new_strings.pop(0)
        elif new_string[0] == 1 and current[0].startswith(b"\x0A\x0D\x34\xFF\x02\x01\xFF\x01"):

            start = value.index(b"\x01\xff\x01") + 3
            end = value.index(b"\x00", start)

            value = value[:start] + new_string + value[end:]
            new_len = len(value)
            data[i][0][0] = value
            offsets[i] = new_len - orig_len

            new_string = new_strings.pop(0)
    amount = 0
    for i in range(len(data)):
        data[i][1] += amount
        amount += offsets.get(i, 0)
    return data


if __name__ == "__main__":
    main()