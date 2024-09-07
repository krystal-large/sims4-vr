import traceback
import sys
from Utility.helpers_compile import compile_src
from settings import mods_folder, src_path, creator_name, build_path, project_name
import shutil
import os

def dprnt(message):
    print(message)
    with open("compile_log.txt", "a") as log_file:
        log_file.write(message + "\n")

try:
    dprnt("Starting compilation process...")
    compile_src(creator_name, src_path, build_path, mods_folder, project_name)
    dprnt("Compilation completed successfully.")

    dprnt("Copying DLL files...")
    dll_files = ['s4vrlib.dll', 'openvr_api.dll']
    for dll in dll_files:
        source = os.path.join('assets', dll)
        destination = os.path.join('build', dll)
        if os.path.exists(source):
            shutil.copyfile(source, destination)
            dprnt(f"Copied {dll} to build directory.")
        else:
            dprnt(f"Warning: {dll} not found in assets directory.")

    dprnt("Executing sync_packages.py...")
    exec(open("sync_packages.py").read())
    dprnt("sync_packages.py executed successfully.")

    dprnt("Executing bundle_build.py...")
    exec(open("bundle_build.py").read())
    dprnt("bundle_build.py executed successfully.")

    dprnt("Compilation process completed without errors.")
except Exception as e:
    error_msg = f"An error occurred: {str(e)}\n"
    error_msg += "Traceback:\n"
    error_msg += traceback.format_exc()
    dprnt(error_msg)
    sys.exit(1)