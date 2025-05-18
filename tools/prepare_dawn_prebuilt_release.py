"""
Usage:
 1. Update the VERSION_NAME below
 2. Download all artefacts from the CI run that you want to release
 3. Run this script from the directory where artefact zips were downloaded
 4. Release zips are in out/
"""

import os
import re
from zipfile import ZipFile, ZipInfo
import tarfile

VERSION_NAME = "7187"

release_filename_re = re.compile(r"Dawn-([^-]*)-(.*)-(Debug|Release)\.zip")

def main():
    for filename in os.listdir():
        if match := release_filename_re.match(filename):
            osname, arch = {
                "macos-13": ("macos", "x64"),
                "macos-latest": ("macos", "aarch64"),
                "ubuntu-latest": ("linux", "x64"),
                "windows-latest": ("windows", "x64"),
            }[match.groups()[1]]
            config = match.groups()[2]
            os.makedirs("out", exist_ok=True)
            destination = f"out/Dawn-{VERSION_NAME}-{osname}-{arch}-{config}.zip"
            print(f"Packaging '{destination}'...")
            processZip(filename, destination)

def processZip(filename, destination):
    with ZipFile(filename, 'r') as zf_in:
        [ tar_filename ] = zf_in.namelist()
        with zf_in.open(tar_filename) as tff:
            tf = tarfile.open(fileobj=tff)
            with ZipFile(destination, 'w') as zf_out:
                copyTarToZip(tf, zf_out)

def copyTarToZip(source_tar, destination_zip):
    for member in source_tar:
        if not member.isfile():
            continue
        zinfo = ZipInfo(filename=member.name.split("/", 1)[1])
        data = source_tar.extractfile(member).read()
        destination_zip.writestr(zinfo, data)

if __name__ == "__main__":
    main()
