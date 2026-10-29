"""One-time metadata-only archive import. Requires yt-dlp; never downloads media."""
import argparse
import concurrent.futures
import datetime as dt
import json
import re
from pathlib import Path
import yt_dlp
from rss import fetch, video_type

CHANNEL='UCKuq0c-RXYaulECSuu5hFug'
HANDLE='@WW_KR_Official'
GAME='wuthering-waves'

def metadata(entry):
    page=fetch('https://www.youtube.com/watch?v='+entry['id'])
    marker=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',page)
    if not marker:raise ValueError('Missing public video metadata: '+entry['id'])
    player,_=json.JSONDecoder().raw_decode(page[marker.end():])
    details=player.get('videoDetails',{})
    if details.get('channelId')!=CHANNEL:raise ValueError('Channel identity mismatch: '+entry['id'])
    title=details.get('title','')
    if '전투 모션' not in title:return None
    info=player.get('microformat',{}).get('playerMicroformatRenderer',{})
    published=info.get('publishDate') or info.get('uploadDate')
    if not published:raise ValueError('Missing publication date: '+entry['id'])
    return {'id':entry['id'],'title':title,'publishedAt':published,'channelTitle':details.get('author','명조:워더링 웨이브'),'channelId':CHANNEL,'gameId':GAME,'language':'ko','type':video_type(title),'sourceChannel':HANDLE,'duration':'PT'+str(details.get('lengthSeconds',0))+'S'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidates-file",action="append",default=[])
    args=parser.parse_args()
    candidates={}
    for filename in args.candidates_file:
        captured=json.loads(Path(filename).read_text(encoding="utf-8-sig"))
        for entry in captured.get("entries",[]):
            if entry and entry.get("channel_id")==CHANNEL and re.search(r"전투 모션|combat motions?",entry.get("title") or "",re.I):candidates[entry["id"]]=entry
    with yt_dlp.YoutubeDL({'extract_flat':True,'skip_download':True,'quiet':True}) as ydl:
        sources=['https://www.youtube.com/'+HANDLE+'/videos','https://www.youtube.com/'+HANDLE+'/search?query=%EC%A0%84%ED%88%AC%20%EB%AA%A8%EC%85%98','ytsearch100:공명자 전투 모션']
        for source in sources:
            result=ydl.extract_info(source,download=False)
            for entry in result.get('entries',[]):
                if entry and entry.get('channel_id')==CHANNEL and re.search(r'전투 모션|combat motions?',entry.get('title') or '',re.I):candidates[entry['id']]=entry
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:videos=[v for v in pool.map(metadata,candidates.values()) if v]
    if not videos:raise ValueError('No archive entries found')
    videos.sort(key=lambda v:v['publishedAt'],reverse=True)
    result={'initializedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'channelId':CHANNEL,'sourceChannel':HANDLE,'candidateCount':len(candidates),'videos':videos}
    Path('data/archive.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Verified and archived:',len(videos))

if __name__=='__main__':main()
