"""
This script automatically replaces the "stepXXX-next" branches of the
LearnWebGPU-Code repo with the tangled result.
Usage:
 1. Run make tangle to make sure it is up to date (optionally run make clean first)
 2. Run this script. It may prompt several time for your ssh passphrase
"""

import os
import re
import json
import subprocess
import shutil

from pathlib import Path

def main():
    guide_dir = Path(__file__).parent.parent
    root_dir = guide_dir.joinpath("_build", "tangle")
    git_dir = root_dir.joinpath("git-repo")
    repo_url = "https://github.com/eliemichel/LearnWebGPU-Code"

    setupAndUpdateGitClone(git_dir, repo_url)

    with open(root_dir.joinpath("metadata.json"), 'r') as f:
        metadata = json.load(f)

    branches_to_push = []

    for tangle_root in metadata["roots"]:
        tangle_dir = root_dir.joinpath(tangle_root)
        branch_name = buildBranchName(tangle_root)
        if not branch_name.endswith("-next"):
            # We only deal with "next" branches here. Other branches are manually released.
            continue
        
        switchToBranch(git_dir, branch_name)
        clearWorkingCopy(git_dir)
        copyContents(tangle_dir, git_dir)
        commitAllChanges(git_dir, message="Auto update from '" + getLatestCommitName(guide_dir) + "'")
        branches_to_push.append(branch_name)
        
    runCmd(
        [ "git", "push", "-u", "origin", *branches_to_push ],
        cwd=str(git_dir)
    )

#################################################

def copyContents(src_dir, dst_dir):
    """Copy the content of src_dir into dst_dir"""
    for child in src_dir.iterdir():
        if child.name.startswith("build") or child.name == ".vscode":
            continue
        if child.is_dir():
            shutil.copytree(child, dst_dir.joinpath(child.name))
        else:
            shutil.copy(child, dst_dir.joinpath(child.name))

#################################################

def buildBranchName(tangle_root):
    step_index, name, *variants = tangle_root.split(" - ")
    tokens = [ f"step{step_index}" ] + sortVariants([ normalizeVariant(var) for var in variants ])
    return "-".join(tokens)

def normalizeVariant(var):
    var = var.lower()
    var = re.sub(' (.)', lambda m: m.group(1).upper(), var)
    return var

def sortVariants(variants):
    return sorted(variants, key=lambda x: x == "next")

#################################################

def setupAndUpdateGitClone(git_dir, repo_url):
    if git_dir.is_dir():
        runCmd(
            [ "git", "reset", "--hard" ],
            cwd=str(git_dir)
        )
        runCmd(
            [ "git", "checkout", "main" ],
            cwd=str(git_dir)
        )
        runCmd(
            [ "git", "pull" ],
            cwd=str(git_dir)
        )
    else:
        runCmd(
            [ "git", "clone", repo_url, git_dir.name ],
            cwd=str(git_dir.parent)
        )

#################################################

def switchToBranch(git_dir, branch_name):
    try:
        runCmd(
            [ "git", "checkout", branch_name ],
            cwd=str(git_dir)
        )
    except subprocess.CalledProcessError:
        runCmd(
            [ "git", "checkout", "main" ],
            cwd=str(git_dir)
        )
        runCmd(
            [ "git", "checkout", "-b", branch_name ],
            cwd=str(git_dir)
        )

#################################################

def commitAllChanges(git_dir, message=None):
    runCmd(
        [ "git", "add", "." ],
        cwd=str(git_dir)
    )
    cmd = [ "git", "commit" ]
    if message is not None:
        cmd += [ "-m", message ]
    try:
        runCmd(
            cmd,
            cwd=str(git_dir)
        )
    except subprocess.CalledProcessError:
        pass  # probably because nothing to commit (TODO: check)

#################################################

def clearWorkingCopy(git_dir):
    """Remove everything by .git"""
    for child in git_dir.iterdir():
        if child.name == ".git":
            continue
        elif child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

#################################################

def getLatestCommitName(git_dir):
    proc = runCmd(
        [ "git", "show", "-s", "--format=%s" ],
        cwd=str(git_dir),
        capture_output=True,
    )
    return proc.stdout.decode().strip()

#################################################

def runCmd(cmd, **kwargs):
    print(cmd)
    return subprocess.run(cmd, check=True, **kwargs)

#################################################

if __name__ == "__main__":
    main()
