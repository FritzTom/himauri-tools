
import os


def extract_text_between_bytes(content):
    start_bytes = b"\xff\x01\x00\x01"
    header_end_bytes = b"\x5c\x6e"
    # start_bytes = bytes([0xFF, 0x01, 0x00, 0x01, 0x5C, 0x6E])
    end_bytes = bytes([0x00, 0x00, 0x0A, 0x0D])
    
    extracted_texts = []
    positions = []
    names = []

        
    start_index = 0
    while True:
        start_index = content.find(start_bytes, start_index)
        if start_index == -1:
            break
        start_index += len(start_bytes)
        new_start_index = content.find(header_end_bytes, start_index)
        if new_start_index == -1:
            break
        name = content[start_index:new_start_index]
        start_index = new_start_index

        start_index += len(header_end_bytes)
        end_index = content.find(end_bytes, start_index)
        if end_index == -1:
            break

        names.append(name.decode('shift_jis'))
        extracted_text = content[start_index:end_index]
        extracted_texts.append(extracted_text.decode('shift_jis', errors='ignore'))
        positions.append((start_index, end_index))
        start_index = end_index + len(end_bytes)

    return extracted_texts, positions, names

def edit_texts(texts, positions, names):
    print("Extracted Texts:")
    for i, text in enumerate(texts):
        print(f"{i} <{hex(positions[i][0])} ({positions[i][0]})>: {('<' + names[i] + '>') if names[i] else ''} {text}")

    choice = input("Enter the number of the text you want to edit (or 'q' to quit): ")
    if choice.lower() == 'q':
        return None

    try:
        index = int(choice)
        if 0 <= index < len(texts):
            new_text = input("Enter the new text: ")
            return index, new_text
    except (ValueError, IndexError):
        print("Invalid choice.")
    
    return None

def update_string(content, extracted_texts, positions, index, new_text, names):
    old_positions = positions[index]
    old_offset = old_positions[0]
    old_length = old_positions[1] - old_positions[0]
    new_text_encoded = new_text.encode("shift_jis", errors='ignore')
    new_length = len(new_text_encoded)
    offset_offset = new_length - old_length
    contents_view = bytearray(content)

    file_length = int.from_bytes(content[0x8:0x8 + 3], "big")
    if file_length != len(content):
        print("Invalid file length!")
        exit(1)
    file_length = file_length + offset_offset
    file_length = file_length.to_bytes(3, "big")
    contents_view[0x8:0x8 + 3] = file_length

    scenario_data_offset = int.from_bytes(content[0x17:0x17 + 2], "big")

    number_offsets = content[0x1c:0x1c + 2]
    number_offsets = int.from_bytes(number_offsets, "big")

    string_offsets_raw = content[0x1e:scenario_data_offset]
    if len(string_offsets_raw) % 3 != 0:
        print("String offset misalignment!")
        exit(1)

    string_offsets = []
    for i in range(len(string_offsets_raw) // 3):
        string_offsets.append(int.from_bytes(string_offsets_raw[i * 3:(i + 1) * 3], "big"))

    if len(string_offsets) != number_offsets:
        print("Incorrect number of offsets!")
        exit(1)

    print(f"Found {number_offsets} offsets total.")

    string_offsets_mapping = get_string_offset_mapping(string_offsets, positions, extracted_texts, names)

    string_offsets.reverse()

    changed_offsets = []
    changed_string_index = -1

    for i in range(len(string_offsets)):
        current = string_offsets[i]
        if current < old_offset:
            changed_string_index = number_offsets - i - 1
            break
        string_offsets[i] += offset_offset
        changed_offsets.append(number_offsets - i - 1)

    string_offsets.reverse()

    for i in range(len(string_offsets)):
        current_text = string_offsets_mapping.get(string_offsets[i] - (offset_offset if i in changed_offsets else 0), "")

        print(f"{('Name: ' + current_text[1] + ', ') if current_text else ''}{string_offsets[i] - (offset_offset if i in changed_offsets else 0)}\
{(' -> ' + str(string_offsets[i])) if i in changed_offsets else ''} ({i})\
{(' : ' + current_text[0]) if current_text else ''}{(' -> ' + new_text) if changed_string_index == i else ''}")


    string_offsets_raw = b''

    for i in string_offsets:
        string_offsets_raw = string_offsets_raw + i.to_bytes(3, "big")

    contents_view[0x1e:scenario_data_offset] = string_offsets_raw

    content = bytes(contents_view)

    content = content[:old_offset] + new_text_encoded + content[old_offset + old_length:]

    return content

def get_string_offset_mapping(offsets, string_offsets, extracted_strings, names):
    mapping = {}
    for i in range(len(offsets)):
        current_offset = offsets[i]
        next_offset = 999999999
        if (i + 1) < len(offsets): next_offset = offsets[i + 1]
        for j in range(len(string_offsets)):
            current_string = string_offsets[j][0]
            if current_offset <= current_string < next_offset:
                mapping[current_offset] = (extracted_strings[j], names[j])

    return mapping

def main(prefix = None):
    while True:
        file_path = input("Enter the path to your binary file: ")  # Prompt for file path
        if prefix:
            file_path = os.path.join(prefix, file_path)
        if not os.path.isfile(file_path):
            print("The specified file does not exist. Please check the path and try again.")
            continue

        with open(file_path, "rb") as f:
            content = f.read()

        extracted_texts, positions, names = extract_text_between_bytes(content)

        if not extracted_texts:
            print("No text found between the specified byte sequences. (No text in this file?)")
            continue
        break


    while True:
        new_text_info = edit_texts(extracted_texts, positions, names)
        if new_text_info is None:
            break
        
        index, new_text = new_text_info

        content = update_string(content, extracted_texts, positions, index, new_text, names)

        extracted_texts, positions, names = extract_text_between_bytes(content)

    with open(file_path, "wb") as f:
        f.write(content)

    print("Changes saved.")

if __name__ == "__main__":
    main()