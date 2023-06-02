import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from rich.console import Console

src_dir = Path(__file__).resolve().parents[1].joinpath("src")
sys.path.insert(0, os.fsdecode(src_dir))
import clixx as pkg

parser = argparse.ArgumentParser()
parser.add_argument("--clean", action="store_true", help="clean the build directory")
parser.add_argument("--dist", action="store_true", help="build a distribution")
args = parser.parse_args()

console = Console()

docs_dir = Path(__file__).resolve().parent
build_dir = docs_dir / "build"
dist_dir = docs_dir / "dist"
doctrees_dir = build_dir / "doctrees"
source_dir = docs_dir / "source"
html_dir = build_dir / "html"

if args.clean and build_dir.exists():
    shutil.rmtree(build_dir)
    console.print(f"[bold bright_white]Clean the build directory {build_dir}[/bold bright_white]")

subprocess.run([sys.executable, "-m", "sphinx.cmd.build", "-b", "html", "-d", doctrees_dir, source_dir, html_dir])

if args.dist:
    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_name = f"{pkg.__title__}-{pkg.__version__}-docs"
    dist_path = dist_dir / f"{dist_name}.tar.xz"
    with tarfile.open(dist_path, "w:xz") as tar:
        tar.add(html_dir, dist_name)
    console.print(f"[bold bright_white]Build a distribution {dist_path}[/bold bright_white]")
