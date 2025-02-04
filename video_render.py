from pathlib import Path
import modal


##################### Config #####################

### Avaliable GPUs
# T4
# L4
# A10G
# L40S
# A100-80GB
# A100-40GB
# H100

from config import config


##################### App #####################

app = modal.App(name=config["app_name"])
volume = modal.Volume.from_name(config["volume_name"], create_if_missing=True)
WITH_GPU = config["gpu-mode"]



################# Rendering frames #################

@app.function(
    gpu=config["gpu"] if WITH_GPU else None, 
    concurrency_limit= config["concurrency_limit"] if WITH_GPU else 50,
    image=modal.Image.debian_slim(python_version="3.11").apt_install("xorg", "libxkbcommon0").pip_install("bpy==4.1.0"),
    volumes={"/root/cloud-volume": volume},
    timeout=60*30
)
def render(blend_file_path_in_volume: str , frame_number: int = 0) -> str:
    """Renders the n-th frame of a Blender file as a PNG."""
    import bpy # type: ignore
    # load the blend file from the volume
    cloud_volume = Path("/root/cloud-volume")
    blend_file_path = cloud_volume / blend_file_path_in_volume
    blend_file = Path(blend_file_path).read_bytes()

    # internal paths
    input_path = "/tmp/input.blend"
    output_path = f"/tmp/output-{frame_number}.png"
    
    # Blender requires input as a file.
    Path(input_path).write_bytes(blend_file)

    bpy.ops.wm.open_mainfile(filepath=input_path)
    bpy.context.scene.frame_set(frame_number)
    bpy.context.scene.render.filepath = output_path
    configure_rendering(bpy.context, with_gpu=WITH_GPU)
    bpy.ops.render.render(write_still=True)
    
    # saving image to volume
    vol_image_path = cloud_volume / config["volume_frame_save_dir"] / f"frame_{frame_number:05}.png"
    vol_image_path.parent.mkdir(parents=True, exist_ok=True)
    
    image_bytes = Path(output_path).read_bytes()
    Path(vol_image_path).write_bytes(image_bytes)
    volume.commit() 

    return str(vol_image_path)

def configure_rendering(ctx, with_gpu: bool):
    # configure the rendering process
    ctx.scene.render.engine = "CYCLES"
    ctx.scene.render.resolution_x = config["x_resolution"]
    ctx.scene.render.resolution_y = config["y_resolution"]
    ctx.scene.render.resolution_percentage = config["resolution_percentage"]
    ctx.scene.cycles.samples = config["samples"]
    
    ##################
    ctx.scene.cycles.use_denoising = True # Enable denoising
    ctx.scene.cycles.denoiser = 'OPENIMAGEDENOISE' # Use OIDN denoiser
    
    ##################

    cycles = ctx.preferences.addons["cycles"]

    # Use GPU acceleration if available.
    if with_gpu:
        cycles.preferences.compute_device_type = "CUDA"
        ctx.scene.cycles.device = "GPU"

        # reload the devices to update the configuration
        cycles.preferences.get_devices()
        for device in cycles.preferences.devices:
            device.use = True
    else:
        ctx.scene.cycles.device = "CPU"
    
    for dev in cycles.preferences.devices:
        print(
            f"ID:{dev['id']} Name:{dev['name']} Type:{dev['type']} Use:{dev['use']}"
        )


##################### Combining frames into a video #####################

@app.function(image=modal.Image.debian_slim(python_version="3.11").apt_install("ffmpeg"), volumes={"/root/cloud-volume": volume})
def combine(volume_frame_save_dir: str = config["volume_frame_save_dir"], fps: int = config["video_fps"]) -> bytes:
    import subprocess
    import tempfile
    
    cloud_volume = Path("/root/cloud-volume")
    volume_video_save_path = cloud_volume / config["volume_video_save_path"]
    volume_video_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "output.mp4"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config["best-quality-video-compilation"]:
            subprocess.run(
                f"ffmpeg -framerate {fps} -pattern_type glob -i '/root/cloud-volume/{volume_frame_save_dir}/*.png' \
                    -c:v libx264 \
                    -preset veryslow \
                    -crf 12 \
                    -pix_fmt yuv444p \
                    {out_path}",
                shell=True,
            )
            
        else:                
            subprocess.run(
                "ffmpeg -framerate {fps} -pattern_type glob -i '/root/cloud-volume/{volume_frame_save_dir}/*.png' \
                    -c:v libx264 \
                    -pix_fmt yuv420p \
                    {out_path}",
                shell=True,
            )
        
        # saving video to volume
        volume_video_save_path.write_bytes(out_path.read_bytes())
        return "Video saved to " + str(volume_video_save_path)



##################### Main function #####################

@app.local_entrypoint()
def main():
    # upload the blend file to the volume
    local_blend_file_path = Path(__file__).parent / config["local_blend_file_path"]
    volume_blend_file_path = config["volume_blend_file_path"]
    with volume.batch_upload() as batch:
        batch.put_file(local_blend_file_path, volume_blend_file_path)

    # rendering the frames
    start_frame = config["start_frame"]
    end_frame = config["end_frame"] + 1
    
    args = [(volume_blend_file_path, frame) for frame in range(start_frame, end_frame, 1)]
    images_paths_in_volume = list(render.starmap(args))
    
    # Celebration
    print(images_paths_in_volume)
    print("\n\nRendering done.")
    
    # combining the frames into a video
    if config["make_video"]:
        video_status = combine.remote(volume_frame_save_dir=config["volume_frame_save_dir"], fps=config["video_fps"])
        print(video_status)
