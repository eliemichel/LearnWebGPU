from urllib.request import urlopen
import json
from zipfile import ZipFile
from io import BytesIO
from os.path import join, isfile
import os
import shutil

#################################################

def makeParser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="prepare_wgpu_release",
        description="Get artifacts from a CD workflow and prepare the associated GitHub release.",
    )

    parser.add_argument(
        '-r', '--repo',
        type=str, default="eliemichel/wgpu-native",
        help="repository from which we get artifacts, in the form OWNER/REPO"
    )

    parser.add_argument(
        '-c', '--cache',
        type=str, default="C:/tmp/prepare_wgpu_release/cache",
        help="Location where artifacts are cached"
    )

    return parser

#################################################

def main(args):
    run_id = findLastCdRunId(args)
    res = apiGet(args, f"actions/runs/{run_id}/artifacts")
    for art in res["artifacts"]:
        downloadArtifact(args, art)

#################################################

def apiGet(args, path):
    endpoint = f"https://api.github.com/repos/{args.repo}"
    url = endpoint + "/" + path
    with urlopen(url) as f:
        return json.load(f)

#################################################

def findWorkflowId(args, workflow_name):
    workflow_id = None
    res = apiGet(args, "actions/workflows")
    for w in res["workflows"]:
        if w["name"] == "CD":
            workflow_id = w["id"]

    if workflow_id is None:
        raise Exception(f"Could not find ID for workflow 'CD' in repository {args.repo}")
    return workflow_id

#################################################

def findLastCdRunId(args):
    workflow_id = findWorkflowId(args, "CD")
    res = apiGet(args, f"actions/workflows/{workflow_id}/runs?status=success&per_page=1")
    run = res["workflow_runs"][0]
    return run["id"]

def downloadArtifact(args, artifact):
    art_dir = join(args.cache, "run", str(artifact["workflow_run"]["id"]))
    os.makedirs(art_dir, exist_ok=True)

    name = artifact["name"]
    path = join(art_dir, name)
    if isfile(path):
        return

    url = artifact["archive_download_url"]
    print(f"Downloading artifact '{name}' from '{url}'...")
    with open(path, 'wb') as f_out:
        with urlopen(url) as f_in:
            shutil.copyfileobj(f_in, f_out)

#################################################

if __name__ == "__main__":
    parser = makeParser()
    main(parser.parse_args())

def download_and_extract_zip(os, arch, config, extract_headers):
    url = f"{base_url}/{git_tag}/wgpu-{os}-{arch}-{config}.zip"
    print(f"Downloading {url}...")
    with urlopen(url) as f:
        with ZipFile(BytesIO(f.read())) as zipfile:
            print(zipfile.namelist())
            prefix = prefix_per_os[os]
            for ext in exts_per_os[os]:
                libfilename = f"lib/{prefix}wgpu_native{ext}"
                path = join(destination, "bin", f"{os}-{arch}")
                print(f"Extracting {libfilename} to {path}...")
                zipfile.extract(libfilename, path)
            if extract_headers:
                path = join(destination, "include", "webgpu")
                print(f"Extracting webgpu.h and wgpu.h to {path}...")
                zipfile.extract("include/webgpu.h", path)
                zipfile.extract("include/wgpu.h", path)
