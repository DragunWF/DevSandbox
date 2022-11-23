import os

username = "dragunwf"
desktop_dir = f"/Users/{username}/Desktop"
image_dir = f"/Users/{username}/Pictures/Images"


def main():
    print("\nMoving files...\n")
    image_files = get_images(desktop_dir)
    for file in image_files:
        print(f'Moving "{file}" to "{image_dir}"')
        move_file(f"{desktop_dir}/{file}",
                  f"{image_dir}/{file}")

    files_moved = len(image_files)
    if files_moved:
        file_word = "files" if files_moved > 1 else "file"
        print(f"\n{files_moved} {file_word} have been moved!\n")
    else:
        print("There are no image files to move!\n")


def get_images(directory: str) -> list:
    output = []
    files = os.listdir(directory)
    image_extensions = ("png", "jpg", "webp")
    for file in files:
        cog = file.split(".")
        if cog[-1] in image_extensions:
            output.append(file)
    return output


def move_file(old_location: str, new_location: str):
    os.rename(old_location, new_location)


if __name__ == "__main__":
    main()
