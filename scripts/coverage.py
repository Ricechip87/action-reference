import sys,json,re,datetime as dt
from pathlib import Path
ALIASES={
'wuthering-waves':{'쇄명':['Suoming'],'여우의 별자리':['Hsin'],'양양 · 현령':['Yangyang Xuanling'],'루시':['Lucy'],'레베카':['Rebecca'],'데니아':['Denia'],'히유키':['Hiyuki'],'시그리카':['Sigrika'],'루크 · 헤르센':['Luke Herssen'],'에이메스':['Aemeath'],'모니에':['Mornye'],'린네':['Lynae'],'치사':['Chisa'],'갈브레나':['Galbrena'],'유노':['Iuno'],'아우구스타':['Augusta'],'플로로':['Phrolova'],'루파':['Lupa'],'카르티시아':['Cartethyia'],'샤콘':['Ciaccona'],'젠니':['Zani'],'칸타렐라':['Cantarella'],'브렌트':['Brant'],'로코코':['Roccia'],'카를로타':['Carlotta'],'카멜리아':['Camellya']},
'neverness-to-everness':{'아카네 린':['Akane Rin'],'레이븐':['Blackbird','Raven'],'링코':['Linko'],'잔홍':['Zankou'],'일로이':['Iroi'],'신쿠':['Shinku'],'카오스':['Chaos'],'라크리모사':['Lacrimosa'],'호토리':['Hotori'],'나나리':['Nanally']},
'zenless-zone-zero':{'피닉스':['Pyrois','Phoenix'],'록시':['Roxy'],'클라렛':['Claret'],'시그리드':['Sigrid'],'레미엘':['Remiel'],'노르마':['Norma'],'벨리나':['Velina'],'스타라이트·빌리':['Starlight Billy'],'프로미아':['Promeia'],'시시아':['Cissia'],'남궁우':['Nangong Yu'],'아리아':['Aria'],'수나':['Sunna'],'자오':['Zhao'],'엽빛나':['Ye Shunguang'],'반악':['Banyue'],'다이아린':['Dialyn'],'이드하리':['Yidhari'],'루시아':['Lucia'],'오피 & 「도깨비불」':['Orphie','Magus'],'「시드 」':['Seed'],'앨리스':['Alice'],'우키나미 유즈하':['Yuzuha'],'귤복복':['Ju Fufu'],'의현':['Yixuan'],'휴고':['Hugo'],'비비안':['Vivian'],'「트리거」':['Trigger'],'0호·엔비':['Silver Soldier Anby'],'이블린':['Evelyn'],'아스트라 야오':['Astra Yao'],'호시미 미야비':['Miyabi'],'아사바 하루마사':['Harumasa'],'라이터':['Lighter'],'츠키시로 야나기':['Yanagi'],'버니스':['Burnice'],'카이사르':['Caesar'],'제인':['Jane'],'청의':['Qingyi'],'주연':['Zhu Yuan'],'엘렌':['Ellen'],'11호':['Soldier 11'],'리나':['Rina'],'그레이스':['Grace'],'리카온':['Lycaon'],'네코마타':['Nekomata'],'엔비':['Anby'],'니콜':['Nicole'],'빌리':['Billy']}}
def person(v):
 t=v['title']
 if v['gameId']=='wuthering-waves':return t.rsplit('|',1)[-1].strip()
 if v['gameId']=='zenless-zone-zero':return t.split('캐릭터 플레이')[0].strip()
 return re.sub(r'^이환\s*[|丨]?\s*','',t).replace('캐릭터 쇼케이스','').strip(' |丨')
def matches(title,name,aliases):
 if name in title:return True
 for a in aliases:
  if re.search(r'(?<![a-z])'+re.escape(a)+r'(?![a-z])',title,re.I):
   if name=='엔비' and re.search('silver soldier|0호',title,re.I):continue
   if name=='빌리' and re.search('starlight|스타라이트',title,re.I):continue
   return True
 return False
def build(videos):
 games=[]
 config=json.loads(Path('config.json').read_text(encoding='utf-8'))
 for game in config['games']:
  official=[v for v in videos if v['gameId']==game['id'] and v.get('sourceKind','official')=='official']
  creators=[v for v in videos if v['gameId']==game['id'] and v.get('sourceKind')=='creator']
  entries=[]
  for v in official:
   name=person(v);aliases=ALIASES.get(game['id'],{}).get(name,[])
   found=[c['id'] for c in creators if matches(c['title'],name,aliases)]
   entries.append({'name':name,'aliases':aliases,'officialVideoId':v['id'],'videoIds':found,'covered':bool(found)})
  games.append({'gameId':game['id'],'name':game['name'],'total':len(entries),'covered':sum(e['covered'] for e in entries),'characters':entries})
 return {'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'공식 시리즈의 캐릭터명과 개별 영상 제목 대조. 모션 전체 포함 여부는 영상별 확인 필요.','games':games}
if __name__=='__main__':
 source=json.loads(Path('data/videos.json' if '--live' in sys.argv else 'data/archive.json').read_text(encoding='utf-8'))
 result=build(source['videos'])
 Path('data/coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for game in result['games']:print(game['gameId'],game['covered'],'/',game['total'])
