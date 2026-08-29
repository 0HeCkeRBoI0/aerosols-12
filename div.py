from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime, timedelta, timezone
import hashlib, json, os, re, secrets, threading

ROOT=Path(__file__).parent; DATA_DIR=ROOT/'data'; STORE=DATA_DIR/'samadhan.json'; LOCK=threading.Lock()
PASSWORD=os.environ.get('SAMADHAN_DEMO_PASSWORD','Samadhan123!'); SLA={'CRITICAL':1,'HIGH':3,'MEDIUM':7,'LOW':14}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def stamp(days=0): return (datetime.now(timezone.utc)+timedelta(days=days)).replace(microsecond=0).isoformat()
def parse(v): return datetime.fromisoformat(v.replace('Z','+00:00'))
def date(v): return parse(v).strftime('%d %b %Y')
def digest(v): return hashlib.sha256(v.encode()).hexdigest()

def organizations(): return [
 {'id':'ORG-BIT','name':'BIT Mesra','type':'University','district':'Ranchi','domains':['Water Management','Environment','Urban Development','Energy'],'expertise':['IoT','Civil Engineering','Water Resources','Data Analytics','Environmental Engineering'],'capabilities':['Field pilots','Research','Prototyping'],'demo':True},
 {'id':'ORG-IITISM','name':'IIT (ISM) Dhanbad','type':'University','district':'Dhanbad','domains':['Energy','Environment','Urban Development'],'expertise':['Mining','Environmental Engineering','Data Analytics','IoT'],'capabilities':['Research','Technical review'],'demo':True},
 {'id':'ORG-BAU','name':'Birsa Agricultural University','type':'University','district':'Ranchi','domains':['Agriculture','Rural Livelihoods','Water Management'],'expertise':['Agronomy','Irrigation','Rural Extension'],'capabilities':['Field pilots','Community outreach'],'demo':True},
 {'id':'ORG-RMC','name':'Ranchi Municipal Corporation','type':'Government Department','district':'Ranchi','domains':['Urban Development','Water Management','Public Administration'],'expertise':['Civic Works','Civil Engineering','Sanitation','Water Services'],'capabilities':['Implementation','Public works'],'demo':True},
 {'id':'ORG-CUJ','name':'Central University of Jharkhand','type':'University','district':'Ranchi','domains':['Education','Accessibility','Public Administration'],'expertise':['Social Research','Accessibility','Policy'],'capabilities':['Research','Community outreach'],'demo':True},
 {'id':'ORG-HEALTH','name':'Jharkhand Health Innovation Cell','type':'Government Department','district':'Ranchi','domains':['Healthcare'],'expertise':['Public Health','Health Systems','Data Analytics'],'capabilities':['Implementation','Technical review'],'demo':True}]

def analysis(title,description,category=''):
 text=f'{title} {description} {category}'.lower(); rules=[
 ('Water Management',['water','tank','overflow','drain','supply','irrigation'],'Water infrastructure and monitoring',['IoT','Civil Engineering','Water Resources','Data Analytics'],['Water-level monitoring','Leak detection','Community maintenance']),
 ('Healthcare',['health','clinic','hospital','medicine','malaria','doctor'],'Community health access',['Public Health','Health Systems','Data Analytics'],['Service access','Awareness','Monitoring']),
 ('Agriculture',['farm','crop','farmer','soil','seed','agriculture'],'Farm resilience',['Agronomy','Irrigation','Rural Extension'],['Advisory','Irrigation','Market access']),
 ('Environment',['waste','pollution','forest','air','environment'],'Environmental quality',['Environmental Engineering','Data Analytics','Community Outreach'],['Monitoring','Waste management','Restoration']),
 ('Urban Development',['road','street','light','traffic','urban','drainage'],'Civic infrastructure',['Civic Works','Civil Engineering','IoT'],['Infrastructure repair','Safety audit','Monitoring']),
 ('Education',['school','student','teacher','education'],'Education access',['Education','Social Research','Accessibility'],['Access support','Learning resources','Community engagement'])]
 r=next((x for x in rules if any(k in text for k in x[1])),None); domain=category if category and category!='Other' else (r[0] if r else 'Public Administration')
 exp=r[3] if r else ['Public Administration','Community Outreach','Data Analytics']; areas=r[4] if r else ['Service redesign','Local coordination','Monitoring']
 priority='CRITICAL' if any(k in text for k in ['danger','emergency','death','flood','unsafe']) else 'HIGH' if any(k in text for k in ['water','health','school','urgent','overflow']) else 'MEDIUM'
 keys=[x.title() for x in re.findall(r'[a-zA-Z]{4,}',text) if x not in {'with','that','this','from','have','problem','people'}][:6]
 return {'domain':domain,'subdomain':r[2] if r else 'Civic service delivery','summary':f'{domain} case requiring a traceable response: {title}.','priority':priority,'confidence':92 if domain=='Water Management' else 86,'requiredExpertise':exp,'keywords':keys,'solutionAreas':areas}
