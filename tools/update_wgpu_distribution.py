from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
from os.path import join

base_url = "https://github.com/gfx-rs/wgpu-native/releases/download"
git_tag = "v0.18.0.1"

# Make sure to check out the right branch!
destination = "G:/SourceCode/WebGPU-distribution"

#all_configs = ["debug", "release"]
all_configs = ["release"]

arch_per_os = {
    "linux": ["x86_64"],
    "macos": ["x86_64", "arm64"],
    "windows": ["x86_64", "i686"],
}

exts_per_os = {
    "linux": [".so"],
    "macos": [".dylib"],
    "windows": [".dll", ".dll.lib"],
}
prefix_per_os = {
    "linux": "lib",
    "macos": "lib",
    "windows": "",
}


def download_and_extract_zip(os, arch, config, extract_headers):
    url = f"{base_url}/{git_tag}/wgpu-{os}-{arch}-{config}.zip"
    print(f"Downloading {url}...")
    with urlopen(url) as f:
        with ZipFile(BytesIO(f.read())) as zipfile:
            print(zipfile.namelist())
            prefix = prefix_per_os[os]
            for ext in exts_per_os[os]:
                libfilename = f"{prefix}wgpu_native{ext}"
                path = join(destination, "bin", f"{os}-{arch}")
                print(f"Extracting {libfilename} to {path}...")
                zipfile.extract(libfilename, path)
            if extract_headers:
                path = join(destination, "include", "webgpu")
                print(f"Extracting webgpu.h and wgpu.h to {path}...")
                zipfile.extract("webgpu.h", path)
                zipfile.extract("wgpu.h", path)

def main():
    extract_headers = True
    for os, all_archs in arch_per_os.items():
        for arch in all_archs:
            for config in all_configs:
                download_and_extract_zip(os, arch, config, extract_headers)
                extract_headers = False

    with open(join(destination, "wgpu-native-git-tag.txt"), 'w', encoding="utf-8") as f:
        f.write(f"{git_tag}\n")

if __name__ == "__main__":
    main()
