"""Verify actual NDK compilation commands rather than assuming a build is optimized."""
import argparse
import json
from pathlib import Path
import shlex

def verify(root):
    required={'camera.cpp','SkinnedMesh.cpp','WeightBuffer.cpp'};seen=set()
    for path in (root/'android/native').rglob('compile_commands.json'):
        for row in json.loads(path.read_text()):
            name=Path(row['file']).name
            if name not in required:continue
            args=row.get('arguments') or shlex.split(row['command'])
            opt=[a for a in args if a in ('-O0','-O1','-O2','-O3','-Og','-Os','-Oz')]
            if not opt or opt[-1]!='-O3' or '-DNDEBUG' not in args:
                raise ValueError('Unoptimized native unit: '+name+' '+str(opt))
            seen.add(name)
    if seen!=required:raise ValueError('Missing actual compilation evidence: '+str(required-seen))
    return {'native_build':'Release','native_optimization':'O3','ndebug':True,'checked_units':sorted(seen)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();report=verify(a.root);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