def event(c,t,msg,actor='System'):
 e={'id':f'EVT-{secrets.token_hex(4).upper()}','challengeId':c['id'],'type':t,'message':msg,'actor':actor,'createdAt':now()}; c.setdefault('events',[]).append(e); return e
def note(data,recipient,msg,cid=None): data['notifications'].append({'id':f'NOT-{secrets.token_hex(3).upper()}','recipient':recipient,'message':msg,'challengeId':cid,'createdAt':now(),'read':False})
def matches(c,orgs):
 needed=set(c['aiAnalysis']['requiredExpertise']); domain=c['aiAnalysis']['domain']; out=[]
 for o in orgs:
  overlap=needed.intersection(o['expertise']); match=domain in o['domains']; score=min(98,48+(30 if match else 0)+len(overlap)*7+len(set(o['capabilities']).intersection({'Field pilots','Implementation','Research','Prototyping'}))*2)
  if match or overlap: out.append({'organizationId':o['id'],'score':score,'matchedExpertise':list(overlap),'why':'Strong domain and expertise overlap with the analysis.' if match else 'Relevant technical expertise overlaps with the analysis.'})
 return sorted(out,key=lambda x:x['score'],reverse=True)[:3]
def seed_case(cid,title,district,location,category,priority,status,deadline_days,oid=None,progress=0,people=0):
 ai=analysis(title,title,category); ai['priority']=priority; c={'id':cid,'title':title,'description':title,'district':district,'location':location,'category':category,'priority':priority,'affectedPeople':people,'evidence':[],'status':status,'createdAt':stamp(-12),'citizenEmail':'citizen@samadhan.demo','assignedOrganizationId':oid,'assignedAt':stamp(-10) if oid else None,'deadline':stamp(deadline_days) if oid else None,'progress':progress,'aiAnalysis':ai,'updates':[],'resolution':None,'verification':None,'matches':[],'events':[]}; event(c,'CHALLENGE_CREATED','Citizen report created.','Citizen'); event(c,'AI_ANALYZED',f'AI analysis completed: {ai["domain"]} / {priority}.');
 if oid:event(c,'ASSIGNED',f'Assigned to {oid}; deadline {date(c["deadline"])}.','Government')
 return c
