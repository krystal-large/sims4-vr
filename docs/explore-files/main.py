#    Copyright 2020 convexvr
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import camera, services, sims4.commands, os

from server_commands import interaction_commands
import sims4.reload as r
import helpers.injector as injector
import ctypes
import sys
import ctypes.wintypes
from zone import Zone
import math
import helpers.threedmath as threedmath
from ReadWriteMemory import ReadWriteMemory
import pyautogui
import importlib.util
import datetime




class VPXFLOAT3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float)
    ]

class VPXFLOAT4(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float)
    ]

class VPX_CONTROLLER_STATE(ctypes.Structure):
    _fields_ = [
        ("IsActive", ctypes.c_ulong),#VPX_BOOL IsActive;				// VPX_TRUE if active, otherwise VPX_FALSE
        ("StickX", ctypes.c_float),#float StickX;					// Thumbstick/pad x-axis [-1|1]
        ("StickY", ctypes.c_float),#float StickY;					// Thumbstick/pad y-axis [-1|1]
        ("Trigger", ctypes.c_float),#float Trigger;					// Trigger axis [0|1]
        ("Grip", ctypes.c_float),#float Grip;						// Grip axis [0|1], on controllers with a grip button (e.g. Vive wands) either 0.0 or 1.0
        ("Extra0", ctypes.c_float),#float Extra0;					// Extra axis (for future use)
        ("Extra1", ctypes.c_float),#float Extra1;					// Extra axis (for future use)
        ("Extra2", ctypes.c_float),#float Extra2;					// Extra axis (for future use)
        ("Extra3", ctypes.c_float),#float Extra3;					// Extra axis (for future use)
        ("Finger0", ctypes.c_float),#float Finger0;					// Finger axis: thumb (for future use)
        ("Finger1", ctypes.c_float),#float Finger1;					// Finger axis: index (for future use)
        ("Finger2", ctypes.c_float),#float Finger2;					// Finger axis: middle (for future use)
        ("Finger3", ctypes.c_float),#float Finger3;					// Finger axis: ring (for future use)
        ("Finger4", ctypes.c_float),#float Finger4;					// Finger axis: pinky (for future use)
        ("ButtonsPressed", ctypes.c_ulong),#unsigned int ButtonsPressed;	// Check with a flag, e.g.: if (ButtonsPressed & VPX_CONTROLLER_BUTTON_0)
        ("ButtonsTouched", ctypes.c_ulong),#unsigned int ButtonsTouched;	// Check with a flag, e.g.: if (ButtonsTouched & VPX_CONTROLLER_BUTTON_0)
    ]


ModFolder = os.path.dirname(os.path.dirname(__file__))

#Function used to print debug information
def dprnt(txt):
    global ModFolder
    txt=str(txt)
    now = datetime.datetime.now()
    log_str = now.strftime("%Y-%m-%d %H:%M:%S")+": "+txt+"\n"
    file_object = open(ModFolder+"\\debug_log.txt", 'a')
    if file_object:
        file_object.write(log_str)
        file_object.close()

dprnt("module loading initiated")
pid = os.getpid()

#function we need is:
_vpxInit = 0
_vpxFree = 0
_vpxIsActive = 0
_vpxGetFloat = 0
_vpxGetFloat3 = 0
_vpxSetFloat3 = 0
_vpxGetFloat4 = 0
_vpxGetControllerState = 0
_vpxYawCorrection = 0
_vpxGetFuncAddress = 0
vpxGetHeadsetRotationEuler = 0
vpxGetHeadsetPosition = 0

vorpx_loaded = False

vpx_active = 0
headset_position = 0
headset_rotation = 0

game_desired_cam_pos = 0

known_sruct_locations = []
chosen_structs = []

origin_sims_camera_pos = 0
origin_sims_camera_rot = 0
#We know that the sims has filled in our address when it is nolonger 4545
sims_camera_address = ctypes.c_ulonglong(4545)
sims_camera_address_compare = ctypes.c_ulonglong(4646)

Scale_patch_address1 = 0x141010608
Scale_patch_address2 = 0x1410105F5

#code_injection_base_address is the address where we patch the exacutable to change the games behavior 
code_injection_base_address = 0x1401F810E


