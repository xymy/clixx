import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

src_dir = Path(__file__).resolve().parents[1].joinpath("src")
sys.path.insert(0, os.fsdecode(src_dir))
import clixx as pkg

parser = argparse.ArgumentParser()
parser.add_argument("--clean", action="store_true", help="clean the build directory")
parser.add_argument("--dist", action="store_true", help="build a distribution")
args = parser.parse_args()

docs_dir = Path(__file__).resolve().parent
build_dir = docs_dir / "build"
dist_dir = docs_dir / "dist"
doctrees_dir = build_dir / "doctrees"
source_dir = docs_dir / "source"
html_dir = build_dir / "html"

if args.clean and build_dir.exists():
    shutil.rmtree(build_dir)
subprocess.run([sys.executable, "-m", "sphinx.cmd.build", "-b", "html", "-d", doctrees_dir, source_dir, html_dir])

if args.dist:
    dist_dir.mkdir(parents=True, exist_ok=True)
    name = f"{pkg.__title__}-{pkg.__version__}-docs"
    with tarfile.open(dist_dir / f"{name}.tar.xz", "w:xz") as tar:
        tar.add(html_dir, name)
