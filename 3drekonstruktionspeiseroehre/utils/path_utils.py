import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
	"""
	Resolve resource path for both source and PyInstaller builds.

	- In a frozen build, prefer the executable directory, then _internal fallback
	- In source, resolve relative to project root (two levels up from this file)
	"""
	# Normalize input to use OS-specific separators
	relative_path = relative_path.replace("/", os.sep).replace("\\", os.sep)

	# Frozen (PyInstaller)
	if getattr(sys, "frozen", False):
		# Exe directory
		base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
		candidate = base_dir / relative_path
		if candidate.exists():
			return str(candidate)
		# Fallback: some datas may end up under _internal
		internal = base_dir / "_internal" / relative_path
		if internal.exists():
			return str(internal)
		# Last resort: working directory
		return str(Path.cwd() / relative_path)

	# Source run: project root = two levels up from this file
	project_root = Path(__file__).resolve().parents[1]
	return str(project_root / relative_path)


