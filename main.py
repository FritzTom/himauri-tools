
from fushigi import *
import editor, os

def main():
    temp_folder = "temp"
    main_file_path = "natsuscn.hxp"

    util.clear_dir_contents(temp_folder)

    with open(main_file_path, "rb") as main_file:
        file_format, metadata = parser.file_info(main_file)

        if file_format == 'Him4':
            for index, offset in enumerate(metadata):
                unpacker.him4(offset, main_file, temp_folder, index)
        elif file_format == 'Him5':
            for metadata_folders in metadata:
                for file in metadata_folders['files']:
                    unpacker.him5(file, main_file, temp_folder)
        else:
            print("Unknown file format!")
            exit(1)

    [print(i) for i in os.listdir(temp_folder)]
    editor.main(temp_folder)

    os.remove(main_file_path)

    content = sorted([os.path.join(temp_folder, f) for f in os.listdir(temp_folder) if os.path.isfile(os.path.join(temp_folder, f))])

    if not content:
        print("A error occurred, no files to be repacked could be found")
        exit(1)

    repacker.him5(content, main_file_path)

    print("Successfully repacked files.")





if __name__ == "__main__": main()
