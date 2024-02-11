import os
import sys

username = os.environ.get("USERNAME")
desktop_dir = f"/Users/{username}/Desktop"
image_dir = f"/Users/{username}/Pictures/Images"
mode = sys.argv[1].lower()


def main() -> None:
    if mode == "move":
        print("\nMoving files...\n")
    elif mode == "delete":
        print("\nDeleting files\n")
    else:
        raise Exception("Invalid mode!")
    
    image_files = get_images(desktop_dir)
    for file in image_files:
        if mode == "move":
            print(f'Moving "{file}" to "{image_dir}"')
            move_file(f"{desktop_dir}/{file}",
                    f"{image_dir}/{file}")
        else:
            print(f'Deleting "{file}"')
            delete_file(f"{desktop_dir}/{file}")

    modified = len(image_files)
    if modified:
        file_word = "files" if modified > 1 else "file"
        print(f"\n{modified} {file_word} have been {mode}d!\n")
    else:
        print(f"There are no image files to {mode}!\n")


def get_images(directory: str) -> list:
    output = []
    files = os.listdir(directory)
    image_extensions = ("png", "jpg", "webp", "jpeg")
    for file in files:
        file_extension = file.split(".")[-1].lower()
        if file_extension in image_extensions:
            output.append(file)
    return output


def delete_file(location: str) -> None:
    os.remove(location)


def move_file(old_location: str, new_location: str) -> None:
    os.rename(old_location, new_location)


if __name__ == "__main__":
    main()
