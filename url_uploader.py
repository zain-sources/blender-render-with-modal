import modal
from config import config
from pathlib import Path
from urllib import request


app = modal.App(name="testing")
volume = modal.Volume.from_name("render-guru", create_if_missing=True)


@app.function(volumes={"/root/cloud-volume": volume}, timeout=60*30)
def uploader():
    cloud_volume = Path("/root/cloud-volume")
    
    volume_blend_save_path = cloud_volume / "blend_files/guru.blend"
    volume_blend_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    url = ""
    b = request.urlopen(url)
    volume_blend_save_path.write_bytes(b.content)
    
    
        