def initial():
 flagship=seed_case('CH-GIR-001','Irregular Water Supply and Tank Overflow','Giridih','Barganda ward, Giridih','Water Management','HIGH','IN_PROGRESS',3,'ORG-BIT',65,350); flagship['description']='Repeated tank overflow and irregular water supply affect households in Barganda ward.'; flagship['updates']=[{'id':'UPD-GIR-01','progress':65,'text':'Prototype monitoring system installed and field testing started.','evidence':[],'createdAt':stamp(-1),'actor':'BIT Mesra'}]; event(flagship,'ACCEPTED','BIT Mesra accepted responsibility.','BIT Mesra'); event(flagship,'WORK_STARTED','Field work started.','BIT Mesra'); event(flagship,'PROGRESS_UPDATED','Progress updated to 65%: prototype installed.','BIT Mesra')
 overdue=seed_case('CH-DHN-002','Unsafe streetlight outage near bus stand','Dhanbad','Bank More bus stand','Urban Development','HIGH','IN_PROGRESS',-4,'ORG-RMC',30,180); event(overdue,'OVERDUE','Deadline passed; government attention required.')
 disputed=seed_case('CH-RAN-003','Community drain remains blocked after repair','Ranchi','Doranda','Environment','MEDIUM','DISPUTED',-1,'ORG-RMC',90,120); disputed['resolution']={'summary':'Drain cleaning completed.','whatWasDone':'Contractor cleared the visible blockage.','evidence':[],'peopleBenefited':120,'resolutionDate':stamp(-2),'submittedAt':stamp(-2),'organization':'Ranchi Municipal Corporation'}; disputed['verification']={'status':'REJECTED','comment':'Water still backs up after rainfall.','at':stamp(-1)}; event(disputed,'RESOLUTION_SUBMITTED','Resolution submitted for citizen verification.','Ranchi Municipal Corporation'); event(disputed,'DISPUTED','Citizen rejected the submitted resolution.','Citizen')
 active=seed_case('CH-RAM-004','Crop irrigation access for small farmers','Ramgarh','Gola block','Agriculture','MEDIUM','ACCEPTED',6,'ORG-BAU',20,75); event(active,'ACCEPTED','Birsa Agricultural University accepted responsibility.','Birsa Agricultural University')
 unassigned=seed_case('CH-KHU-005','Accessible ramp needed at community health centre','Khunti','Khunti Sadar','Accessibility','MEDIUM','ANALYZED',0,None,0,90)
 resolved=seed_case('CH-RES-006','Solar lighting restored at girls hostel','East Singhbhum','Jamshedpur','Energy','LOW','RESOLVED',0,'ORG-IITISM',100,220); resolved['resolution']={'summary':'Solar lighting and maintenance alerts installed.','whatWasDone':'Repaired solar units and installed maintenance alerts.','evidence':[],'peopleBenefited':220,'resolutionDate':stamp(-5),'organization':'Jharkhand Energy Innovation Cell'}; resolved['verification']={'status':'VERIFIED','comment':'Lighting is working.','at':stamp(-5)}; event(resolved,'VERIFIED','Citizen confirmed the resolution.','Citizen'); event(resolved,'CERTIFICATE_ISSUED','Verified certificate CERT-JH-2026-0001 issued.')
 cases=[flagship,overdue,disputed,active,unassigned,resolved]; orgs=organizations()
 for c in cases:c['matches']=matches(c,orgs)
 cert={'id':'CERT-JH-2026-0001','challengeId':'CH-RES-006','challengeTitle':resolved['title'],'location':'Jamshedpur, East Singhbhum','organization':'Jharkhand Energy Innovation Cell','resolution':'Solar lighting and maintenance alerts installed.','peopleBenefited':220,'resolutionDate':stamp(-5),'issuedAt':stamp(-5),'verified':True}
 users=[{'email':'citizen@samadhan.demo','password':digest(PASSWORD),'role':'CITIZEN','name':'Asha Kumari'},{'email':'bitmesra@samadhan.demo','password':digest(PASSWORD),'role':'ORGANIZATION','name':'BIT Mesra Desk','organizationId':'ORG-BIT'},{'email':'admin@samadhan.demo','password':digest(PASSWORD),'role':'GOVERNMENT','name':'Jharkhand Monitoring Desk'}]
 return {'users':users,'organizations':orgs,'challenges':cases,'complaints':[{'id':'CMP-2026-0001','challengeId':'CH-RAN-003','type':'Problem still exists','description':'Drain remains blocked after the reported repair.','evidence':[],'createdAt':stamp(-1),'status':'ESCALATED'}],'notifications':[],'certificates':[cert]}
def load():
 DATA_DIR.mkdir(exist_ok=True)
 if not STORE.exists(): data=initial(); save(data); return data
 try:return json.loads(STORE.read_text(encoding='utf-8'))
 except:return initial()
def save(data):
 DATA_DIR.mkdir(exist_ok=True); temp=STORE.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');temp.replace(STORE)
def get_org(data,oid):return next((x for x in data['organizations'] if x['id']==oid),None)
def get_case(data,cid):return next((x for x in data['challenges'] if x['id']==cid),None)
def get_user(data,email):return next((x for x in data['users'] if x['email']==email),None)
def deadline_state(c):
 if not c.get('deadline') or c['status'] in ('RESOLVED','DISPUTED'):return 'NORMAL'
 d=(parse(c['deadline'])-datetime.now(timezone.utc)).total_seconds()/86400; return 'OVERDUE' if d<0 else 'DUE_SOON' if d<=2 else 'NORMAL'
