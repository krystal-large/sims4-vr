import ctypes
import ctypes.wintypes
import logging
import sys
import os
import inspect
import importlib
import platform
import dis
import types
import zipfile
import io



# Windows API definitions
LPCSTR = ctypes.c_char_p
DWORD = ctypes.wintypes.DWORD
LONG = ctypes.wintypes.LONG
WORD = ctypes.wintypes.WORD
BYTE = ctypes.wintypes.BYTE

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)
    ]

class IMAGE_DOS_HEADER(ctypes.Structure):
    _fields_ = [
        ("e_magic", WORD),
        ("e_cblp", WORD),
        ("e_cp", WORD),
        ("e_crlc", WORD),
        ("e_cparhdr", WORD),
        ("e_minalloc", WORD),
        ("e_maxalloc", WORD),
        ("e_ss", WORD),
        ("e_sp", WORD),
        ("e_csum", WORD),
        ("e_ip", WORD),
        ("e_cs", WORD),
        ("e_lfarlc", WORD),
        ("e_ovno", WORD),
        ("e_res", WORD * 4),
        ("e_oemid", WORD),
        ("e_oeminfo", WORD),
        ("e_res2", WORD * 10),
        ("e_lfanew", LONG)
    ]

class IMAGE_DATA_DIRECTORY(ctypes.Structure):
    _fields_ = [
        ("VirtualAddress", DWORD),
        ("Size", DWORD)
    ]

class IMAGE_OPTIONAL_HEADER64(ctypes.Structure):
    _fields_ = [
        ("Magic", WORD),
        ("MajorLinkerVersion", BYTE),
        ("MinorLinkerVersion", BYTE),
        ("SizeOfCode", DWORD),
        ("SizeOfInitializedData", DWORD),
        ("SizeOfUninitializedData", DWORD),
        ("AddressOfEntryPoint", DWORD),
        ("BaseOfCode", DWORD),
        ("ImageBase", ctypes.c_ulonglong),
        ("SectionAlignment", DWORD),
        ("FileAlignment", DWORD),
        ("MajorOperatingSystemVersion", WORD),
        ("MinorOperatingSystemVersion", WORD),
        ("MajorImageVersion", WORD),
        ("MinorImageVersion", WORD),
        ("MajorSubsystemVersion", WORD),
        ("MinorSubsystemVersion", WORD),
        ("Win32VersionValue", DWORD),
        ("SizeOfImage", DWORD),
        ("SizeOfHeaders", DWORD),
        ("CheckSum", DWORD),
        ("Subsystem", WORD),
        ("DllCharacteristics", WORD),
        ("SizeOfStackReserve", ctypes.c_ulonglong),
        ("SizeOfStackCommit", ctypes.c_ulonglong),
        ("SizeOfHeapReserve", ctypes.c_ulonglong),
        ("SizeOfHeapCommit", ctypes.c_ulonglong),
        ("LoaderFlags", DWORD),
        ("NumberOfRvaAndSizes", DWORD),
        ("DataDirectory", IMAGE_DATA_DIRECTORY * 16)
    ]

class IMAGE_FILE_HEADER(ctypes.Structure):
    _fields_ = [
        ("Machine", WORD),
        ("NumberOfSections", WORD),
        ("TimeDateStamp", DWORD),
        ("PointerToSymbolTable", DWORD),
        ("NumberOfSymbols", DWORD),
        ("SizeOfOptionalHeader", WORD),
        ("Characteristics", WORD)
    ]

class IMAGE_NT_HEADERS64(ctypes.Structure):
    _fields_ = [
        ("Signature", DWORD),
        ("FileHeader", IMAGE_FILE_HEADER),
        ("OptionalHeader", IMAGE_OPTIONAL_HEADER64)
    ]

class IMAGE_EXPORT_DIRECTORY(ctypes.Structure):
    _fields_ = [
        ("Characteristics", DWORD),
        ("TimeDateStamp", DWORD),
        ("MajorVersion", WORD),
        ("MinorVersion", WORD),
        ("Name", DWORD),
        ("Base", DWORD),
        ("NumberOfFunctions", DWORD),
        ("NumberOfNames", DWORD),
        ("AddressOfFunctions", DWORD),
        ("AddressOfNames", DWORD),
        ("AddressOfNameOrdinals", DWORD)
    ]