def find_pach_locations():
    global Scale_patch_address1
    global Scale_patch_address2
    global code_injection_base_address
    global pid
    
    rwm = ReadWriteMemory()
    process = rwm.get_process_by_id(pid)
    process.get_all_access_handle()
    
    
    #Read in loots of memmory so we can search it
    dprnt("Reading memmory")
    mem_search_start_addr = 0x140000000
    memmory = process.readByte2(mem_search_start_addr, 0x144000000-mem_search_start_addr)
    dprnt("Done reading memmory")
    process.close()
    
    #Search for code in the binary that is located where we want to patch the binary
    Scale_patch_address1 = memmory.find(b'\x0f\x11\x91\x80\x00\x00\x00\x41\x0f\x28\xd2\x0f\x14\xd7\xf3\x0f\x59\xf4\x41\x0f\x28\xe3\xf3\x0f\x59\xc5\xf3\x41\x0f\x5e\xe1\x0f', 0)
    if Scale_patch_address1 == -1:
        dprint("could not find Scale_patch_address1")
    Scale_patch_address1 += mem_search_start_addr
    
    Scale_patch_address2 = memmory.find(b'\x0f\x11\x51\x70\x0f\x57\xd2\x0f\x14\xc8\x0f\x28\xc4\x0f\x14\xd1\x0f\x57\xc9\x0f\x11\x91\x80\x00\x00\x00\x41\x0f\x28\xd2\x0f\x14', 0)
    if Scale_patch_address2 == -1:
        dprint("could not find Scale_patch_address2")
    Scale_patch_address2 += mem_search_start_addr
    
    code_injection_base_address = memmory.find(b'\x0f\x11\x41\x30\x0f\x10\x4a\x40\x0f\x11\x49\x40\x0f\x10\x42\x50\x0f\x11\x41\x50\x0f\x10\x4a\x60\x0f\x11\x49\x60\x0f\x10\x42\x70', 0)
    if code_injection_base_address == -1:
        dprint("could not find code_injection_base_address")
    code_injection_base_address += mem_search_start_addr
    
    dprnt("Scale_patch_address1: "+hex(Scale_patch_address1)+" Scale_patch_address2: "+hex(Scale_patch_address2)+" code_injection_base_address: "+hex(code_injection_base_address))
    
    


find_pach_locations()

code_injection_base2_address = code_injection_base_address - 46

#then we get references to the location where we will patch these are locations in the code that i found with cheat engine
first = ctypes.c_ulonglong.from_address(code_injection_base_address)
second = ctypes.c_ulonglong.from_address(code_injection_base_address+8)

headset_offset = sims4.math.Vector3(0, 0, 0)

patch_frame_counter = 0
is_patched = False
patch2_active = False
saved_second = 0
saved_first = 0
hold_b_button_frame_counter = 0
holding_grab = False
holding_trig = False
last_btns_press = 0
scale = 1#1.25

game_camera_scale = 0.905
game_camera_scalew = 0.5

#resolution 768/1024=0.75
game_camera_scale = 0.905
game_camera_scalew = 0.68

#when image zoom is 1.073
game_camera_scale = 0.83
game_camera_scalew = 0.633

#when image zoom is 0.795
game_camera_scale = 1.1298482051491667
game_camera_scalew = 0.8552593232989314

#the quest has 93 deg vertical fov
#game_camera_scale = math.atan(math.radians(93)/2)


#the quest has 96.0160446166992 deg vertical fov according to vorpx
#game_camera_scale = math.atan(math.radians(96.0160446166992)/2)


#game_camera_scale = math.atan(math.radians(136)/2)#But for some reason 136 deg gives better result
#game_camera_scalew = game_camera_scale/(1024/768)

org_code = 4545




def dump_mem():
    global Scale_patch_address1
    global Scale_patch_address2
    global code_injection_base_address
    global pid
    
    patchlocations = [
        Scale_patch_address1, #scaling upp and down
        Scale_patch_address2, #scaling left and right
        code_injection_base_address
    ]
    rwm = ReadWriteMemory()
    process = rwm.get_process_by_id(pid)
    process.get_all_access_handle()
    
    for x, patchlocation in enumerate(patchlocations):
        org_dat = process.readByte(patchlocation, 32)
        dprnt("patchlocation: "+str(x)+"("+hex(patchlocation)+") = "+org_dat.hex())
        
    process.close()

dump_mem()

original_codes = [0,0,0,0,0,0,0,0]

@sims4.commands.Command('scale', command_type=(sims4.commands.CommandType.Live))
def scl(scale_str: str="", _connection=None):
    global scale
    scale = float(scale_str)
    
#Set camera scaling up and down
@sims4.commands.Command('gscale', command_type=(sims4.commands.CommandType.Live))
def gscale(scale_str: str="", _connection=None):
    global game_camera_scale
    global game_camera_scalew
    game_camera_scale = float(scale_str)
    vrdll.set_scale(game_camera_scalew, game_camera_scale)

#Set camera scaling left and right
@sims4.commands.Command('gscalew', command_type=(sims4.commands.CommandType.Live))
def gscalew(scale_str: str="", _connection=None):
    global game_camera_scalew
    global game_camera_scale
    game_camera_scalew = float(scale_str)
    vrdll.set_scale(game_camera_scalew, game_camera_scale)

#prints the scale variables
@sims4.commands.Command('ptscale', command_type=(sims4.commands.CommandType.Live))
def ptscale(_connection=None):
    global game_camera_scalew
    global game_camera_scale
    dprnt("scale: "+str(game_camera_scale)+", "+str(game_camera_scalew))

