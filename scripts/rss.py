"""Public channel Atom feeds; no API key or third-party packages."""
import concurrent.futures
import datetime as dt
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL=re.compile(r'UC[\w-]{22}')
NS={'a':'http://www.w3.org/2005/Atom','yt':'http://www.youtube.com/xml/schemas/2015','m':'http://search.yahoo.com/mrss/'}

def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'FRAME-Reference/1.0','Accept-Language':'ko,en;q=0.7'})
    with urllib.request.urlopen(request,timeout=35) as response:
        body=response.read(8_000_001)
        if len(body)>8_000_000:raise ValueError('Response too large')
        return body.decode('utf-8')

def resolve_channel_id(channel,fetcher=fetch):
    if CHANNEL.fullmatch(channel):return channel
    if not re.fullmatch(r'@[\w.-]{3,30}',channel):raise ValueError('Invalid channel handle')
    page=fetcher('https://www.youtube.com/'+channel)
    patterns=[r'<link[^>]+rel="canonical"[^>]+href="https://www.youtube.com/channel/(UC[\w-]{22})"',r'<meta[^>]+property="og:url"[^>]+content="https://www.youtube.com/channel/(UC[\w-]{22})"',r'"channelMetadataRenderer"\s*:\s*\{[^}]*?"externalId"\s*:\s*"(UC[\w-]{22})"']
    for pattern in patterns:
        match=re.search(pattern,page)
        if match:return match.group(1)
    raise ValueError('Channel ID not found for '+channel)

def parse_feed(xml,channel):
    if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():raise ValueError('Unsupported XML declaration')
    root=ET.fromstring(xml)
    if root.tag!='{'+NS['a']+'}feed':raise ValueError('Not an Atom feed')
    title=root.findtext('a:title','',NS);videos=[]
    for entry in root.findall('a:entry',NS):
        video_id=entry.findtext('yt:videoId','',NS)
        if not re.fullmatch(r'[\w-]{11}',video_id) or entry.findtext('yt:channelId','',NS)!=channel:continue
        videos.append({'id':video_id,'title':entry.findtext('a:title','',NS),'description':entry.findtext('m:group/m:description','',NS),'publishedAt':entry.findtext('a:published','',NS),'channelTitle':title,'channelId':channel})
    return videos

def relevant(video,game):
    hay=(video['title']+' '+video.get('description','')).casefold()
    if any(term.casefold() in video['title'].casefold() for term in game.get('excludeKeywords',[])):return False
    if game.get('sourceKind')=='creator' and re.search(r'closed beta|\bcbt\d?\b|beta test|leaked footage|유출|베타 테스트',hay,re.I):return False
    if game.get('sourceKind')=='creator' and game.get('releaseDate') and video.get('publishedAt'):
        try:
            published=dt.datetime.fromisoformat(video['publishedAt'].replace('Z','+00:00')).astimezone(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
            if published<game['releaseDate']:return False
        except ValueError:return False
    if not game.get('channelSpecific',False) and not (video.get('gameVerified') and video.get('gameId')==game.get('id')) and not any(k.strip() and k.casefold() in hay for k in game['keywords']):return False
    terms=game.get('includeKeywords',[])
    return not terms or any(k.strip() and k.casefold() in video['title'].casefold() for k in terms)

def video_type(title):
    if '데인 여담' in title:return '데인 여담'
    if '오퍼레이터 전투 시연' in title:return '오퍼레이터 전투 시연'
    if any(t in title for t in ['스킬 전시','스킬 소개']):return '캐릭터 스킬 시연'
    if '전투 모션' in title:return '전투 모션'
    if '캐릭터 쇼케이스' in title:return '캐릭터 쇼케이스'
    if '캐릭터 플레이' in title:return '캐릭터 플레이'
    if re.search(r'전투|combat|gameplay|플레이',title,re.I):return '플레이 영상'
    if re.search(r'캐릭터|character|공명자',title,re.I):return '캐릭터 소개'
    if re.search(r'트레일러|trailer|\bpv\b|프로모션',title,re.I):return 'PV / 트레일러'
    return '기타'

def merge_previous(current,previous,jobs):
    output=list(current)
    active={(g['id'],c):g for g,c in jobs}
    seen={v['id'] for v in output}
    for old in previous:
        game=active.get((old.get('gameId'),old.get('sourceChannel')))
        if game and relevant(old,game) and old['id'] not in seen:
            output.append(old);seen.add(old['id'])
    return output

def collection_jobs(config):
    jobs=[]
    for game in config['games']:
        if not game.get('enabled',True):continue
        jobs.extend(({**game,'sourceKind':'official'},c) for c in game['channels'])
        for creator in game.get('creators',[]):
            if creator.get('enabled',True):jobs.append(({**game,**creator,'channelSpecific':False,'sourceKind':'creator'},creator['channel']))
    return jobs

def collect():
    config=json.loads(Path('config.json').read_text(encoding='utf-8'));prior={}
    try:prior=json.loads(fetch('https://ricechip87.github.io/action-reference/data/videos.json'))
    except Exception as error:
        raise RuntimeError('Previous publication unavailable; preserve existing history by stopping') from error
    jobs=collection_jobs(config)
    output=[];statuses=[]
    def run(job):
        game,source=job
        try:
            channel=resolve_channel_id(source)
            entries=parse_feed(fetch('https://www.youtube.com/feeds/videos.xml?channel_id='+channel),channel);selected=[]
            for v in entries:
                if not relevant(v,game):continue
                v.update(gameId=game['id'],language='ko' if re.search(r'_KO$|_KR_',source,re.I) else '',type='캐릭터 무브셋' if game.get('sourceKind')=='creator' else video_type(v['title']),sourceChannel=source,sourceKind=game.get('sourceKind','official'),gameVerified=True)
                v.pop('description',None);selected.append(v)
            return selected,{'gameId':game['id'],'channel':source,'ok':True,'feedCount':len(entries),'matchedCount':len(selected)}
        except Exception as error:
            return [],{'gameId':game['id'],'channel':source,'ok':False,'error':str(error)[:200]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for entries,status in pool.map(run,jobs):output.extend(entries);statuses.append(status)
    if jobs and not any(s['ok'] for s in statuses):raise RuntimeError('All channel feeds failed: '+json.dumps(statuses,ensure_ascii=False))
    archive=json.loads(Path('data/archive.json').read_text(encoding='utf-8')) if Path('data/archive.json').exists() else {}
    output=merge_previous(output,[*prior.get('videos',[]),*archive.get('videos',[])],jobs)
    result={'updatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'source':'rss','channels':statuses,'videos':output}
    Path('data/rss-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'channels':statuses,'videos':len(output)},ensure_ascii=False))

if __name__=='__main__':collect()
