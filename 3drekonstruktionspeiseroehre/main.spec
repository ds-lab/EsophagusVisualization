# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from pathlib import Path
import os
import sys
import glob

# Include data files from dash_daq and dash_extensions (e.g., package-info.json)
dash_daq_datas = collect_data_files('dash_daq', include_py_files=False)
dash_extensions_datas = collect_data_files('dash_extensions', include_py_files=False)

# Collect VTK/VC++ runtime DLLs from the active conda environment (Library/bin)
conda_prefix = os.environ.get('CONDA_PREFIX', sys.prefix)
vtk_bin_dir = os.path.join(conda_prefix, 'Library', 'bin')
extra_binaries = []
if os.path.isdir(vtk_bin_dir):
    dll_patterns = ['*.dll', 'tbb*.dll', 'tbbmalloc*.dll', 'tbbmalloc_proxy*.dll']
    for pattern in dll_patterns:
        for dll_path in glob.glob(os.path.join(vtk_bin_dir, pattern)):
            # Lege alle DLLs direkt neben die EXE (Windows-Suchreihenfolge bevorzugt EXE-Verzeichnis)
            extra_binaries.append((dll_path, '.'))

# Always also collect VTK DLLs from site-packages (pip wheel layout)
try:
    import vtkmodules as _vtkmods
    vtk_site_dir = Path(_vtkmods.__file__).resolve().parent
    vtklibs_dir = vtk_site_dir.parent / 'vtk.libs'
    patterns = [
        'vtk*.dll',
        'tbb*.dll',
        'tbbmalloc*.dll',
        'tbbmalloc_proxy*.dll',
        'msvcp140*.dll',
        'vcruntime140*.dll',
        'concrt140*.dll',
        'vcomp140*.dll',
    ]
    for base_dir in (vtk_site_dir, vtklibs_dir):
        if base_dir.is_dir():
            for pat in patterns:
                for dll in base_dir.rglob(pat):
                    extra_binaries.append((str(dll), '.'))
except Exception:
    pass

# Collect all vtkmodules (datas, binaries, hidden imports)
vtk_datas, vtk_binaries, vtk_hidden_all = collect_all('vtkmodules')
vtk_hidden = collect_submodules('vtkmodules')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=extra_binaries + vtk_binaries,
    datas=[
        ('ui-files', 'ui-files'),
        ('media', 'media'),
        ('logic', 'logic'),
        ('gui', 'gui'),
        ('config.py', '.'),
        ('disclaimer.txt', '.'),
    ] + dash_daq_datas + dash_extensions_datas + vtk_datas,
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'numpy'
    ] + vtk_hidden + vtk_hidden_all,
    hooksconfig={},
    excludes=[
        'PySide6',
        'shiboken6',
        'PyQt5',
        'PySide2',
        'shiboken2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    'media\\splash_screen.jpg',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='EsophagusVisualization',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='media\\icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash.binaries,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='main',
)