#Debug: add a render struct address manually
@sims4.commands.Command('addptr', command_type=(sims4.commands.CommandType.Live))
def addptr(ptr: str="", _connection=None):
    global known_sruct_locations
    known_sruct_locations.append(int(ptr))
    tsl()


#Resets the render struct addresses
@sims4.commands.Command('rsts', command_type=(sims4.commands.CommandType.Live))
def rsts(_connection=None):
    global known_sruct_locations
    global chosen_structs
    known_sruct_locations.clear()
    vrdll.set_struct_location(4545)
    chosen_structs.clear()
 
#Gets the camera position from game memmory
def get_cam_pos():
    global chosen_structs
    for structpos in chosen_structs:
        x_pos = ctypes.c_float.from_address(structpos+96)
        y_pos = ctypes.c_float.from_address(structpos+100)
        z_pos = ctypes.c_float.from_address(structpos+104)
        
        return (sims4.math.Vector3(x_pos.value, y_pos.value, z_pos.value))
    dprnt("could not find a camera position, nr of chosen_structs = "+str(len(chosen_structs)))
    return False

#Gets the camera rotation from game memmory
def get_cam_rot():
    mat = [[vrdll.get_float_value(3),vrdll.get_float_value(4),vrdll.get_float_value(5)],
        [vrdll.get_float_value(6),vrdll.get_float_value(7),vrdll.get_float_value(8)],
        [vrdll.get_float_value(9),vrdll.get_float_value(10),vrdll.get_float_value(11)]
    ]
    return threedmath.tpy_rotmat_to_euler(mat)
    
#figures out what render struct address the mod should use
@sims4.commands.Command('tsl', command_type=(sims4.commands.CommandType.Live))
def tsl(_connection=None):
    global known_sruct_locations
    global chosen_structs
    
    dprnt("Selecting chosen_structs, nr of known_sruct_locations = "+str(len(chosen_structs)))
    chosen_structs = []
    chosen_structs2 = []
    first = True
    for structpos in known_sruct_locations:
        x_pos = ctypes.c_float.from_address(structpos+96)
        y_pos = ctypes.c_float.from_address(structpos+100)
        z_pos = ctypes.c_float.from_address(structpos+104)

        if (not math.isnan(x_pos.value)) and round(x_pos.value,2) == round(camera._camera_position.x,2) and round(y_pos.value,2) == round(camera._camera_position.y,2) and round(z_pos.value,2) == round(camera._camera_position.z,2):
            #if first:
            #    
            #    sims_camera_address_compare.value = structpos
            #    first = False

            #TODO there is a bug here as we allow multiple structs
            dprnt("posible struct: "+ hex(structpos))
            chosen_structs2.append(structpos)
            
            
    if len(chosen_structs2) < 1:
        dprnt("Could not find any matching structs");
        return(0)

    if len(chosen_structs2) > 1:
        dprnt("To many matching structs, picking the last one");
    
    structpos = chosen_structs2.pop()
    chosen_structs.append(structpos)
    sims_camera_address_compare.value = structpos
    vrdll.set_struct_location(structpos)#The last struct seams to be the one acctually controlling the camera
    dprnt("chosen struct: "+ hex(structpos)+ " pos: "+str(x_pos.value)+", "+str(y_pos.value)+", "+str(z_pos.value))

    #vr_act()#NOV-30-2022 This should not be here just for temp testing


open_vr_modpath = ModFolder+"\\openvr_api.dll"

dprnt("loading openvr_api")
# it is not needed in python but the dll does not know the path at which it is loaded so we load it before the dll tries to load it
try:
    ctypes.CDLL(open_vr_modpath)
except Exception as e:
    dprnt("could not load openvr_api.dll: "+ str(e))

vr_dll_modpath = ModFolder+"\\s4vrlib.dll"
dprnt("loading vrdll: "+vr_dll_modpath)
vrdll = False
try:
    vrdll = ctypes.CDLL(vr_dll_modpath)
except Exception as e:
    dprnt("could not load vrdll: "+ str(e))
    exit

vrdll.set_scale.argtypes = [ctypes.c_float, ctypes.c_float]
vrdll.set_offset.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
vrdll.set_origin.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
vrdll.set_added_rotation.argtypes = [ctypes.c_float]
vrdll.set_position_scale.argtypes = [ctypes.c_float]
vrdll.set_struct_location.argtypes = [ctypes.c_ulonglong]
vrdll.get_button_value.argtypes = [ctypes.c_int]
vrdll.get_button_value.restype = ctypes.c_ulonglong
vrdll.set_follow.argtypes = [ctypes.c_int]
vrdll.get_float_value.argtypes = [ctypes.c_int]
vrdll.get_float_value.restype  = ctypes.c_float

