import shutil
import os
from pathlib import Path

def get_safe_destination(target_path: Path) -> Path:
    
    # I do this so the program doesn't accidentally overwrite files if two share the same name
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1
    
    # i just keep incrementing a number at the end of the filename until an empty slot is found
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def clean_empty_folders(path: Path):
    
    # moving files leaves behind a mess of empty directories, so I clean them up to keep the filesystem tidy
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        current_dir = Path(dirpath)
        if current_dir != path: 
            try:
                # I ignore errors here because the os sometimes throws unecessary errors if we try to delete a folder that still has hidden stuff in it
                current_dir.rmdir()
            except OSError:
                pass 

def move_file(file_path: Path, target_folder: Path):
    # i centralize the moving logic here so if the system denies access, the whole app doesn't crash
    try:
        target_folder.mkdir(parents=True, exist_ok=True)
        destination = get_safe_destination(target_folder / file_path.name)
        shutil.move(str(file_path), str(destination))
        return True
    except Exception:
        return False