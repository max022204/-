import ctypes as c
from pathlib import Path
d=c.WinDLL(str(Path(__file__).resolve().parent/'stormlib/x64/StormLib.dll'),use_last_error=True)
signatures={'SFileOpenArchive':[c.c_wchar_p,c.c_uint32,c.c_uint32,c.POINTER(c.c_void_p)],'SFileOpenFileEx':[c.c_void_p,c.c_char_p,c.c_uint32,c.POINTER(c.c_void_p)],'SFileGetFileSize':[c.c_void_p,c.POINTER(c.c_uint32)],'SFileReadFile':[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_void_p],'SFileCloseFile':[c.c_void_p],'SFileCloseArchive':[c.c_void_p]}
for n,args in signatures.items():
 f=getattr(d,n);f.argtypes=args;f.restype=c.c_uint32 if n=='SFileGetFileSize' else c.c_bool
class MPQ:
 def __init__(self,path):
  self.h=c.c_void_p();assert d.SFileOpenArchive(str(Path(path).resolve()),0,0x100,c.byref(self.h)),c.get_last_error()
 def read(self,name):
  f=c.c_void_p()
  if not d.SFileOpenFileEx(self.h,name.encode(),0,c.byref(f)):return None
  try:
   size=d.SFileGetFileSize(f,None)
   if size==0xffffffff or size>200000000:raise ValueError(size)
   b=c.create_string_buffer(size);n=c.c_uint32()
   assert d.SFileReadFile(f,b,size,c.byref(n),None),c.get_last_error()
   return b.raw[:n.value]
  finally:d.SFileCloseFile(f)
 def close(self):d.SFileCloseArchive(self.h)
if __name__=='__main__':
 for p in ['output/original.w3x','C:/Program Files (x86)/War3 v1.29c/War3x.mpq','C:/Program Files (x86)/War3 v1.29c/War3.mpq']:
  m=MPQ(p)
  for name in ['common.j','blizzard.j','Scripts\\common.j','Scripts\\Blizzard.j','Units\\MiscData.txt','war3mapMisc.txt']:
   data=m.read(name)
   dest=Path('extracted',name.replace('\\','_'))
   if data and not dest.exists():dest.write_bytes(data);print(p,name,len(data))
  m.close()