dprnt("initiating vrdll")
vrdll.init()
dprnt("initiation done")


vrdll.set_scale(game_camera_scalew, game_camera_scale)


using_dll = True
if using_dll:
    address_to_update_function = ctypes.c_ulonglong.from_address(ctypes.addressof(vrdll.update)).value

#Creates a callable function in memory
def create_x86_x64_function(sc):
    rwm = ReadWriteMemory()
    process = rwm.get_process_by_id(pid)
    process.get_all_access_handle()
    ctypes.windll.kernel32.VirtualAllocEx.restype = ctypes.c_ulonglong#Fix the broken VirtualAllocEx before we use it
    memadr = ctypes.windll.kernel32.VirtualAllocEx(process.handle,0, len(sc), 0x3000, 0x40)
    process.writeByte(memadr, sc)
    process.close()
    return memadr

#Patches the game so that the dll gets called on every rendred frame
def call_patch():

    rwm = ReadWriteMemory()
    process = rwm.get_process_by_id(pid)
    process.get_all_access_handle()
    org_instructions = process.readByte(code_injection_base2_address, 15)#save original code
    #process.close()
    
    #Code that can be jumped to that then jumps back after calling a function
    
    #Save all registers except rbp & rsp before function call
    jump_to_code = b'\x50\x53\x51\x52\x56\x57\x41\x50\x41\x51\x41\x52\x41\x53\x41\x54\x41\x55\x41\x56\x41\x57'
    
    #Add sims specific code
    
    #save the camera position struct pointer
    adr = ctypes.addressof(sims_camera_address)
    cmpadr = ctypes.addressof(sims_camera_address_compare)
    jump_to_code += b'\x49\xb9'
    jump_to_code += adr.to_bytes(8,'little')
    jump_to_code += b'\x49\x89\x11\x90\x90\x90'
    
    #At this point we can compare that address with sims_camera_address_compare
    jump_to_code += b'\x49\xb9'+cmpadr.to_bytes(8,'little')#add cmpadr to r9
    jump_to_code += b'\x49\x39\x11'#cmp rdx, r9
    jump_to_code += b'\x75\x1d'#jne 29 pos forward
    
    #function call
    #COmment out to test if the injeciton works
    jump_to_code += b'\x55\x48\x89\xe5\x48\x83\xEc\x20'#setup for function call "push rbp; mov rbp,rsp; sub rsp,20"
    jump_to_code += b'\xFF\x15\x02\x00\x00\x00\xEB\x08'
    jump_to_code += address_to_update_function.to_bytes(8,'little')
    jump_to_code += b'\x48\x83\xc4\x20\x5d'#clean after function call "add rsp,20;pop rbp"
    
    #restore registers and run the instructions replaced by the injection_code
    jump_to_code += b'\x41\x5f\x41\x5e\x41\x5d\x41\x5c\x41\x5b\x41\x5a\x41\x59\x41\x58\x5f\x5e\x5A\x59\x5b\x58'#pop registers from stack

    jump_to_code += org_instructions
    #jump back
    jump_to_code += b'\xFF\x25\x00\x00\x00\x00'
    jump_to_code += (code_injection_base2_address+14).to_bytes(8,'little')
    dprnt("creating patch function")
    jump_to = create_x86_x64_function(jump_to_code)
    
    injection_code = b'\xFF\x25\x00\x00\x00\x00'
    injection_code += jump_to.to_bytes(8,'little')
    injection_code += b'\x90'#We add noop after as it is important for the instructions to tatch length
    
    
    dprnt("jmp "+hex(jump_to))
    
    dprnt("injecting patch function jump")
    process.writeByte(code_injection_base2_address, injection_code)#Write new code
    dprnt("injectied")
    process.close()

dprnt("patching sims4 binary in memory")
if using_dll:
    call_patch()
dprnt("patching sims4 done")

#patch() is an old function that is no longer used, should be removed
@sims4.commands.Command('patch', command_type=(sims4.commands.CommandType.Live))
def patch(_connection=None):
    global sims_camera_address
    global is_patched
    global org_code
    global patch_frame_counter
    global code_injection_base_address
    global saved_first
    global first
    global known_sruct_locations
    global second
    global saved_second
    global pid
    #output = sims4.commands.CheatOutput(_connection) #call 1400F34B0
    
    
    #This is where we will tell the simms to store the pointer to its camera position struct
    adr = ctypes.addressof(sims_camera_address)
    if is_patched == False:
        patch_frame_counter = 0
        is_patched = True
        tsl()

