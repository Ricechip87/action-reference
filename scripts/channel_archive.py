"""Initial channel-list metadata import. Never invents an exact upload timestamp.

Watch pages can be unavailable while public channel listings remain readable. The
listing verifies video and channel IDs. Relative upload labels are stored as a
conservative interval and used only to reject pre-launch creator footage.
"""
import argparse,calendar,datetime as dt,json,re,time
from pathlib import Path
from urllib.parse import quote
from rss import fetch,relevant,resolve_channel_id,video_type

def text(value):return value.get('simpleText') or ''.join(r.get('text','') for r in value.get('runs',[]))
def walk(value):
    if isinstance(value,dict):
        if 'videoRenderer' in value:yield value['videoRenderer']
        for item in value.values():yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)

def publication_window(label,today):
    match=re.search(r'(\d+)\s*(년|개월|달|주|일|시간|분|초|years?|months?|weeks?|days?|hours?|minutes?|seconds?)\s*(?:전|ago)',label,re.I)
    if not match:return None
    n=int(match[1]);unit=match[2].lower()
    def months(offset):
        index=today.year*12+today.month-1-offset;y,m=divmod(index,12);m+=1
        return today.replace(year=y,month=m,day=min(today.day,calendar.monthrange(y,m)[1]))
    if unit=='년' or unit.startswith('year'):early,late=months(12*(n+1)),months(12*n)
    elif unit in ['개월','달'] or unit.startswith('month'):early,late=months(n+1),months(n)
    elif unit=='주' or unit.startswith('week'):early,late=today-dt.timedelta(days=(n+1)*7),today-dt.timedelta(days=n*7)
    elif unit=='일' or unit.startswith('day'):early,late=today-dt.timedelta(days=n+1),today-dt.timedelta(days=n)
    else:early,late=today-dt.timedelta(days=1),today
    return {'earliest':early.isoformat(),'latest':late.isoformat(),'label':label,'capturedAt':today.isoformat()}

def collect_listing(game,channel,query,today,fetcher=fetch):
    url='https://www.youtube.com/channel/'+channel+'/search?query='+quote(query)
    page=fetcher(url);marker=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',page)
    if not marker:raise ValueError('Public channel list unavailable')
    data=json.JSONDecoder().raw_decode(page[marker.end():])[0]
    owner=data.get('metadata',{}).get('channelMetadataRenderer',{})
    if owner.get('externalId')!=channel:raise ValueError('Channel identity mismatch')
    output=[]
    for item in walk(data):
        video_id=item.get('videoId','')
        owners=[r.get('navigationEndpoint',{}).get('browseEndpoint',{}).get('browseId') for r in item.get('ownerText',{}).get('runs',[])]
        if channel not in owners or not re.fullmatch(r'[\w-]{11}',video_id):continue
        video={'id':video_id,'title':text(item.get('title',{})),'description':text(item.get('descriptionSnippet',{})),'gameId':game['id']}
        if not relevant(video,game):continue
        window=publication_window(text(item.get('publishedTimeText',{})),today)
        if game.get('sourceKind')=='creator' and (not window or window['earliest']<game['releaseDate']):continue
        length=text(item.get('lengthText',{}));parts=length.split(':');seconds=sum(int(p)*60**i for i,p in enumerate(reversed(parts))) if all(p.isdigit() for p in parts) else 0
        video.update(publishedAt='',publicationWindow=window,channelId=channel,channelTitle=owner.get('title',''),language='ko' if re.search('[가-힣]',video['title']) else 'en',sourceChannel=game['sourceChannel'],sourceKind=game.get('sourceKind','official'),gameVerified=True,type='캐릭터 무브셋' if game.get('sourceKind')=='creator' else video_type(video['title']),duration='PT'+str(seconds)+'S',verification='public-channel-list',verificationSource=url)
        output.append(video)
    return output

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--game',required=True);parser.add_argument('--creator',type=int);parser.add_argument('--query',action='append');args=parser.parse_args()
    game=next(g for g in json.loads(Path('config.json').read_text(encoding='utf-8'))['games'] if g['id']==args.game)
    source=game['channels'][0]
    if args.creator is not None:
        creator=game['creators'][args.creator];game={**game,**creator,'channelSpecific':False,'sourceKind':'creator'};source=creator['channel']
    game={**game,'sourceChannel':source};channel=resolve_channel_id(source)
    path=Path('data/archive.json');archive=json.loads(path.read_text(encoding='utf-8'));known={v['id']:v for v in archive['videos']};added=0
    today=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    for query in args.query or game['includeKeywords']:
        videos=collect_listing(game,channel,query,today)
        for video in videos:
            if video['id'] not in known:known[video['id']]=video;added+=1
        print(query,len(videos),'verified listing entries',flush=True);time.sleep(1)
    archive['videos']=list(known.values());path.write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Added',added,'without fabricating upload dates')
if __name__=='__main__':main()
