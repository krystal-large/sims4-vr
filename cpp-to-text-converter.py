import os
import chardet
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def convert_cpp_to_text(input_file, output_file):
    try:
        logging.info(f"Attempting to convert {input_file}")
        encoding = detect_encoding(input_file)
        logging.debug(f"Detected encoding: {encoding}")
        
        with open(input_file, 'r', encoding=encoding) as infile:
            content = infile.read()
        
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(content)
        
        logging.info(f"Successfully converted {input_file} to {output_file}")
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")

def main(cpp_files, output_directory):
    root_directory = os.getcwd()
    logging.info(f"Root directory: {root_directory}")
    logging.info(f"Output directory: {output_directory}")

    os.makedirs(output_directory, exist_ok=True)
    logging.info(f"Ensured output directory exists: {output_directory}")

    for relative_path in cpp_files:
        input_file = os.path.normpath(os.path.join(root_directory, relative_path))
        logging.debug(f"Constructed input file path: {input_file}")
        
        if os.path.exists(input_file):
            logging.debug(f"File exists: {input_file}")
            if input_file.endswith(".cpp"):
                base_name = os.path.basename(input_file)
                # Change this line to keep the .cpp extension
                output_file = os.path.join(output_directory, base_name + ".txt")
                logging.debug(f"Constructed output file path: {output_file}")
                convert_cpp_to_text(input_file, output_file)
            else:
                logging.warning(f"Skipping {input_file}: Not a .cpp file")
        else:
            logging.error(f"File not found: {input_file}")
            logging.debug(f"Current working directory: {os.getcwd()}")
            try:
                parent_dir = os.path.dirname(input_file)
                if os.path.exists(parent_dir):
                    logging.debug(f"Parent directory contents: {os.listdir(parent_dir)}")
                else:
                    logging.error(f"Parent directory does not exist: {parent_dir}")
            except Exception as e:
                logging.error(f"Error accessing parent directory: {str(e)}")

if __name__ == "__main__":
    cpp_files = [
        "src/vrdll/vrdll/dllmain.cpp",
        "src/vrdll/vrdll/OpenVR-DirectMode.cpp",
        # Add more file paths as needed
    ]
    
    output_directory = "./docs/explore-files"

    main(cpp_files, output_directory)