#unpatch() is an old function that is no longer used, should be removed
@sims4.commands.Command('unpatch', command_type=(sims4.commands.CommandType.Live))
def unpatch(_connection=None):
    global is_patched
    global code_injection_base_address
    global pid
    global org_code
    
    #I asume we are done lets reset patch 1
    if is_patched:
        #rwm = ReadWriteMemory()
        #process = rwm.get_process_by_id(pid)
        #process.get_all_access_handle()
        #process.writeByte(code_injection_base_address, org_code)#Write new code
        #process.close()
        is_patched = False


#For some reason the scaling is overwriten by some operations, so we patch those ops away
@sims4.commands.Command('patch2', command_type=(sims4.commands.CommandType.Live))
def patch2_togle(_connection=None):
    global sims_camera_address
    global original_codes
    global Scale_patch_address1
    global Scale_patch_address2
    global patch2_active
    #output = sims4.commands.CheatOutput(_connection)
    #write 4 bytes of NOP ie byte 0x90 to these locations 
    
    
    #When you patch the scale the mouse ponter no longer points to it "correct" position
    patchlocations = [
        Scale_patch_address1, #scaling upp and down
        Scale_patch_address2 #scaling left and right

    ]
    patches = [
        b'\x90\x90\x90\x90\x90\x90\x90',
        b'\x90\x90\x90\x90'
    #    b'\x90'*187
    ]
    

    
    
    
    rwm = ReadWriteMemory()
    process = rwm.get_process_by_id(pid)
    process.get_all_access_handle()
    
    if not patch2_active:
        for x, patchlocation in enumerate(patchlocations):
            original_codes[x] = process.readByte(patchlocation, len(patches[x]))
        
        for x, patchlocation in enumerate(patchlocations):
            process.writeByte(patchlocation, patches[x])#Write NOP's
        
        patch2_active = True
    else:
        for x, patchlocation in enumerate(patchlocations):
            process.writeByte(patchlocation, original_codes[x])
        patch2_active = False
        
    process.close()


vr_active = False
vr_pos = 1

target_compensation = 2.8
extra_rotate = 0
origin_rotate = 0
controller_state = 0
cam_syncing = False
before_sync_cam_location = 0
keypress_bebounce_count = 0
headset_position_corected = 0
headset_position_uncorected = 0

last_second = "0"
ticks_p_s = 0

#not acctually renderd on every gfx frame (the function is named like this cause of old legacy)
def on_gfx_frame():
    global headset_position_uncorected
    global headset_position
    global headset_rotation
    
    global last_second
    global ticks_p_s
    
    global game_desired_cam_pos
    global extra_rotate
    global origin_rotate
    global headset_offset
    global origin_sims_camera_pos
    
    
    second = datetime.datetime.now().strftime("%S")
    if second != last_second:
        #dprnt("cam: "+str(camera._camera_position.x)+", "+str(camera._camera_position.y)+", "+str(camera._camera_position.z))
        #dprnt("fps: "+str(ticks_p_s))
        ticks_p_s = 0
        last_second = second
    
    ticks_p_s += 1
    
    if True:
        headset_position_struct = sims4.math.Vector3(vrdll.get_float_value(15), vrdll.get_float_value(16), vrdll.get_float_value(17))
        headset_position_uncorected = sims4.math.Vector3(headset_position_struct.x, headset_position_struct.y, headset_position_struct.z)
        ##30-nov-2022 This need to be fixed should be yaw corrected
        headset_position = headset_position_struct
        #_vpxGetFloat3(103)
        headset_rotation = sims4.math.Vector3(vrdll.get_float_value(12), vrdll.get_float_value(13), vrdll.get_float_value(14))
    
    if vorpx_loaded:
        try:
            fov = _vpxGetFloat(100)#always 96.01604461669922 on quest2
            last_headset_rotation = headset_rotation
            headset_position_struct = _vpxGetFloat3(103)
            headset_rotation = _vpxGetFloat3(101)
            #headset_quat = _vpxGetFloat4(102)
            headset_position = _vpxYawCorrection(headset_position_struct, float(origin_rotate+extra_rotate))
            
        except Exception as e:
            dprnt("failed using _vpxGetControllerState: "+str(e))
    
    
    if vr_active:
        
        #We should read in game_desired_cam_pos here it is avalible in memmory at this point 2022-01 Nahhh not any longer 2022-04 that would need to be done in the vrdll
        
        #save for use when reseting position
        
        
        headset_position_struct.x -= headset_offset.x
        headset_position_struct.y -= headset_offset.y
        headset_position_struct.z -= headset_offset.z
        
        
        
#Togles "sims4 First person camera mode"
def togle_fps_mode():
    pyautogui.keyDown('shift')
    pyautogui.press('tab')
    pyautogui.keyUp('shift')

#Trys to figure out if we are in "sims4 First person camera mode"
def is_in_fps_mode():
    actual_cam_pos = get_cam_pos()
    if round(actual_cam_pos.x,2) == round(camera._camera_position.x,2) and round(actual_cam_pos.y,2) == round(camera._camera_position.y,2) and round(actual_cam_pos.z,2) == round(camera._camera_position.z,2):
        return False
    return True 

