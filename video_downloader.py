import modal
from config import config

i = 0
app = modal.App(name=config["app_name"])
volume = modal.Volume.from_name(config["volume_name"], create_if_missing=True)


with open(config["local_video_save_path"], "wb") as f:
    for chunk in volume.read_file(config["volume_video_save_path"]):
        f.write(chunk)
        if i % 1000 == 0:
            print(f"Downloaded ...")
            
    print("Downloaded video")