def log_dll_details(dll_obj, logger):
    """
    Log details of the given DLL, including its exported functions.
    
    :param dll_obj: The loaded DLL object (ctypes.CDLL)
    :param logger: A logging.Logger object to use for logging
    """
    logger.debug("DLL details:")
    logger.debug(f"DLL object: {dll_obj}")
    logger.debug(f"DLL type: {type(dll_obj)}")
    logger.debug(f"DLL dir: {dir(dll_obj)}")
    logger.debug(f"DLL vars: {vars(dll_obj)}")
    logger.debug(f"DLL __sizeof__: {dll_obj.__sizeof__()}")

    logger.debug("Enumerating DLL exports:")
    
    try:
        # Get the base address of the loaded DLL
        base_addr = dll_obj._handle

        # Read the DOS header
        dos_header = IMAGE_DOS_HEADER.from_address(base_addr)
        
        # Read the NT headers
        nt_headers = IMAGE_NT_HEADERS64.from_address(base_addr + dos_header.e_lfanew)
        
        # Get the export directory RVA and size
        export_dir_rva = nt_headers.OptionalHeader.DataDirectory[0].VirtualAddress
        export_dir_size = nt_headers.OptionalHeader.DataDirectory[0].Size
        
        if export_dir_rva == 0:
            logger.debug("No export directory found.")
            return
        
        # Read the export directory
        export_dir = IMAGE_EXPORT_DIRECTORY.from_address(base_addr + export_dir_rva)
        
        # Read the arrays of exported functions
        names_array = (DWORD * export_dir.NumberOfNames).from_address(base_addr + export_dir.AddressOfNames)
        ordinals_array = (WORD * export_dir.NumberOfNames).from_address(base_addr + export_dir.AddressOfNameOrdinals)
        functions_array = (DWORD * export_dir.NumberOfFunctions).from_address(base_addr + export_dir.AddressOfFunctions)
        
        # Enumerate and log the exported functions
        for i in range(export_dir.NumberOfNames):
            name_rva = names_array[i]
            ordinal = ordinals_array[i]
            func_rva = functions_array[ordinal]
            
            func_name = ctypes.string_at(base_addr + name_rva).decode('ascii')
            func_addr = base_addr + func_rva
            
            logger.debug(f"Function: {func_name}, Address: {hex(func_addr)}")
            
            # Try to get function signature
            try:
                func = getattr(dll_obj, func_name)
                arg_types = getattr(func, 'argtypes', None)
                res_type = getattr(func, 'restype', None)
                logger.debug(f"  Signature: args={arg_types}, restype={res_type}")
            except Exception as e:
                logger.warning(f"  Error getting function signature: {str(e)}")

    except Exception as e:
        logger.error(f"Error enumerating DLL exports: {str(e)}")



import zipfile
import io
import sys

def attempt_decompile(filename):
    """
    Attempt to decompile a .pyc file from within a zip archive.
    """
    try:
        # Split the filename into zip path and internal path
        zip_path, internal_path = filename.split('.zip')
        zip_path += '.zip'
        internal_path = internal_path.lstrip('\\/')

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open(internal_path) as pyc_file:
                pyc_contents = pyc_file.read()

        # Now we have the .pyc contents, we can attempt to decompile
        import uncompyle6
        from uncompyle6.main import decompile_bytes

        # Create a string buffer to capture the output
        out = io.StringIO()
        # The first 16 bytes are the .pyc header, which we skip
        decompile_bytes(sys.version_info, pyc_contents[16:], out)
        return out.getvalue()

    except ImportError:
        # If uncompyle6 is not available, fall back to disassembly
        import dis
        import marshal
        import types
        
        # Skip the .pyc header (first 16 bytes)
        code = marshal.loads(pyc_contents[16:])
        return dis.dis(code)

    except Exception as e:
        return f"Error decompiling: {str(e)}"
    


def log_python_environment(logger):
    """
    Log details about the current Python environment using only standard library modules.
    """
    logger.info("Python Environment Details:")
    logger.info(f"Python Executable: {sys.executable}")
    logger.info(f"Python Version: {platform.python_version()}")
    logger.info(f"Python Implementation: {platform.python_implementation()}")
    
    logger.info("Python Path:")
    for path in sys.path:
        logger.info(f"  {path}")
    
    logger.info("Loaded Modules:")
    for name, module in sys.modules.items():
        if module:
            file_path = getattr(module, '__file__', 'Unknown location')
            version = getattr(module, '__version__', 'Unknown version')
            logger.info(f"  {name}: {version} - {file_path}")

def log_module_details(module_name, logger, depth=0, max_depth=3):
    """
    Log details of the specified module, including its submodules and components.
    """
    indent = "  " * depth
    try:
        module = importlib.import_module(module_name)
        logger.info(f"{indent}Module: {module_name}")
        
        # Version
        version = getattr(module, '__version__', 'Version not available')
        logger.info(f"{indent}Version: {version}")
        
        # Help text
        logger.info(f"{indent}Help:")
        help_text = inspect.getdoc(module)
        for line in help_text.split('\n') if help_text else ['No help available']:
            logger.info(f"{indent}  {line}")
        
        # Source file location and content
        try:
            source_file = inspect.getfile(module)
            logger.info(f"{indent}Source file: {source_file}")
            if '.zip' in source_file and source_file.endswith('.pyc'):
                logger.info(f"{indent}Decompiled content:")
                decompiled = attempt_decompile(source_file)
                for line in str(decompiled).split('\n'):
                    logger.info(f"{indent}  {line}")
        except TypeError:
            logger.info(f"{indent}Source file: Built-in module")
        
        # Directory listing
        logger.info(f"{indent}Directory listing:")
        for item in dir(module):
            logger.info(f"{indent}  {item}")
        
        # Submodules and components
        if depth < max_depth:
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj):
                    log_module_details(f"{module_name}.{name}", logger, depth + 1, max_depth)
                elif inspect.isfunction(obj):
                    logger.info(f"{indent}  Function: {name}")
                    signature = inspect.signature(obj)
                    logger.info(f"{indent}    Arguments: {signature}")
                    doc = inspect.getdoc(obj)
                    if doc:
                        logger.info(f"{indent}    Doc: {doc.split()[0]}...")
                elif inspect.isclass(obj):
                    logger.info(f"{indent}  Class: {name}")
                    doc = inspect.getdoc(obj)
                    if doc:
                        logger.info(f"{indent}    Doc: {doc.split()[0]}...")
    
    except ImportError:
        logger.error(f"Could not import module: {module_name}")
    except Exception as e:
        logger.error(f"Error inspecting module {module_name}: {str(e)}")

# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    log_python_environment(logger)
    log_module_details('camera', logger)
    log_module_details('services', logger)
    log_module_details('sims4', logger)