#the FireID is the id of some object that will be placed on the position of the right controller. Used for scale debuging.
FireID = 43#0x097c0d80186b3304
def set_fireid(uf):
    global FireID
    FireID = uf
tab_active = False

class Object(object):
    pass

follow_active = 0
#When the game informs us that it has executed a game frame
def on_game_frame():
    global patch_frame_counter
    global keypress_bebounce_count
    global cam_syncing
    global vr_active
    global tab_active
    global game_desired_cam_pos
    global game_camera_scalew
    global game_camera_scale
    global hold_b_button_frame_counter
    global last_btns_press
    global holding_grab
    global follow_active
    global holding_trig
    global before_sync_cam_location
    global origin_sims_camera_pos
    global origin_sims_camera_pos
    global headset_offset
    global extra_rotate
    global origin_rotate
    global controller_state
    global FireID
    global sims_camera_address
    global known_sruct_locations
    
    #Handle input from the debug TCP connection
    handle_dbg_com()
    
    patch_frame_counter += 1
    keypress_bebounce_count += 1
    
    vr_tog = False
    
    if cam_syncing:
        after_sync_cam_location = get_cam_pos()
        if before_sync_cam_location.x != after_sync_cam_location.x or before_sync_cam_location.y != after_sync_cam_location.y:
            vr_act()
            cam_syncing = False
    
    #We wait for 300 frames untill we evaluate the data, unpatch, and apply patch2
    if patch_frame_counter == 20 and is_patched:
        unpatch()
        vr_tog = True
    
    if sims_camera_address.value != 4545:
        if sims_camera_address.value not in known_sruct_locations:
            dprnt("Added new known_sruct_locations: "+str(sims_camera_address.value))
            known_sruct_locations.append(sims_camera_address.value)
    
    
    controller_state = Object()
    controller_state.ButtonsPressed = vrdll.get_button_value(0)
    controller_state.StickX = vrdll.get_float_value(18)*2
    controller_state.StickY = vrdll.get_float_value(19)*2
    controller_state.Trigger = 0
    controller_state.Grip = 0
    controler_rotation = sims4.math.Vector3(0, 0, 0)

    dprnt("btnpres: "+str(controller_state.ButtonsPressed))

    if headset_rotation != 0:
        controler_rotation = sims4.math.Vector3(headset_rotation.x, headset_rotation.y, headset_rotation.z)#TODO jan 29 hack to make movments work with camera

    if controller_state.ButtonsPressed == 128:
        controller_state.ButtonsPressed = 1
    elif controller_state.ButtonsPressed == 2:
        controller_state.ButtonsPressed = 2
    elif controller_state.ButtonsPressed == 17179869188:
        controller_state.ButtonsPressed = 0
        controller_state.Grip = 1
    elif controller_state.ButtonsPressed == 8589934592:#
        controller_state.Trigger = 1
    elif controller_state.ButtonsPressed == 25769803780:
        controller_state.Trigger = 1
        controller_state.Grip = 1

    if vorpx_loaded:
        #controller_state = _vpxGetControllerState(1)#get right controler state
        #controller_state_left = _vpxGetControllerState(0)#get left controler state
        
        #controler_rotation = _vpxGetFloat3(203)
        #controler_pos = _vpxGetFloat3(205)##if we want to create shoot to location

        controler_pos.x -= headset_offset.x
        controler_pos.y -= headset_offset.y
        controler_pos.z -= headset_offset.z
        #For debuging i would like to draw the controllers in game
        #Not sure how to get a model of the controllers in to the game and then how to create an instance of the models
        #so we jsut use a firealarm that is already in the game to debug the controler position
        controler_pos_corrected = _vpxYawCorrection(controler_pos, float(origin_rotate))
        if origin_sims_camera_pos != 0:
            new_cont_x = origin_sims_camera_pos.x + (controler_pos_corrected.x);
            new_cont_y = origin_sims_camera_pos.y + (controler_pos_corrected.y);
            new_cont_z = origin_sims_camera_pos.z - (controler_pos_corrected.z);
            
            
            
            if FireID != 43:
                firealarm = services.object_manager().get(FireID)
                FireLocat = firealarm.location
                FireLocat[0].translation = sims4.math.Vector3(new_cont_x, new_cont_y, new_cont_z)
                firealarm.set_location(FireLocat)
        
    if controller_state.ButtonsPressed != 0:
        hold_b_button_frame_counter += 1
        if hold_b_button_frame_counter == 20:
            dprnt("button hold down for long: "+str(last_btns_press))
            #if last_btns_press == 2:#B was pressed long, 
            #    pyautogui.press('somebutton')
                
            if last_btns_press == 1:#A was pressed long, tell sims4 to toogle GUI (press tab)
                pyautogui.press('tab')
    else:
        if last_btns_press != controller_state.ButtonsPressed:
            if hold_b_button_frame_counter < 20:
                dprnt("button was clicked quickly: "+str(last_btns_press))
                #if last_btns_press == 1:#A was pressed short, click mouse
                #    pyautogui.click()
                if last_btns_press == 1:#A was pressed short, reset position
                    if follow_active == 0:
                        follow_active = 1
                    else:
                        follow_active = 0
                        x = vrdll.get_float_value(0)
                        y = vrdll.get_float_value(1)
                        z = vrdll.get_float_value(2)
                            
                        origin_sims_camera_pos = sims4.math.Vector3(x, y, z)
                        vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)

                        if headset_position_uncorected != 0:
                            headset_offset.x = headset_position_uncorected.x
                            headset_offset.y = headset_position_uncorected.y
                            headset_offset.z = headset_position_uncorected.z
                            vrdll.set_offset(0, headset_offset.y, 0)
                    vrdll.set_follow(follow_active)
                    
                if last_btns_press == 2:#B was pressed short, initate vr (should also  press tab+shit to enter fps mode)
                    dprnt("#B was pressed short, start vr")
                    vr_tog = True
        
    if vr_tog:
        if len(chosen_structs) > 0:
            if vr_active:
                if is_in_fps_mode():
                    togle_fps_mode()
                vr_act()
            else:
                if not is_in_fps_mode():
                    #cam_syncing = True
                    #before_sync_cam_location = get_cam_pos()
                    vr_act()
                    togle_fps_mode()
                else:
                    vr_act()
        else:
            patch()

    
    old_holding_trig = holding_trig
    if controller_state.Trigger == 0:
        holding_trig = False
    else:
        holding_trig = True
        
    if holding_trig != old_holding_trig:
        if holding_trig:
            pyautogui.click()#press mouse on trigger
        
    old_holding_grab = holding_grab
    if controller_state.Grip == 0:
        holding_grab = False
    else:
        holding_grab = True
        
    #if holding_grab != old_holding_grab and vr_active:
    #    if holding_grab:
    #        _vpxSetInt(400, 1)#Enable Edge peek
    #    else:
    #        _vpxSetInt(400, 0)#Disable Edge peek
        
    if last_btns_press != controller_state.ButtonsPressed:
        hold_b_button_frame_counter = 0
        last_btns_press = controller_state.ButtonsPressed
        dprnt("button change: "+str(last_btns_press))
        
        
    #if controller_state_left.StickX > 0.5 or controller_state_left.StickX < -0.5:
    #    game_camera_scalew += controller_state_left.StickX*0.001
    #    vrdll.set_scale(game_camera_scalew, game_camera_scale)
            
    #if controller_state_left.StickY > 0.5 or controller_state_left.StickY < -0.5:
    #    game_camera_scale += controller_state_left.StickY*0.001
    #    vrdll.set_scale(game_camera_scalew, game_camera_scale)
            
    #When holding grap we move the cursor
    mouse_speed = 20
    if holding_grab:
        pyautogui.moveRel(controller_state.StickX*mouse_speed, -controller_state.StickY*mouse_speed)
    else:
        #should move in the 3D direction of the controller but we will start with just camera direction first on the plane
        if controller_state.StickY != 0.0:
            if origin_sims_camera_pos != 0:
                cos_len = math.cos(math.radians(controler_rotation.x))
                origin_sims_camera_pos.x += math.sin(math.radians(controler_rotation.y+origin_rotate))*cos_len*0.05*controller_state.StickY
                origin_sims_camera_pos.z += -math.cos(math.radians(controler_rotation.y+origin_rotate))*cos_len*0.05*controller_state.StickY
                origin_sims_camera_pos.y -= math.sin(math.radians(controler_rotation.x))*0.05*controller_state.StickY
                dprnt("controler rot: x: "+str(controler_rotation.x)+" y: "+str(controler_rotation.y))
                vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
            
        if controller_state.StickX > 0.5 or controller_state.StickX < -0.5:
                
            #To rotate we need to create a new reference frame
            if headset_rotation == 0:
                rot = 0
            else:
                rot = headset_rotation.y
            origin_sims_camera_rot = get_cam_rot()
            origin_rotate = origin_rotate+controller_state.StickX
            vrdll.set_added_rotation(float(origin_rotate))
            new_cam_pos = sims4.math.Vector3(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
            new_cam_pos.x += (headset_position.x)*scale#*math.sin(math.radians(extra_rotate))
            new_cam_pos.y += (headset_position.y)*scale#up/down
            new_cam_pos.z -= (headset_position.z)*scale
            origin_sims_camera_pos = new_cam_pos
            vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
            if headset_position_uncorected != 0:
                headset_offset.x = headset_position_uncorected.x
                headset_offset.y = headset_position_uncorected.y
                headset_offset.z = headset_position_uncorected.z
                vrdll.set_offset(0, headset_offset.y, 0)

tickers = 0
@injector.inject_to(Zone, 'update')
def vr_zone_update(original, self, absolute_ticks):
    global vr_active
    global vr_pos
    global vorpx_loaded
    global extra_rotate
    global keypress_bebounce_count
    global patch_frame_counter
    global is_patched
    global scale
    global game_camera_scale
    global game_camera_scalew
    global headset_position_uncorected
    global headset_position_corected
    global cam_syncing
    global headset_offset
    global controller_state
    global hold_b_button_frame_counter
    global last_btns_press
    global before_sync_cam_location
    global headset_position
    global headset_rotation
    global target_compensation
    global known_sruct_locations
    global sims_camera_address
    global tickers
    original(self, absolute_ticks)

    on_game_frame()
    
    on_gfx_frame()
    
change_act = True
@sims4.commands.Command('vrd', command_type=(sims4.commands.CommandType.Live))
def vr_dllact(load_fresh=True,_connection=None):
    global change_act
    if change_act:
        change_act = False
        vrdll.set_vr_active(0)
    else:
        change_act = True
        vrdll.set_vr_active(1)


#Initiates VR
@sims4.commands.Command('vra', command_type=(sims4.commands.CommandType.Live))
def vr_act(load_fresh=True,_connection=None):
    global vr_active
    global headset_position
    global headset_rotation
    global scale
    global headset_offset
    global origin_sims_camera_pos
    global origin_sims_camera_rot
    global extra_rotate
    global origin_rotate
    if vr_active:
        #_vpxSetInt(400, 1)#Enable Edge peek
        new_cam_pos = sims4.math.Vector3(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
        new_cam_pos.x += (headset_position.x)*scale
        new_cam_pos.y += (headset_position.y)*scale#up/down
        new_cam_pos.z -= (headset_position.z)*scale
        origin_sims_camera_pos = new_cam_pos
        vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
        vr_active = False
        vrdll.set_vr_active(0)
        target = sims4.math.Vector3(origin_sims_camera_pos.x+math.sin(math.radians(headset_rotation.y+origin_rotate)), origin_sims_camera_pos.y, origin_sims_camera_pos.z-math.cos(math.radians(headset_rotation.y+origin_rotate)))
        camera.focus_on_object_from_position(target, origin_sims_camera_pos)
        camera._camera_position = origin_sims_camera_pos
    else:
        #_vpxSetInt(400, 0)#Disable Edge peek

        origin_sims_camera_rot = get_cam_rot()
        origin_sims_camera_pos = get_cam_pos()
        vr_active = True
        
        orgiginal_target = camera._target_position
        if headset_rotation == 0:
            rot = 0
        else:
            rot = headset_rotation.y
        
        
        origin_rotate = origin_sims_camera_rot.y-rot
        vrdll.set_added_rotation(float(origin_rotate))
        extra_rotate = 0
        
        #TODO: add correction, camera gets located inside the head of the character instead of where the headset is
        #The camera should be moved about 10cm in the camera direction from the characters head
        
        vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
        #vrdll.set_offset(0,,0)
        if headset_position_uncorected != 0:
            headset_offset.x = headset_position_uncorected.x
            headset_offset.y = headset_position_uncorected.y
            headset_offset.z = headset_position_uncorected.z
            vrdll.set_offset(0, headset_offset.y, 0)#The headset 0,0,0 is on the ground?
        vrdll.set_vr_active(1)
    patch2_togle()

#Debug command to allow executing simple python commands from inside the game
@sims4.commands.Command('py', command_type=sims4.commands.CommandType.Live)
def _py(cmd: str="", cmda: str="", cmdb: str="", cmdc: str="", _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    cmd = cmd +" "+ cmda +" "+ cmdb +" "+ cmdc 
    output("py eval: "+cmd)
    try:
        ret = str(eval(cmd))
        output(ret)
    except Exception as e:
        output("Exception: "+ str(e))


dprnt("Initiate Debug TCP connection")
if True:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    connected = False

    try:
        s.connect(('127.0.0.1', 5000))
        s.setblocking(False)
        s.send(b'python shell:')
        connected = True
    except Exception as e:
        dprnt("Failed to connect to debug connection: "+str(e))

def se(dat):
    global s
    global connected
    if connected:
        s.send(bytes(str(dat), "utf-8"))

#Handle data from Debug TCP connection
def handle_dbg_com():
    global s
    global connected
    
    if connected:
        cmd = ""
        try:
            cmd = s.recv(2500).decode("utf-8") 
        except Exception as e:
            1#no data from debug conection
        if cmd != "":
            try:
                exec(cmd, globals(), globals())
            except Exception as e:
                se("Exception: "+ str(e))
        

dprnt("Loaded VR Mod")

