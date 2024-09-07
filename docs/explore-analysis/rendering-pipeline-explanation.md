# Rendering Pipeline and Presentation in VR Context

## Understanding Presentation

In graphics programming, 'presentation' refers to the act of displaying a fully rendered frame on the screen. It's the final step in the rendering process where the completed frame is swapped into view.

- In traditional rendering: This usually means swapping the back buffer (where the frame was drawn) with the front buffer (what's currently displayed on the screen).
- In VR: Presentation involves submitting the rendered frame to the VR compositor, which then handles displaying it on the VR headset.

## Pre- and Post-Presentation Hooks

Hooks are points in the code where we can intercept and modify the normal flow of execution. In the context of this VR mod:

1. **Pre-Presentation Hook**:
   - Occurs just before the game would normally present its frame.
   - In `OpenVRDirectMode::PrePresentEx()`, this is where the mod:
     - Captures the frame the game has rendered.
     - Prepares it for VR (which may involve rendering it twice, once for each eye).
     - Copies it from DirectX 9 surfaces (used by the game) to DirectX 11 surfaces (used for VR).

2. **Post-Presentation Hook**:
   - Occurs just after the game would normally have presented its frame.
   - In `OpenVRDirectMode::PostPresentEx()`, this is where the mod:
     - Submits the prepared VR frames to the OpenVR compositor.
     - Handles any post-render VR-specific operations.

## Relationship Between `dllmain.cpp` and `OpenVR-DirectMode.cpp`

These two files work together to implement the VR functionality:

1. `dllmain.cpp`:
   - Acts as the entry point for the VR DLL.
   - Sets up function hooks into the game's DirectX functions (like `EndScene` and `Present`).
   - Creates and manages the `OpenVRDirectMode` object.

2. `OpenVR-DirectMode.cpp`:
   - Implements the actual VR functionality that the hooks in `dllmain.cpp` call into.
   - Handles the OpenVR initialization, frame submission, and VR-specific operations.

## The Flow of a Frame

1. The game renders a frame as usual.
2. Just before the game would present this frame, `dllmain.cpp`'s hook intercepts and calls `OpenVRDirectMode::PrePresentEx()`.
3. `PrePresentEx()` prepares the frame for VR.
4. The game thinks it has presented the frame and continues.
5. `dllmain.cpp`'s post-presentation hook calls `OpenVRDirectMode::PostPresentEx()`.
6. `PostPresentEx()` submits the prepared VR frame to the OpenVR compositor.
7. The VR compositor displays the frame on the VR headset.

This process allows the mod to take control of the rendering pipeline at crucial points, enabling VR output without requiring extensive modifications to the game's core rendering code.

