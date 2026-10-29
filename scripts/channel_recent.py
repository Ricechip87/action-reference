"""Read the selected public videos tab only; no continuation or watch requests."""
import calendar,datetime as dt,json,re

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

def parse_recent(page,channel,today,limit=15):
    marker=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',page)
    if not marker:raise ValueError('Public videos tab unavailable')
    data=json.JSONDecoder().raw_decode(page[marker.end():])[0]
    owner=data.get('metadata',{}).get('channelMetadataRenderer',{})
    if owner.get('externalId')!=channel:raise ValueError('Channel identity mismatch')
    tabs=data.get('contents',{}).get('twoColumnBrowseResultsRenderer',{}).get('tabs',[])
    selected=[t['tabRenderer'] for t in tabs if t.get('tabRenderer',{}).get('selected')]
    if len(selected)!=1 or 'richGridRenderer' not in selected[0].get('content',{}):raise ValueError('Public videos grid unavailable')
    videos=[]
    def plain(value):return value.get('simpleText') or ''.join(r.get('text','') for r in value.get('runs',[]))
    for item in selected[0]['content']['richGridRenderer'].get('contents',[]):
        content=item.get('richItemRenderer',{}).get('content',{})
        if 'lockupViewModel' in content:
            v=content['lockupViewModel']
            if v.get('contentType')!='LOCKUP_CONTENT_TYPE_VIDEO':continue
            id=v.get('contentId','');meta=v.get('metadata',{}).get('lockupMetadataViewModel',{})
            title=meta.get('title',{}).get('content','')
            parts=[p.get('text',{}).get('content','') for row in meta.get('metadata',{}).get('contentMetadataViewModel',{}).get('metadataRows',[]) for p in row.get('metadataParts',[])]
            window=next((w for p in parts if (w:=publication_window(p,today))),None)
        elif 'videoRenderer' in content:
            v=content['videoRenderer'];id=v.get('videoId','');title=plain(v.get('title',{}))
            owners=[r.get('navigationEndpoint',{}).get('browseEndpoint',{}).get('browseId') for r in v.get('ownerText',{}).get('runs',[])]
            if owners and channel not in owners:continue
            window=publication_window(plain(v.get('publishedTimeText',{})),today)
        else:continue
        if not re.fullmatch(r'[\w-]{11}',id) or not title or not window:continue
        videos.append({'id':id,'title':title,'description':'','publishedAt':'','publicationWindow':window,'channelId':channel,'channelTitle':owner.get('title',''),'verification':'public-channel-videos','verificationSource':'https://www.youtube.com/channel/'+channel+'/videos'})
        if len(videos)>=limit:break
    if not videos:raise ValueError('No dated public videos found')
    return videos
