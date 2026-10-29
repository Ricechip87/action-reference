const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const todayKorea=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul'}).format(new Date());
const validDate=d=>/^\d{4}-\d{2}-\d{2}$/.test(d||'');
function hits(title,alias){
 const words=String(alias).normalize('NFKC').match(/[\p{L}\p{N}]+/gu);
 if(!words?.length)return [];
 const pattern=words.map(escape).join('[^\\p{L}\\p{N}]*');
 return [...title.matchAll(new RegExp('(?<![\\p{L}\\p{N}])'+pattern+'(?![\\p{L}\\p{N}])','giu'))].map(m=>({start:m.index,end:m.index+m[0].length}));
}
function identifiedCharacters(video,characters){
 const title=String(video.title||'').normalize('NFKC').replace(/[丨｜]/g,' ');
 const found=characters.filter(c=>c.gameId===video.gameId&&!(c.kind==='family'&&video.sourceKind==='creator')).flatMap(c=>[...new Set([c.name,...(c.aliases||[])])].flatMap(a=>hits(title,a).map(span=>({character:c,...span}))));
 // A shorter name inside a full variant name must never claim that variant.
 const specific=found.filter(h=>!found.some(other=>other.character.id!==h.character.id&&other.start<=h.start&&other.end>=h.end&&(other.start<h.start||other.end>h.end)));
 const unique=new Map(specific.map(h=>[h.character.id,h.character]));
 return [...unique.values()];
}
export function identifyCharacter(video,characters){
 const found=identifiedCharacters(video,characters);
 return found.length===1?found[0]:null;
}
export function enrichVideos(videos,characters,{asOf=todayKorea()}={}){
 const output=[],excluded=[];
 for(const video of videos){
  const found=identifiedCharacters(video,characters),c=found.length===1?found[0]:null,release=c?.releaseDate;
  if(video.sourceKind==='creator'&&found.length>1){excluded.push({...video,exclusionReason:'여러 캐릭터 합본'});continue;}
  if(video.sourceKind==='creator'&&validDate(release)&&release>asOf){excluded.push({...video,exclusionReason:'미출시 캐릭터'});continue;}
  output.push({...video,characterId:c?.id||null,characterName:c?.name||null,characterKind:c?.kind||'character',characterReleaseDate:validDate(release)?release:null,characterReleaseOrder:c?.releaseOrder??null,characterReleaseBasis:c?.releaseBasis||null});
 }
 return {videos:output,excluded};
}
export function compareRelease(a,b,{descending=false}={}){
 const knownA=validDate(a.characterReleaseDate),knownB=validDate(b.characterReleaseDate);
 if(knownA!==knownB)return knownA?-1:1;
 const date=knownA?a.characterReleaseDate.localeCompare(b.characterReleaseDate):0;
 if(date)return descending?-date:date;
 const name=String(a.characterName||a.title).localeCompare(String(b.characterName||b.title),'ko');
 if(name)return name;
 const korean=v=>v.language==='ko'||/[가-힣]/.test(v.title||'');
 return Number(korean(b))-Number(korean(a))||String(a.title).localeCompare(String(b.title),'ko')||String(a.id).localeCompare(String(b.id));
}
