import ctypes
import ctypes.wintypes
import logging

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
    logger.info("DLL details:")
    logger.info(f"DLL object: {dll_obj}")
    logger.info(f"DLL type: {type(dll_obj)}")
    logger.info(f"DLL dir: {dir(dll_obj)}")
    logger.info(f"DLL vars: {vars(dll_obj)}")
    logger.info(f"DLL __sizeof__: {dll_obj.__sizeof__()}")

    logger.info("Enumerating DLL exports:")
    
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
            logger.info("No export directory found.")
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
            
            logger.info(f"Function: {func_name}, Address: {hex(func_addr)}")
            
            # Try to get function signature
            try:
                func = getattr(dll_obj, func_name)
                arg_types = getattr(func, 'argtypes', None)
                res_type = getattr(func, 'restype', None)
                logger.info(f"  Signature: args={arg_types}, restype={res_type}")
            except Exception as e:
                logger.warning(f"  Error getting function signature: {str(e)}")

    except Exception as e:
        logger.error(f"Error enumerating DLL exports: {str(e)}")
