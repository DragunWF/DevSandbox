import os
import shutil
from rich import print

save_location = r"E:\Steam\userdata\240879930\1446780\remote\win64_save"
backup_location = r"E:\Backup\Monster-Hunter-Rise\Save-Files"


def copy_files(dir: str, files: list) -> None:
    print()
    for save_file in files:
        save_file_location = f"{save_location}\\{save_file}"
        new_backup_location = f"{dir}\\{save_file}"
        shutil.copyfile(save_file_location, new_backup_location)
        print(f"Copying {save_file_location} to {new_backup_location}\n")


def ordinal_place(num: int) -> str:
    last_place = str(num)[-1]
    if last_place == "1":
        return "st"
    elif last_place == "2":
        return "nd"
    elif last_place == "3":
        return "rd"
    return "th"


def main() -> None:
    save_files = os.listdir(save_location)
    backup_count = len(os.listdir(backup_location)) + 1

    backup_dir_name = f"Backup-{backup_count}"
    new_backup_location = f"{backup_location}\\{backup_dir_name}"

    os.makedirs(new_backup_location)
    copy_files(new_backup_location, save_files)
    backup_place = f"{backup_count}{ordinal_place(backup_count)}"
    print(f"The {backup_place} backup has been created!\n")


if __name__ == "__main__":
    main()
