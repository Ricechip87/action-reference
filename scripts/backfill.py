"""One-time metadata-only archive import. Requires yt-dlp; never downloads media."""
import argparse
import threading
import urllib.error
import concurrent.futures
import datetime as dt
import json
import re
from pathlib import Path
import yt_dlp
from rss import fetch, video_type, resolve_channel_id, relevant



def metadata(entry,game,channel,handle):
    page=fetch('https://www.youtube.com/watch?v='+entry['id'])
    marker=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',page)
    if not marker:raise ValueError('Missing public video metadata: '+entry['id'])
    player,_=json.JSONDecoder().raw_decode(page[marker.end():])
    details=player.get('videoDetails',{})
    if details.get('channelId')!=channel:raise ValueError('Channel identity mismatch: '+entry['id'])
    title=details.get('title','')
    if not relevant({'title':title,'description':details.get('shortDescription','')},game):return None
    info=player.get('microformat',{}).get('playerMicroformatRenderer',{})
    published=info.get('publishDate') or info.get('uploadDate')
    if not published:raise ValueError('Missing publication date: '+entry['id'])
    return {'id':entry['id'],'title':title,'publishedAt':published,'channelTitle':details.get('author','명조:워더링 웨이브'),'channelId':channel,'gameId':game['id'],'language':'ko' if re.search(r'[가-힣]',title) else 'en','type':'캐릭터 무브셋' if game.get('sourceKind')=='creator' else video_type(title),'sourceChannel':handle,'sourceKind':game.get('sourceKind','official'),'gameVerified':True,'description':details.get('shortDescription','')[:4000] if game.get('sourceKind')=='creator' else '', 'duration':'PT'+str(details.get('lengthSeconds',0))+'S'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--creator",type=int)
    parser.add_argument("--game",default="wuthering-waves")
    parser.add_argument("--candidates-file",action="append",default=[])
    args=parser.parse_args()
    config=json.loads(Path('config.json').read_text(encoding='utf-8'))
    game=next(g for g in config['games'] if g['id']==args.game)
    handle=game['channels'][0]
    if args.creator is not None:
        creator=game['creators'][args.creator]
        game={**game,**creator,'channelSpecific':False,'sourceKind':'creator'}
        handle=creator['channel']
    channel=resolve_channel_id(handle)
    aliases={'wuthering-waves':['combat motion'],'neverness-to-everness':['character showcase'],'zenless-zone-zero':['character demo','character gameplay']}
    terms=[*game['includeKeywords'],*aliases.get(args.game,[])]
    def candidate(entry):
        return entry and entry.get('channel_id')==channel and (not game.get('titleGameRequired') or any(k.casefold() in (entry.get('title') or '').casefold() for k in game['keywords'])) and not any(k.casefold() in (entry.get('title') or '').casefold() for k in game.get('excludeKeywords',[])) and any(t.casefold() in (entry.get('title') or '').casefold() for t in terms)
    candidates={}
    for filename in args.candidates_file:
        captured=json.loads(Path(filename).read_text(encoding="utf-8-sig"))
        for entry in captured.get("entries",[]):
            if candidate(entry):candidates[entry["id"]]=entry
    with yt_dlp.YoutubeDL({'extract_flat':True,'skip_download':True,'quiet':True}) as ydl:
        from urllib.parse import quote
        query=game['includeKeywords'][0]
        channel_url='https://www.youtube.com/'+('channel/' if handle.startswith('UC') else '')+handle
        sources=[channel_url+'/videos',channel_url+'/search?query='+quote(query),'ytsearch100:'+game['name']+' '+query]
        for source in sources:
            result=ydl.extract_info(source,download=False)
            for entry in result.get('entries',[]):
                if candidate(entry):candidates[entry['id']]=entry
    # A private/unavailable item must not discard the verified entries of a whole channel.
    stopped=threading.Event();failures=[]
    def verify(entry):
        if stopped.is_set():return None
        try:return metadata(entry,game,channel,handle)
        except Exception as error:
            failures.append({'id':entry['id'],'sourceChannel':handle,'gameId':game['id'],'reason':str(error)[:180]})
            if isinstance(error,urllib.error.HTTPError) and error.code==429:stopped.set()
            return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:videos=[v for v in pool.map(verify,candidates.values()) if v]
    if not videos and not candidates:raise ValueError('No matching candidates found')
    errors_path=Path('data/initialization-errors.json')
    errors=json.loads(errors_path.read_text(encoding='utf-8')) if errors_path.exists() else {'entries':[]}
    errors['entries']=[e for e in errors['entries'] if e.get('sourceChannel')!=handle or e.get('gameId')!=game['id']]+failures
    errors_path.write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    videos.sort(key=lambda v:v['publishedAt'],reverse=True)
    previous=json.loads(Path('data/archive.json').read_text(encoding='utf-8')) if Path('data/archive.json').exists() else {}
    combined={v['id']:v for v in previous.get('videos',[])}
    combined.update({v['id']:v for v in videos})
    result={'initializedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'videos':list(combined.values())}
    Path('data/archive.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Verified and archived:',len(videos),'Unverified:',len(failures),'Rate limited:',stopped.is_set())

if __name__=='__main__':main()
