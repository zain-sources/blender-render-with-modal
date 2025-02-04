
# *Blender Scene render using Modal Cloud*

This is a code file that renders a blender file on Modal Cloud GPUs. `config.py` contains all the settings. Change settings in `config.py` file and manage things accordingly.
### Roadmap
- Setup your **Modal.com** account on your PC
- Copy you `scene.blend` file (*all assets should be packed in one file*) into 
- Change the parameters in `congif.py` file accordingly
- Start the rendering


## **Documentation**
Here is complete documentation to run the script
### Model Setup

Goto [modal.com](https://modal.com/) and create an account. After creating account follow the modal setup on your PC as below

```bash
    pip install modal
    python -m modal setup
```

### Intial Setup
- Place your `scene.blend` in **/blend_files** folder
- Make changes in `config.py` file as needed

```python
// config.py file

config = {
    "x_resolution": 3500,
    "y_resolution": 3500,
    "resolution_percentage": 100,
    "samples": 100,

    "gpu-mode": True,
    "gpu": "L40S",
    "concurrency_limit": 4,

    "start_frame": 1,
    "end_frame": 20,

    "app_name": "blender-video-render",
    "volume_name": "exp-render-farm",
    "volume_frame_save_dir": "frames",
    "volume_blend_file_path": "blend_files/scene.blend",
    "local_blend_file_path": "blend_files/scene.blend",

    "video_fps": 30,
    "volume_video_save_path": "videos/scene.mp4",
    "local_video_save_path": "videos/scene.mp4",
    "make_video": True,
    "best-quality-video-compilation": False,
}

```

### Run
Open command prompt/terminal in project directory and run this command

```
modal video_render.py
```
## **Features**

- concurrency
- video compilation from frames

