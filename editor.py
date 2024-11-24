import os

def extract_text_between_bytes(content):
    start_bytes = bytes([0xFF, 0x01, 0x00, 0x01, 0x5C, 0x6E])
    end_bytes = bytes([0x00, 0x00, 0x0A, 0x0D])
    
    extracted_texts = []
    positions = []

        
    start_index = 0
    while True:
        start_index = content.find(start_bytes, start_index)
        if start_index == -1:
            break

        start_index += len(start_bytes)
        end_index = content.find(end_bytes, start_index)
        if end_index == -1:
            break

        extracted_text = content[start_index:end_index]
        extracted_texts.append(extracted_text.decode('shift_jis', errors='ignore'))
        positions.append((start_index, end_index))
        start_index = end_index + len(end_bytes)

    return extracted_texts, positions

def edit_texts(texts, positions):
    print("Extracted Texts:")
    for i, text in enumerate(texts):
        print(f"{i + 1} <{hex(positions[i][0])} ({positions[i][0]})>: {text}")

    choice = input("Enter the number of the text you want to edit (or 'q' to quit): ")
    if choice.lower() == 'q':
        return None

    try:
        index = int(choice) - 1
        if 0 <= index < len(texts):
            new_text = input("Enter the new text: ")
            return index, new_text
    except (ValueError, IndexError):
        print("Invalid choice.")
    
    return None

def write_changes(file_path, positions, new_texts):
    with open(file_path, 'rb+') as file:
        content = file.read()
        for (index, new_text), (start_index, end_index) in zip(new_texts, positions):
            # Replace the old text with the new text
            content = content[:start_index] + new_text + content[end_index:]
        
        file.seek(0)
        file.write(content)
        file.truncate()  # Ensure the file is not longer than the new content


def update_string(content, extracted_texts, positions, index, new_text):
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
    print(string_offsets)

    if len(string_offsets) != number_offsets:
        print("Incorrect number of offsets!")
        exit(1)

    string_offsets.reverse()

    for i in range(len(string_offsets)):
        current = string_offsets[i]
        if current < old_offset:
            break
        string_offsets[i] += offset_offset

    string_offsets.reverse()

    string_offsets_raw = b''

    for i in string_offsets:
        string_offsets_raw = string_offsets_raw + i.to_bytes(3, "big")

    contents_view[0x1e:scenario_data_offset] = string_offsets_raw

    content = bytes(contents_view)

    content = content[:old_offset] + new_text_encoded + content[old_offset + old_length:]

    return content


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

        extracted_texts, positions = extract_text_between_bytes(content)

        if not extracted_texts:
            print("No text found between the specified byte sequences. (No text in this file?)")
            continue
        break


    while True:
        new_text_info = edit_texts(extracted_texts, positions)
        if new_text_info is None:
            break
        
        index, new_text = new_text_info

        content = update_string(content, extracted_texts, positions, index, new_text)

        extracted_texts, positions = extract_text_between_bytes(content)

    with open(file_path, "wb") as f:
        f.write(content)

    print("Changes saved.")

if __name__ == "__main__":
    main()