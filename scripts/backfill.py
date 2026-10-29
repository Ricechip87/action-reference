"""One-time metadata-only archive import. Requires yt-dlp; never downloads media."""
import argparse
import concurrent.futures
import datetime as dt
import json
import re
from pathlib import Path
import yt_dlp
from rss import fetch, video_type, resolve_channel_id



def metadata(entry,game,channel,handle):
    page=fetch('https://www.youtube.com/watch?v='+entry['id'])
    marker=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',page)
    if not marker:raise ValueError('Missing public video metadata: '+entry['id'])
    player,_=json.JSONDecoder().raw_decode(page[marker.end():])
    details=player.get('videoDetails',{})
    if details.get('channelId')!=channel:raise ValueError('Channel identity mismatch: '+entry['id'])
    title=details.get('title','')
    if not any(term.casefold() in title.casefold() for term in game['includeKeywords']):return None
    info=player.get('microformat',{}).get('playerMicroformatRenderer',{})
    published=info.get('publishDate') or info.get('uploadDate')
    if not published:raise ValueError('Missing publication date: '+entry['id'])
    return {'id':entry['id'],'title':title,'publishedAt':published,'channelTitle':details.get('author','명조:워더링 웨이브'),'channelId':channel,'gameId':game['id'],'language':'ko','type':video_type(title),'sourceChannel':handle,'duration':'PT'+str(details.get('lengthSeconds',0))+'S'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--game",default="wuthering-waves")
    parser.add_argument("--candidates-file",action="append",default=[])
    args=parser.parse_args()
    config=json.loads(Path('config.json').read_text(encoding='utf-8'))
    game=next(g for g in config['games'] if g['id']==args.game)
    handle=game['channels'][0]
    channel=resolve_channel_id(handle)
    aliases={'wuthering-waves':['combat motion'],'neverness-to-everness':['character showcase'],'zenless-zone-zero':['character demo','character gameplay']}
    terms=[*game['includeKeywords'],*aliases.get(args.game,[])]
    def candidate(entry):
        return entry and entry.get('channel_id')==channel and any(t.casefold() in (entry.get('title') or '').casefold() for t in terms)
    candidates={}
    for filename in args.candidates_file:
        captured=json.loads(Path(filename).read_text(encoding="utf-8-sig"))
        for entry in captured.get("entries",[]):
            if candidate(entry):candidates[entry["id"]]=entry
    with yt_dlp.YoutubeDL({'extract_flat':True,'skip_download':True,'quiet':True}) as ydl:
        from urllib.parse import quote
        query=game['includeKeywords'][0]
        sources=['https://www.youtube.com/'+handle+'/videos','https://www.youtube.com/'+handle+'/search?query='+quote(query),'ytsearch100:'+game['name']+' '+query]
        for source in sources:
            result=ydl.extract_info(source,download=False)
            for entry in result.get('entries',[]):
                if candidate(entry):candidates[entry['id']]=entry
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:videos=[v for v in pool.map(lambda entry:metadata(entry,game,channel,handle),candidates.values()) if v]
    if not videos:raise ValueError('No archive entries found')
    videos.sort(key=lambda v:v['publishedAt'],reverse=True)
    previous=json.loads(Path('data/archive.json').read_text(encoding='utf-8')) if Path('data/archive.json').exists() else {}
    combined={v['id']:v for v in previous.get('videos',[])}
    combined.update({v['id']:v for v in videos})
    result={'initializedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'videos':list(combined.values())}
    Path('data/archive.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Verified and archived:',len(videos))

if __name__=='__main__':main()
