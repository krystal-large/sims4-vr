# Sims 4 VR Mod Analysis Recap

## Key Findings and Conclusions

1. Hybrid approach: Python for high-level logic, C++ (via DLL) for low-level VR integration.
2. .ts4script file: Custom Sims 4 mod format (zip file with .pyc files and resources).
3. DirectX hooks used to modify the game's rendering pipeline for VR.
4. OpenVR integration for VR functionality (headset tracking, controller input).
5. Custom camera scaling and positioning for VR, adjustable in real-time.
6. Python-C++ boundary managed through custom DLL (s4vrlib.dll) with exported functions.
7. Sophisticated modding approach, interfacing with game's Python API and graphics pipeline.
8. DirectX hooks enable VR integration without base game code modification.

## Useful Python Capabilities Uncovered

1. Creating custom Sims 4 cheat console commands:
   ```python
   @sims4.commands.Command('vr_scale', command_type=sims4.commands.CommandType.Live)
def set_vr_scale(scale: float, scale_w: float, _connection=None):
    global game_camera_scale, game_camera_scalew
    game_camera_scale = float(scale)
    game_camera_scalew = float(scale_w)
    vrdll.set_scale(game_camera_scalew, game_camera_scale)
    output = sims4.commands.CheatOutput(_connection)
    output(f"VR scale set to: vertical={game_camera_scale}, horizontal={game_camera_scalew}")

@sims4.commands.Command('vr_scale_info', command_type=sims4.commands.CommandType.Live)
def get_vr_scale_info(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output(f"Current VR scale: vertical={game_camera_scale}, horizontal={game_camera_scalew}")
    ```



1. Interacting with C++ DLLs using ctypes:

```python
vrdll = ctypes.CDLL(vr_dll_modpath)

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

vrdll.init()

vrdll.set_scale(game_camera_scalew, game_camera_scale)
vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
vrdll.set_added_rotation(float(origin_rotate))
```

Regarding useful inputs we can have available in Python:

VR System Information:

vrdll.get_float_value(15), vrdll.get_float_value(16), vrdll.get_float_value(17): These seem to return the VR headset position.
vrdll.get_float_value(12), vrdll.get_float_value(13), vrdll.get_float_value(14): These appear to return the VR headset rotation.


Controller Input:

vrdll.get_button_value(0): Returns the current button state.
vrdll.get_float_value(18) and vrdll.get_float_value(19): Seem to return controller stick positions.


Render Parameters:

vrdll.get_float_value(3) to vrdll.get_float_value(11): These appear to return elements of the view or projection matrix.



1. Compiling Python files to .pyc and creating .ts4script files:

```python
compile_full(src_dir, zf)  # Where zf is a PyZipFile object
```

1. Using exec() to run additional Python scripts (use cautiously):

```python
exec(open("sync_packages.py").read())
```

1. implementing a custom logging system:

```python
def dprnt(txt):
    global ModFolder
    txt=str(txt)
    now = datetime.datetime.now()
    log_str = now.strftime("%Y-%m-%d %H:%M:%S")+": "+txt+"\n"
    file_object = open(ModFolder+"\\debug_log.txt", 'a')
    if file_object:
        file_object.write(log_str)
        file_object.close()
```




## Best Practices Observed

- Separation of concerns: Python for high-level logic, C++ for performance-critical operations.
- Real-time adjustment capabilities for VR development.
- Modular approach for easier maintenance and future expansions.

## Areas for Potential Improvement

- More interesting sims cheat console commands for more control over the VR setting in `vrdll`
- More robust error handling in compilation and DLL loading processes.
- Consider using Python's logging module instead of custom logging function.
- Implement user-friendly interface for adjusting VR settings.

## Roles Involved

- Game Modder: Understanding Sims 4 modding ecosystem and API.
- VR Developer: Implementing OpenVR integration and VR-specific features.
- Python Programmer: Developing high-level mod logic and game interactions.
- C++ Programmer: Creating the DLL for low-level VR and DirectX operations.
- 3D Graphics Programmer: Handling camera transformations and rendering pipeline modifications.
- UI/UX Designer: Potentially needed for creating in-game VR settings interface.

## Future Development Opportunities

- Performance Optimization: Profile the mod to identify and optimize performance bottlenecks, especially in VR rendering.
- Enhanced VR Interactions: Implement VR-specific interactions with in-game objects using tracked controllers.
- Multiplayer VR: Explore possibilities of VR multiplayer experiences within Sims 4.
- Mod Configuration Tool: Develop a separate tool for easy mod configuration and VR calibration.
- VR-Specific UI: Create a VR-friendly user interface for in-game menus and controls.
- Photogrammetry Integration: Explore adding real-world scanned objects into the game in VR.
- Voice Commands: Implement voice recognition for easier control in VR.
- VR Spectator Mode: Develop a feature allowing non-VR players to view VR player's perspective.

This project showcases the impressive possibilities of game modding, particularly in adding VR support to a game not originally designed for it. It demonstrates a deep understanding of both the game's architecture and VR technology, blending high-level and low-level programming to achieve its goals.