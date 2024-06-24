import subprocess

# Config
clone_root = r"G:\SourceCode\LearnWebGPU-Code-folded"
cherry_picked_commit = "1957beb"
all_branches = [
    #"step000",
    #"step001",
    "step005",
    "step010",
    "step015",
    "step020",
    "step025",
    "step028",
    "step030",
    "step030-vanilla",
    "step031",
    "step031-vanilla",
    "step032",
    "step032-vanilla",

    #"step030-headless",
    #"step030-sdl",
    #"step030-sdl-c",

    #"step033",
    #"step033-optionB",
    #"step034",
    #"step037",
    #"step039",
    #"step043",
    #"step044",
    #"step050",
    #"step052",
    #"step054",
    #"step055",
    #"step056",
    #"step058",
    #"step060",
    #"step065",
    #"step070",
    #"step075",
    #"step080",
    #"step085",
    #"step090",
    #"step095",
    #"step095-emscripten",
    #"step095-timestamp-queries",
    #"step100",
    #"step100-gltf",
    #"step105",
    #"step110",
    #"step110-next",
    #"step115",
    #"step117",
    #"step120",
    #"step125",
    #"step200",
    #"step201",
    #"step210",
    #"step211",
    #"step215",
    #"step220",
    #"step222",
    #"step240",
]
excluded_branches = [
    'main',
    'step240',
]

git = lambda *x: subprocess.run(["git", '-C', clone_root, *x], capture_output=True)

def main():
    global all_branches
    print(f"Applying commit '{cherry_picked_commit}' to all branches but " + ", ".join(excluded_branches))

    if all_branches is None:
        res = git("for-each-ref", "--format=%(refname:short)", "refs/heads/")
        all_branches = res.stdout.decode().strip().split("\n")
    res = git("show-ref", "--head", "--hash", "HEAD")
    current_head = res.stdout.decode().strip()
    
    processed_branches = []
    for branch in all_branches:
        if branch in excluded_branches:
            continue
        print(f"Processing branch '{branch}'...")
        git("checkout", branch)
        res = git("cherry-pick", cherry_picked_commit, "-m", "1")
        if res.returncode != 0:
            print(f"Cannot cherry pick for branch '{branch}':")
            print(res.stderr.decode())
            return
        processed_branches.append(branch)

    git("checkout", current_head)
    #git("push", "origin", *processed_branches)
    print(f"Run 'git push origin {' '.join(processed_branches)}'")

main()
