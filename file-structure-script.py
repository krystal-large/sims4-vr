"""

Unpacks and prints the current working directory's file structure, going through each folder.

Command to run:
`python3 file-structure-script.py | tee file-structure.md`

"""


import os

def print_directory_structure(startpath): 
    for root, dirs, files in os.walk(startpath):
        
        # Skip the .git folder
        if '.git' in dirs:
            dirs.remove('.git')
        if 'env' in dirs:
            dirs.remove('env')

        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")
    print("\nFile structure:")
    print_directory_structure(current_directory)