def view(data,c):
 out=dict(c);out['assignedOrganization']=get_org(data,c.get('assignedOrganizationId'));out['deadlineState']=deadline_state(c);out['complaints']=[x for x in data['complaints'] if x['challengeId']==c['id']];return out

class App(BaseHTTPRequestHandler):
 def sendit(self,status,payload,ctype='application/json'):
  raw=payload if isinstance(payload,bytes) else payload.encode();self.send_response(status);self.send_header('Content-Type',f'{ctype}; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def respond(self,status,obj):self.sendit(status,json.dumps(obj))
 def body(self):
  try:return json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
  except:return {}
 def actor(self,data):return get_user(data,self.headers.get('X-Samadhan-User','').lower())
 def do_GET(self):
  route=unquote(urlparse(self.path).path)
  if route in ('/','/landing.html'):return self.sendit(200,(ROOT/'landing.html').read_bytes(),'text/html')
  if route=='/app' or route.startswith('/case/'):return self.sendit(200,(ROOT/'app.html').read_bytes(),'text/html')
  if route.startswith('/verify/'):return self.sendit(200,(ROOT/'verify.html').read_bytes(),'text/html')
  if route in ('/how-it-works','/how-it-works.html'):return self.sendit(200,(ROOT/'how-it-works.html').read_bytes(),'text/html')
  if route in ('/partners','/partners.html'):return self.sendit(200,(ROOT/'partners.html').read_bytes(),'text/html')
  data=load()
  if route=='/api/me':
   u=self.actor(data);return self.respond(200,{'user':u}) if u else self.respond(401,{'error':'Sign in required'})
  if route=='/api/challenges':return self.respond(200,{'challenges':[view(data,c) for c in data['challenges']]})
  if route.startswith('/api/challenges/'):
   c=get_case(data,route.split('/')[-1]);return self.respond(200,{'challenge':view(data,c)}) if c else self.respond(404,{'error':'Challenge not found'})
  if route=='/api/organizations':return self.respond(200,{'organizations':data['organizations']})
  if route=='/api/dashboard':
   cases=data['challenges'];over=[c for c in cases if deadline_state(c)=='OVERDUE'];resolved=[c for c in cases if c['status']=='RESOLVED'];m={'total':len(cases),'assigned':sum(bool(c.get('assignedOrganizationId')) for c in cases),'active':sum(c['status'] in ('ACCEPTED','IN_PROGRESS','ASSIGNED') for c in cases),'overdue':len(over),'resolved':len(resolved),'complaints':sum(x['status'] not in ('CLOSED','RESOLVED') for x in data['complaints']),'organizations':len({c.get('assignedOrganizationId') for c in cases if c.get('assignedOrganizationId')}),'peopleBenefited':sum((c.get('resolution') or {}).get('peopleBenefited',0) for c in resolved),'certificates':len(data['certificates'])};recent=sorted([e for c in cases for e in c.get('events',[])],key=lambda e:e['createdAt'],reverse=True)[:10];return self.respond(200,{'metrics':m,'attention':[view(data,c) for c in cases if deadline_state(c) in ('OVERDUE','DUE_SOON') or c['status'] in ('ANALYZED','DISPUTED')],'recent':recent})
  if route=='/api/notifications':
   u=self.actor(data);return self.respond(200,{'notifications':[n for n in data['notifications'] if u and n['recipient'] in (u['email'],u['role'])]})
  if route.startswith('/api/verify/'):
   cert=next((x for x in data['certificates'] if x['id']==route.split('/')[-1]),None);return self.respond(200,{'certificate':cert}) if cert else self.respond(404,{'error':'Certificate not found'})
  return self.respond(404,{'error':'Not found'})
 def do_POST(self):
  route=unquote(urlparse(self.path).path);b=self.body()
  with LOCK:
   data=load()
   if route=='/api/auth/login':
    u=get_user(data,str(b.get('email','')).lower());return self.respond(200,{'user':{k:v for k,v in u.items() if k!='password'}}) if u and u['password']==digest(str(b.get('password',''))) else self.respond(401,{'error':'Incorrect email or password'})
   if route=='/api/auth/register':
    email=str(b.get('email','')).strip().lower();pw=str(b.get('password',''))
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email) or len(pw)<6:return self.respond(400,{'error':'Enter a valid email and password of at least 6 characters'})
    if get_user(data,email):return self.respond(409,{'error':'That email already has an account'})
    u={'email':email,'password':digest(pw),'role':'CITIZEN','name':str(b.get('name','')).strip() or 'Citizen'};data['users'].append(u);save(data);return self.respond(201,{'user':{k:v for k,v in u.items() if k!='password'}})
   u=self.actor(data)
   if not u:return self.respond(401,{'error':'Sign in required'})
   if route=='/api/challenges':
    if any(not str(b.get(x,'')).strip() for x in ('title','description','district','location')):return self.respond(400,{'error':'Complete title, description, district, and location'})
    ai=analysis(b['title'],b['description'],b.get('category',''));priority=str(b.get('priority') or ai['priority']).upper();cid=f"CH-{str(b['district'])[:3].upper()}-{len(data['challenges'])+1:03d}";c={'id':cid,'title':b['title'].strip(),'description':b['description'].strip(),'district':b['district'].strip(),'location':b['location'].strip(),'category':ai['domain'],'priority':priority,'affectedPeople':int(b.get('affectedPeople') or 0),'evidence':b.get('evidence',[])[:2],'status':'ANALYZED','createdAt':now(),'citizenEmail':u['email'],'assignedOrganizationId':None,'assignedAt':None,'deadline':None,'progress':0,'aiAnalysis':ai,'updates':[],'resolution':None,'verification':None,'events':[]};c['matches']=matches(c,data['organizations']);event(c,'CHALLENGE_CREATED','Citizen report created.',u['name']);event(c,'AI_ANALYZED',f"AI analysis completed: {ai['domain']} / {priority}.");event(c,'ORGANIZATION_MATCHED',f"{len(c['matches'])} suitable demo organizations matched.");data['challenges'].insert(0,c);note(data,u['email'],f'{cid} received and analyzed.',cid);note(data,'GOVERNMENT',f'New {priority} challenge {cid} requires review.',cid);save(data);return self.respond(201,{'challenge':view(data,c)})
   p=route.split('/');c=get_case(data,p[3]) if len(p)>4 and p[:3]==['','api','challenges'] else None;action=p[4] if len(p)>4 else ''
   if not c:return self.respond(404,{'error':'Challenge not found'})
   if action=='assign':
    if u['role']!='GOVERNMENT':return self.respond(403,{'error':'Government role required'})
    target=get_org(data,b.get('organizationId'))
    if not target:return self.respond(400,{'error':'Choose an organization'})
    c.update({'assignedOrganizationId':target['id'],'assignedAt':now(),'deadline':stamp(SLA[c['priority']]),'status':'ASSIGNED'});event(c,'ASSIGNED',f"Assigned to {target['name']}; deadline {date(c['deadline'])}.",u['name']);note(data,'ORGANIZATION',f"New challenge {c['id']} assigned to {target['name']}.",c['id']);note(data,c['citizenEmail'],f"{c['id']} assigned to {target['name']}.",c['id'])
   elif action=='accept':
    if u['role']!='ORGANIZATION' or u.get('organizationId')!=c.get('assignedOrganizationId'):return self.respond(403,{'error':'Assigned organization role required'})
    c['status']='ACCEPTED';event(c,'ACCEPTED','Organization accepted responsibility.',u['name']);note(data,c['citizenEmail'],f"{get_org(data,c['assignedOrganizationId'])['name']} accepted {c['id']}.",c['id'])
   elif action=='start':
    if u['role']!='ORGANIZATION':return self.respond(403,{'error':'Organization role required'})
    c['status']='IN_PROGRESS';event(c,'WORK_STARTED','Work started.',u['name']);note(data,c['citizenEmail'],f"Work started on {c['id']}.",c['id'])
   elif action=='progress':
    if u['role']!='ORGANIZATION':return self.respond(403,{'error':'Organization role required'})
    progress=max(0,min(100,int(b.get('progress',0))));text=str(b.get('text','')).strip()
    if not text:return self.respond(400,{'error':'Describe the progress update'})
    c['status']='IN_PROGRESS';c['progress']=progress;c['updates'].append({'id':f'UPD-{secrets.token_hex(3).upper()}','progress':progress,'text':text,'evidence':b.get('evidence',[])[:2],'createdAt':now(),'actor':u['name']});event(c,'PROGRESS_UPDATED',f'Progress updated to {progress}%: {text}',u['name']);note(data,c['citizenEmail'],f"New progress update on {c['id']}: {progress}%.",c['id'])
   elif action=='resolution':
    if u['role']!='ORGANIZATION':return self.respond(403,{'error':'Organization role required'})
    summary=str(b.get('summary','')).strip();done=str(b.get('whatWasDone','')).strip()
    if not summary or not done:return self.respond(400,{'error':'Complete the resolution summary and work completed'})
    c['resolution']={'summary':summary,'whatWasDone':done,'evidence':b.get('evidence',[])[:2],'peopleBenefited':int(b.get('peopleBenefited') or 0),'resolutionDate':b.get('resolutionDate') or now(),'submittedAt':now(),'organization':get_org(data,c['assignedOrganizationId'])['name']};c['status']='VERIFICATION';event(c,'RESOLUTION_SUBMITTED',f'Resolution submitted: {summary}',u['name']);event(c,'VERIFICATION_REQUESTED','Citizen verification requested.');note(data,c['citizenEmail'],f"Please verify the submitted resolution for {c['id']}.",c['id'])
   elif action=='verify':
    if u['role']!='CITIZEN' or u['email']!=c['citizenEmail']:return self.respond(403,{'error':'Reporting citizen role required'})
    confirmed=bool(b.get('confirmed'));comment=str(b.get('comment','')).strip();c['verification']={'status':'VERIFIED' if confirmed else 'REJECTED','comment':comment,'at':now()}
    if confirmed:
     c['status']='RESOLVED';event(c,'VERIFIED','Citizen confirmed the resolution.',u['name']);event(c,'RESOLVED','Challenge marked resolved after citizen verification.');cert={'id':f"CERT-JH-2026-{len(data['certificates'])+1:04d}",'challengeId':c['id'],'challengeTitle':c['title'],'location':f"{c['location']}, {c['district']}",'organization':c['resolution']['organization'],'resolution':c['resolution']['summary'],'peopleBenefited':c['resolution']['peopleBenefited'],'resolutionDate':c['resolution']['resolutionDate'],'issuedAt':now(),'verified':True};data['certificates'].append(cert);event(c,'CERTIFICATE_ISSUED',f"Verified certificate {cert['id']} issued.");note(data,'GOVERNMENT',f"{c['id']} was verified and resolved.",c['id'])
    else:
     c['status']='DISPUTED';event(c,'DISPUTED','Citizen rejected the submitted resolution.',u['name']);complaint={'id':f"CMP-2026-{len(data['complaints'])+1:04d}",'challengeId':c['id'],'type':'Incorrect resolution','description':comment or 'Citizen reports the problem still exists.','evidence':[],'createdAt':now(),'status':'ESCALATED'};data['complaints'].append(complaint);event(c,'COMPLAINT_RAISED',f"Complaint {complaint['id']} automatically created.");note(data,'GOVERNMENT',f"Disputed resolution on {c['id']} requires attention.",c['id'])
   elif action=='complaint':
    if u['role']!='CITIZEN' or u['email']!=c['citizenEmail']:return self.respond(403,{'error':'Reporting citizen role required'})
    desc=str(b.get('description','')).strip()
    if not desc:return self.respond(400,{'error':'Describe the complaint'})
    complaint={'id':f"CMP-2026-{len(data['complaints'])+1:04d}",'challengeId':c['id'],'type':b.get('type','Other'),'description':desc,'evidence':b.get('evidence',[])[:2],'createdAt':now(),'status':'OPEN'};data['complaints'].append(complaint);event(c,'COMPLAINT_RAISED',f"Complaint {complaint['id']} raised: {complaint['type']}.",u['name']);note(data,'GOVERNMENT',f"New complaint {complaint['id']} for {c['id']}.",c['id'])
   else:return self.respond(404,{'error':'Unknown action'})
   save(data);return self.respond(200,{'challenge':view(data,c)})
 def log_message(self,*args):pass
if __name__=='__main__':
 print('SAMADHAN running at http://127.0.0.1:8000 — demo password: Samadhan123!');ThreadingHTTPServer(('0.0.0.0',8000),App).serve_forever()
