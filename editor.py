
import os

DEBUG = False

def get_string_offsets_between_bytes(content, headers):
    # start_bytes = b"\xff\x01\x00\x01"
    # header_end_bytes = b"\x5c\x6e"
    # start_bytes = bytes([0xFF, 0x01, 0x00, 0x01, 0x5C, 0x6E])
    # end_bytes = bytes([0x00, 0x00, 0x0A, 0x0D])
    
    positions = []

    start_index = 0
    while len(headers) > 0:
        current_header = headers.pop(0)
        new_start_index = content.find(current_header, start_index)
        if new_start_index == -1:
            return positions
        if start_index != 0:
            positions.append((start_index, new_start_index - start_index))
        new_start_index += len(current_header)
        start_index = new_start_index

    return positions

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
    with open("exported", "r") as f:
        data = f.read()
    data = data.split(";B;\n")
    values = []
    for i in range(len(data)):
        if i != int(data[i].split(": ", 1)[0]):
            print("Improperly ordered file.\nAborting!")
            exit(1)
            #values.append([])
            #continue
        values.append([])
        current_values = data[i].split(": ", 1)[1]
        if ";A;" in current_values:
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

def get_offsets(content):
    file_length = int.from_bytes(content[0x8:0x8 + 3], "big")
    if file_length != len(content):
        print("Invalid file length!")
        exit(1)

    scenario_data_offset = int.from_bytes(content[0x17:0x17 + 2], "big")

    number_offsets = content[0x1c:0x1c + 2]
    number_offsets = int.from_bytes(number_offsets, "big")

    string_offsets_raw = content[0x1e:scenario_data_offset]
    if len(string_offsets_raw) % 3 != 0:
        print("Offset misalignment!")
        exit(1)

    offsets = []
    for i in range(len(string_offsets_raw) // 3):
        offsets.append(int.from_bytes(string_offsets_raw[i * 3:(i + 1) * 3], "big"))

    if len(offsets) != number_offsets:
        print("Incorrect number of offsets!")
        exit(1)

    print(f"Found {number_offsets} offsets total.")

    offset_values = []
    if len(offsets) > 0:
        for i in range(len(offsets) - 1):
            offset_values.append(content[offsets[i]:offsets[i + 1]])
        offset_values.append(content[offsets[-1]:file_length - 1])

    return offsets, offset_values, scenario_data_offset - 0x1e

def update_value(content, index, new_value):
    offsets, string_offsets_values, string_offsets_length = get_offsets(content)

    old_offset = offsets[index]
    # Length is till next offset or if there is no next offset till end of file - 1 (last byte of file is static, thanks xor (dc user id 1091741505049350226))
    old_length = (offsets[index + 1] if len(offsets) > (index + 1) else len(content) - 1) - old_offset
    new_length = len(new_value)
    offset_offset = new_length - old_length

    # Create bytearray which will be updated to have the new value
    contents_view = bytearray(content)

    # Update (and write) file length
    file_length = int.from_bytes(content[0x8:0x8 + 3], "big")
    if file_length != len(content):
        print("Invalid file length!")
        exit(1)
    file_length = file_length + offset_offset
    file_length = file_length.to_bytes(3, "big")
    contents_view[0x8:0x8 + 3] = file_length

    # Update data offsets
    offsets.reverse()
    for i in range(len(offsets)):
        current = offsets[i]
        if current == old_offset:
            break
        offsets[i] += offset_offset
    offsets.reverse()

    # Write updated data offsets
    offsets_encoded = b''
    for i in offsets:
        offsets_encoded = offsets_encoded + i.to_bytes(3, "big")
    contents_view[0x1e:0x1e + string_offsets_length] = offsets_encoded

    # Replace value
    contents_view[old_offset:old_offset + old_length] = new_value

    content = bytes(contents_view)
    return content

# def print_useful_info(string_offsets, positions, extracted_texts, names, offset_offset, new_text, update_name, changed_offsets, changed_string_index):
#     string_offsets_mapping = get_string_offset_mapping(string_offsets, positions, extracted_texts, names)
#
#     for i in range(len(string_offsets)):
#         current_text = string_offsets_mapping.get(string_offsets[i] - (offset_offset if i in changed_offsets else 0), "")
#
#         print(f"{string_offsets[i] - (offset_offset if i in changed_offsets else 0)}\
# {(' -> ' + str(string_offsets[i])) if i in changed_offsets else ''} ({i}) \
# {('Name: ' + current_text[1]) if (current_text and current_text[1]) else ''}\
# {(': ' + current_text[0]) if current_text else ''}{(' -> ' + new_text) if changed_string_index == i else ''}{' NAME UPDATE!' if update_name and changed_string_index == i else ''}")

def get_strings(content):
    offsets, offset_values, offsets_length = get_offsets(content)

    # b"\x0a\x0d"
    # 33 ff xx xx ff xx xx ff 01 00 01
    headers =[b"\xff\x01\x00\x01", b"\x5c\x6e", b"\x00\x00"]
    #choice_headers = [b"\x34\xFF\x02\x01\xFF\x01", b"\x00\x02\x01\xff\x00"]

    all_fixed_string_offsets = []
    all_relative_string_offsets = []
    for i in range(len(offsets)):
        string_offsets = get_string_offsets_between_bytes(offset_values[i], [i for i in headers])
        all_relative_string_offsets.append(string_offsets)
        fixed_string_offsets = []
        for j in string_offsets:
            fixed_string_offsets.append((j[0] + offsets[i], j[1]))
        all_fixed_string_offsets.append(fixed_string_offsets)

    strings = []
    for i in all_fixed_string_offsets:
        strings.append([])
        for j in i:
            strings[-1].append(content[j[0]:j[0] + j[1]])

    return all_fixed_string_offsets, all_relative_string_offsets, strings

def parse_pattern(value, pattern):
    found = []
    for i in pattern:
        match pattern[0]:
            case 0:
                c, value = value[:len(i[1])], value[len(i[1]):]
                if c != i[1]:
                    return False, found
            case 1:
                c, value = value[:i[1]], value[i[1]:]
                found.append(c)
            case 2:
                e = i[1]
                l = -1
                if len(i[1]) > 1: l = i[1][1]
                cf = b""
                c, value = value[0], value[1:]
                i = 0
                while (c != e) and ((l == -1) or (l > i)):
                    i += 1
                    cf = cf + bytes([c])
                    c, value = value[0], value[1:]


    return True, found

def create_pattern(*pattern):
    constructed_pattern = []
    for i in pattern:
        match type(i):
            case "bytes":
                constructed_pattern.append((0, i))
            case "int":
                constructed_pattern.append((1, i))
            case "tuple":
                constructed_pattern.append((2, i))
    return constructed_pattern




def main(prefix = None):
    while True:
        file_path = input("Enter the path to your binary file: ")  # Prompt for file path
        if prefix:
            file_path = os.path.join(prefix, file_path)
        if not os.path.isfile(file_path):
            print("The specified file does not exist, please check the path and try again.")
            continue

        with open(file_path, "rb") as f:
            content = f.read()

        fixed_string_offsets, relative_string_offsets, strings = get_strings(content)

        if len(strings) < 1:
            print("No text found between the specified byte sequences. (No text in this file?)")
            continue
        break


    while True:
        new_strings = ex_import_texts(strings, None, True)
        if new_strings is None:
            break


        for i in range(len(strings)):
            for j in range(len(new_strings[i])):
                if strings[i][j] != new_strings[i][j]:
                    offsets, offset_values, offsets_length = get_offsets(content)
                    fixed_string_offsets, relative_string_offsets, strings = get_strings(content)
                    value = offset_values[i]
                    value = value[:relative_string_offsets[i][j][0]] + new_strings[i][j] + value[relative_string_offsets[i][j][0] + relative_string_offsets[i][j][1]:]
                    content = update_value(content, i, value)

    print("Quitting.")

    with open(file_path, "wb") as f:
        f.write(content)

    print("Changes saved to sub file.")

if __name__ == "__main__":
    main()