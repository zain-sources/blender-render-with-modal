
from pathlib import Path
import modal

##################### Config #####################
from config import config


##################### App #####################

app = modal.App(name=config["app_name"])
volume = modal.Volume.from_name(config["volume_name"], create_if_missing=True)


################# Combining frames #################

combination_image = modal.Image.debian_slim(python_version="3.11").apt_install("ffmpeg")

@app.function(image=combination_image, volumes={"/root/cloud-volume": volume}, timeout=60*30)
def combine(volume_frame_save_dir: str = config["volume_frame_save_dir"], fps: int = config["video_fps"]) -> bytes:
    import subprocess
    import tempfile
    from glob import glob
    from pathlib import Path
    
    cloud_volume = Path("/root/cloud-volume")
    volume_video_save_path = cloud_volume / config["volume_video_save_path"]
    volume_video_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "output.mp4"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Using ffmpeg to combine frames into a video
        if config["best-quality-video-compilation"]:
            subprocess.run(
                f"ffmpeg -framerate {fps} -pattern_type glob -i '/root/cloud-volume/{volume_frame_save_dir}/*.png' \
                    -c:v libx264 \
                    -preset veryslow \
                    -crf 10 \
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
    video_status = combine.remote(volume_frame_save_dir=config["volume_frame_save_dir"], fps=config["video_fps"])
    print(video_status)
    