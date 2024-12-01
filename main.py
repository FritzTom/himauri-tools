
from fushigi import *
import editor, os

DEV_MODE = True

def main():
    temp_folder = "temp"
    main_file_path = "natsuscn.hxp"
    if not DEV_MODE or len(input("Extract?: ")) > 0:
        extract_file(main_file_path, temp_folder)

    [print(i) for i in os.listdir(temp_folder)]
    editor.main(temp_folder)

    if not DEV_MODE or len(input("Pack?: ")) > 0:
        pack_file(temp_folder, main_file_path)


def extract_file(file_path, destination):
    util.clear_dir_contents(destination)

    with open(file_path, "rb") as main_file:
        file_format, metadata = parser.file_info(main_file)

        if file_format == 'Him4':
            for index, offset in enumerate(metadata):
                unpacker.him4(offset, main_file, destination, index)
        elif file_format == 'Him5':
            for metadata_folders in metadata:
                for file in metadata_folders['files']:
                    unpacker.him5(file, main_file, destination)
        else:
            print("Unknown file format!")
            exit(1)

def pack_file(source, file_path):
    os.remove(file_path)
    content = sorted([os.path.join(source, f) for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))])

    if not content:
        print("A error occurred, no files to be repacked could be found")
        exit(1)

    repacker.him5(content, file_path)

    print("Successfully repacked files.")





if __name__ == "__main__": main()
