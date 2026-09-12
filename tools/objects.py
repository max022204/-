import struct,json
from pathlib import Path
class Reader:
 def __init__(self,b):self.b=b;self.p=0
 def n(self,fmt='i'):
  v=struct.unpack_from('<'+fmt,self.b,self.p);self.p+=struct.calcsize('<'+fmt);return v[0] if len(v)==1 else v
 def s(self):
  end=self.b.index(0,self.p);v=self.b[self.p:end];self.p=end+1;return v.decode('utf-8',errors='replace')
def ability_changes():
 r=Reader(Path('extracted/war3map.w3a').read_bytes());version=r.n();out={}
 for table in range(2):
  for _ in range(r.n()):
   old=r.n('4s').decode('latin1');new=r.n('4s').decode('latin1');id=new if new!='\0'*4 else old
   changes=[]
   for _ in range(r.n()):
    field=r.n('4s').decode('latin1');typ=r.n();level=r.n();data=r.n();value=r.s() if typ==3 else r.n('i' if typ==0 else 'f');end=r.n('4s')
    changes.append({'field':field,'level':level,'data':data,'value':value})
   out[id]={'base':old,'changes':changes}
 assert r.p==len(r.b),(r.p,len(r.b))
 Path('output/ability_overrides.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
 return out
def mapinfo():
 r=Reader(Path('extracted/war3map.w3i').read_bytes());version=r.n();assert version==25
 r.n();r.n()
 texts=[r.s() for _ in range(4)]
 r.n('8f');r.n('4i');r.n('2i');r.n();r.n('c');r.n()
 for _ in range(4):r.s()
 r.n();r.s()
 for _ in range(3):r.s()
 r.n();r.n('3f');r.n('4B');r.n();r.s();r.n('c');r.n('4B')
 n=r.n();players=[];data=bytearray(r.b)
 for _ in range(n):
  id=r.n();typeoffset=r.p;typ=r.n();race=r.n();fixed=r.n();name=r.s();x,y=r.n('2f');r.n('2I')
  players.append({'id':id,'type':typ,'name':name,'x':x,'y':y})
  if id in [7,8,9]:struct.pack_into('<i',data,typeoffset,2)
 Path('output/war3map_ai.w3i').write_bytes(data)
 Path('output/mapinfo.json').write_text(json.dumps({'texts':texts,'players':players},ensure_ascii=False,indent=2),'utf-8')
 print('mapinfo',n,'players',players)
if __name__=='__main__':
 print('ability overrides',len(ability_changes()));mapinfo()
