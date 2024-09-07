Certainly! Let's dive into how the camera scale is set in this mod. Based on the code we've seen in `main.py` and the log file, there are several components involved in configuring the game camera's scale, position, and angle for VR. Let's break this down:

1. Camera Scale:
   In `main.py`, we see these variables:

   ```python
   game_camera_scale = 1.1298482051491667
   game_camera_scalew = 0.8552593232989314
   ```

   These values are used to set the camera scale. The `game_camera_scale` likely affects the vertical scale, while `game_camera_scalew` affects the horizontal scale.

   The scale is set using this function call:

   ```python
   vrdll.set_scale(game_camera_scalew, game_camera_scale)
   ```

   This suggests that the actual scaling is handled in the C++ part of the mod (in the s4vrlib.dll).

2. Camera Position:
   The mod seems to manipulate the camera position based on the VR headset's position. This is handled in the `on_game_frame()` function, where it updates `origin_sims_camera_pos`:

   ```python
   vrdll.set_origin(origin_sims_camera_pos.x, origin_sims_camera_pos.y, origin_sims_camera_pos.z)
   ```

3. Camera Angle:
   The camera angle is likely derived from the VR headset's rotation. This is handled in the same function:

   ```python
   vrdll.set_added_rotation(float(origin_rotate))
   ```

4. Depth of Field:
   The depth of field issue you're experiencing might be related to how the mod is calculating the projection matrix for VR. This is typically handled in the VR system itself (OpenVR in this case), but the mod might be overriding or adjusting these values.

To address the depth of field issue:

1. Check the `OpenVR-DirectMode.cpp` file (if available) for functions related to setting up the projection matrix or camera frustum.

2. Look for calls to OpenVR functions that set up the projection, such as `vr::IVRSystem::GetProjectionRaw` or similar.

3. In `main.py`, there's a comment about FOV calculation:

   ```python
   #the quest has 96.0160446166992 deg vertical fov according to vorpx
   #game_camera_scale = math.atan(math.radians(96.0160446166992)/2)
   ```

   This suggests that the FOV (Field of View) is being calculated based on the Quest's specifications, but it's currently commented out.

To adjust the depth of field:

1. You could try uncommenting and adjusting the FOV calculation. A wider FOV might help with the depth perception in VR.

2. Experiment with different values for `game_camera_scale` and `game_camera_scalew`. These directly affect how the game world is projected into VR space.

3. Look for any functions in the C++ part of the mod (s4vrlib.dll) that handle projection matrix creation or modification. You might need to adjust the near and far clipping planes or the way the projection matrix is calculated.

4. Check if there's any post-processing or distortion correction being applied in the VR rendering pipeline that might be affecting depth perception.

To get a better understanding, you could add more detailed logging in the `set_scale` function call, like:

```python
dprnt(f"Setting camera scale: vertical={game_camera_scale}, horizontal={game_camera_scalew}")
```

This will help you confirm what values are actually being used when the mod runs.

Remember, VR depth perception is sensitive to many factors, including IPD (Interpupillary Distance) settings, FOV, and how the game's 3D space is mapped to VR space. You might need to experiment with several of these factors to get the right feel.