"""Package and verify AI8 in output; never install or overwrite the source map."""
import ctypes as c
import hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
from mpq import MPQ,d

BASE=Path('output/backups/AI5_baseline.w3x')
DEST=Path('output/000羈絆7.3.7_AI版_八人守城.w3x')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before=sha(BASE)
    assert before=='8d84f50b3f87704976ed6035247402cd1cd0bd4df351b017917ae071e659633c','Unexpected AI5 baseline'
    subprocess.run([sys.executable,'tools/prepare_ai8.py'],check=True,capture_output=True)
    subprocess.run([sys.executable,'tools/test_ai8.py'],check=True)
    proc=subprocess.run(['tools/pjass.exe','extracted/Scripts_common.j','extracted/Scripts_Blizzard.j','output/war3map_ai8.j'],capture_output=True)
    Path('output/ai8_jass_check.txt').write_bytes(proc.stdout+proc.stderr)
    assert proc.returncode==0,proc.stdout.decode(errors='replace')
    draft=json.loads(Path('output/ai8_draft_manifest.json').read_text('utf-8'))
    entries={'war3map.j':Path('output/war3map_ai8.j'),'war3map.w3i':Path('output/war3map_ai8.w3i')}
    assert sha(entries['war3map.j'])==draft['script_sha256']
    assert sha(entries['war3map.w3i'])==draft['lobby_sha256']
    temp=DEST.with_suffix('.building.w3x')
    shutil.copyfile(BASE,temp)
    d.SFileAddFileEx.argtypes=[c.c_void_p,c.c_wchar_p,c.c_char_p,c.c_uint32,c.c_uint32,c.c_uint32]
    d.SFileAddFileEx.restype=c.c_bool
    handle=c.c_void_p()
    assert d.SFileOpenArchive(str(temp.resolve()),0,0,c.byref(handle)),c.get_last_error()
    try:
        for name,path in entries.items():
            assert d.SFileAddFileEx(handle,str(path.resolve()),name.encode(),0x80000200,2,2),c.get_last_error()
    finally:d.SFileCloseArchive(handle)
    base=MPQ(BASE);built=MPQ(temp)
    count=0
    try:
        original=base.read('war3map.j')
        assert original==Path('output/backups/ai5_script.j').read_bytes(),'Extracted source differs from archive'
        for name,path in entries.items():assert built.read(name)==path.read_bytes(),name
        names=set((base.read('(listfile)') or b'').decode('utf-8',errors='replace').splitlines())
        names.update(['war3map.w3e','war3map.wpm','war3map.doo','war3mapUnits.doo','war3map.shd','war3map.w3a','war3map.w3b','war3map.w3d','war3mapMisc.txt'])
        names.update('Units\\'+p.name.removeprefix('Units_') for p in Path('extracted').glob('Units_*'))
        names.update(m.replace('\\\\','\\') for m in re.findall(r'"([^"\r\n]+\.(?:mdx|mdl|blp|tga|wav|mp3|toc|lua))"',original.decode('latin1'),re.I))
        for name in sorted(names):
            if not name or name in entries or name=='(listfile)':continue
            data=base.read(name)
            if data is not None:
                assert built.read(name)==data,'Resource changed: '+name
                count+=1
    finally:
        base.close();built.close()
    assert sha(BASE)==before,'Baseline changed'
    if DEST.exists():
        assert sha(DEST)==sha(temp),'Existing output differs; choose a new version filename'
        temp.unlink()
    else:temp.rename(DEST)
    report=dict(draft,packaged=True,map_path=str(DEST.resolve()),map_sha256=sha(DEST),base_sha256=before,
                modified_entries=list(entries),resources_compared=count,jass_passed=True,
                policy_tests_passed=json.loads(Path('output/ai8_policy_tests.json').read_text('utf-8'))['passed'],runtime_tested=False)
    Path('output/ai8_package_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({k:report[k] for k in ['map_path','map_sha256','resources_compared','jass_passed','policy_tests_passed','runtime_tested']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
