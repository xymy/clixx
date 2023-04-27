import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

src_dir = Path(__file__).resolve().parents[1].joinpath("src")
sys.path.insert(0, os.fsdecode(src_dir))
import clixx as pkg  # noqa

parser = argparse.ArgumentParser()
parser.add_argument("--clean", action="store_true", help="clean build directory before building")
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

dist_dir.mkdir(parents=True, exist_ok=True)
name = f"{pkg.__title__}-{pkg.__version__}-doc"
with tarfile.open(dist_dir / f"{name}.tar.gz", "w:gz") as tar:
    tar.add(html_dir, name)
