"""Build an isolated Reader tree from the pinned GER2; input stays untouched."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
from Cython import __version__ as cyversion

here=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('reader',type=Path)
p.add_argument('target',type=Path)
a=p.parse_args()
if a.target.exists(): raise SystemExit('target must be new')
if cyversion!='3.1.6': raise SystemExit('Cython 3.1.6 required')
pins=json.loads((here/'reader_hashes.json').read_text())
for name,sha in pins.items():
    if hashlib.sha256((a.reader/name).read_bytes()).hexdigest()!=sha: raise SystemExit(f'input mismatch: {name}')
root=a.target.resolve()
shutil.copytree(a.reader,root,ignore=shutil.ignore_patterns('__pycache__'))
mod=root/'geoenclosereader'
flags=['-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-msse2','-mfpmath=sse','-fPIC','-shared']
cc=os.environ.get('CC','gcc')
subprocess.run([cc,*flags,'-I'+sysconfig.get_path('include'),str(here/'kernel.c'),str(here/'cpython_fsum.c'),'-lm','-o',str(mod/'libtri4.so')],check=True)
shutil.copyfile(here/'native.py',mod/'_native_port.py')
# Preserve Python number types and source order in the control / AD layer.
import ast
def functions(filename,names):
    src=(mod/filename).read_text()
    definitions={n.name:ast.get_source_segment(src,n) for n in ast.parse(src).body if isinstance(n,ast.FunctionDef)}
    return '\n\n'.join(definitions[n] for n in names)
cells = "from .tri4 import I,D,J,PQF,_PQ_d,np\n"
cells += functions('tri3.py',['_common','_make']).replace('def _make(','def _masked_make(')
cells += '\n'+functions('tri4.py',['_PQ_any','_make','_mv_cells'])
(mod/'_cells.py').write_text(cells+'\n')
shutil.copyfile(here/'tiles.py',mod/'_tiles.py')
for name in ('dual','jet','_cells'):
    cfile=root/(name+'.c')
    subprocess.run([sys.executable,'-m','cython','-3','-X','infer_types=False,annotation_typing=False,binding=True',
                    '-o',str(cfile),str(mod/(name+'.py'))],check=True)
    subprocess.run([cc,*flags,'-I'+sysconfig.get_path('include'),str(cfile),'-lm','-o',
                    str(mod/(name+sysconfig.get_config_var('EXT_SUFFIX')))],check=True)
with (mod/'__init__.py').open('a') as f:
    f.write('\nfrom ._native_port import install as _install_port\n_install_port()\nfrom ._tiles import install as _install_tiles\n_install_tiles()\n')
print('Cython',cyversion)
subprocess.run([cc,'--version'],check=True)
print('flags',*flags)
