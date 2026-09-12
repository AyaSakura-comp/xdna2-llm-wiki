"""Read-only literal AIE2P register/event source index; never access hardware."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'sources/mlir-aie/third_party/aie-rt'
COMMIT='8849e208bdcc533b20a0ed3f95c1ce961dee9c3a'
FILES=['driver/src/global/xaie2pgbl_params.h','driver/src/events/xaie_events_aie2p.h']

def parse_defines(text,url):
 rows=[];lines=text.splitlines();i=0
 while i<len(lines):
  start=i+1;raw=lines[i];i+=1
  while raw.rstrip().endswith('\\') and i<len(lines):
   raw+='\n'+lines[i];i+=1
  match=re.match(r'#define\s+((?:XAIE2PGBL_|XAIE2P_EVENTS_)\w+)\s+(.+)',raw,re.S)
  if not match:continue
  name,expr=match.groups();expr=expr.strip()
  literal=re.fullmatch(r'(0[xX][0-9a-fA-F]+|[0-9]+)[uUlL]*',expr)
  value=str(int(literal[1],16 if literal[1].lower().startswith('0x') else 10)) if literal else None
  rows.append({'name':name,'expression':expr,'integer_decimal':value,'line_start':start,'line_end':i,'source_url':f'{url}#L{start}-L{i}'})
 return rows

def extract():
 sources=[];records=[]
 for name in FILES:
  raw=subprocess.check_output(['git','-C',str(REPO),'show',f'{COMMIT}:{name}']);url=f'https://github.com/Xilinx/aie-rt/blob/{COMMIT}/{name}'
  rows=parse_defines(raw.decode(),url)
  for r in rows:r['source_path']=name
  sources.append({'path':name,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'record_count':len(rows)})
  records+=rows
 return {'schema_version':1,'architecture':'AIE2P / XDNA2 (arch21)','evidence_class':'pinned_runtime_register_event_source','source_commit':COMMIT,'scope':'Every prefixed object-like macro in the two listed headers, including offsets, masks, field widths/defaults and event IDs. A macro is not necessarily a register; this is not a silicon-complete MMIO manual or a safe register-write API. Source expressions are preserved, not evaluated. Numeric decimal values are strings to preserve 128-bit masks. Event IDs are NOT cycle counts.','sources':sources,'records':records}

if __name__=='__main__':
 data=extract();out=ROOT/'wiki/spec-data/registers-events.json';out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(f'{len(data["records"])} source macros -> {out}')
