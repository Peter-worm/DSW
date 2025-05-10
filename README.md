Hello

### Large-file prerequisite (Git LFS)

This repository stores the 58 MB **`warsaw.pbf`** map with **Git LFS**.
Before you clone or pull, install LFS once:

```bash
# macOS
brew install git-lfs
# Debian / Ubuntu
sudo apt-get install git-lfs
# Windows
winget install --id GitHub.GitLFS

git lfs install          # sets up local hooks
```

After that, `git clone …` and `git pull` automatically fetch the full map file; no extra steps required.

