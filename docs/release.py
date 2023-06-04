import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from rich.console import Console
from rich.markup import escape

src_dir = Path(__file__).resolve().parents[1].joinpath("src")
sys.path.insert(0, os.fsdecode(src_dir))
import clixx as pkg

parser = argparse.ArgumentParser()
parser.add_argument("--clean", action="store_true", help="clean the build directory")
parser.add_argument("--dist", action="store_true", help="build a distribution")
args = parser.parse_args()

console = Console(soft_wrap=True, emoji=False, highlight=False)

docs_dir = Path(__file__).resolve().parent
source_dir = docs_dir / "source"
build_dir = docs_dir / "build"
html_dir = build_dir / "html"
doctrees_dir = build_dir / "doctrees"

if args.clean and build_dir.exists():
    shutil.rmtree(build_dir)
    console.print(f"[b blue]Clean the build directory [u]{escape(str(build_dir))}[/u][/b blue]")

subprocess.run([sys.executable, "-m", "sphinx.cmd.build", "-b", "html", "-d", doctrees_dir, source_dir, html_dir])

if args.dist:
    dist_dir = docs_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_name = f"{pkg.__title__}-{pkg.__version__}-docs"
    dist_path = dist_dir / f"{dist_name}.tar.xz"

    with tarfile.open(dist_path, "w:xz") as tar:
        tar.add(html_dir, dist_name)
    console.print(f"[b green]Build a distribution [u]{escape(str(dist_path))}[/u][/b green]")
