import ctypes as c
from pathlib import Path
d=c.WinDLL(str(Path('tools/stormlib/x64/StormLib.dll').resolve()),use_last_error=True)
d.SFileOpenArchive.argtypes=[c.c_wchar_p,c.c_uint32,c.c_uint32,c.POINTER(c.c_void_p)]
d.SFileOpenFileEx.argtypes=[c.c_void_p,c.c_char_p,c.c_uint32,c.POINTER(c.c_void_p)]
d.SFileGetFileSize.argtypes=[c.c_void_p,c.POINTER(c.c_uint32)]
d.SFileGetFileSize.restype=c.c_uint32
d.SFileReadFile.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_void_p]
d.SFileCloseFile.argtypes=[c.c_void_p]
d.SFileCloseArchive.argtypes=[c.c_void_p]
for fn in ['SFileOpenArchive','SFileOpenFileEx','SFileReadFile','SFileCloseFile','SFileCloseArchive']:
 getattr(d,fn).restype=c.c_bool
h=c.c_void_p()
assert d.SFileOpenArchive(str(Path('output/original.w3x').resolve()),0,0x100,c.byref(h)),c.get_last_error()
names=['(listfile)','war3map.j','scripts\\war3map.j','war3map.wts','war3map.w3u','war3map.w3t','war3map.w3a','war3map.w3q','war3map.w3i','war3map.w3b','war3map.w3d','war3map.w3h']
names += ['Units\\'+n+'.slk' for n in ['UnitData','UnitBalance','UnitAbilities','UnitUI','UnitWeapons','ItemData','AbilityData','AbilityBuffData','UpgradeData']]
names += ['Units\\'+race+kind+'.txt' for race in ['Human','Orc','Undead','NightElf','Neutral','Campaign','Common','Item'] for kind in ['UnitStrings','UnitFunc','AbilityStrings','AbilityFunc','Strings','Func']]
for name in names:
 f=c.c_void_p()
 if not d.SFileOpenFileEx(h,name.encode(),0,c.byref(f)):
  print(name,'MISSING',c.get_last_error());continue
 size=d.SFileGetFileSize(f,None)
 if size==0xffffffff or size>100000000:
  print(name,'INVALID SIZE',size);d.SFileCloseFile(f);continue
 buf=c.create_string_buffer(size);read=c.c_uint32()
 ok=d.SFileReadFile(f,buf,size,c.byref(read),None)
 print(name,size,ok,read.value,c.get_last_error())
 if ok:Path('extracted',name.replace('\\','_')).write_bytes(buf.raw[:read.value])
 d.SFileCloseFile(f)
d.SFileCloseArchive(h)
