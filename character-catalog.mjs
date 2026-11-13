const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const todayKorea=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul'}).format(new Date());
const validDate=d=>/^\d{4}-\d{2}-\d{2}$/.test(d||'');
function publicationBounds(video){
 const published=video.publishedAt;
 const day=validDate(published)?published:typeof published==='string'&&Number.isFinite(Date.parse(published))
  ?new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul'}).format(new Date(published)):null;
 if(day)return {earliest:day,latest:day};
 return video.publicationWindow||{};
}
function hits(title,alias){
 const words=String(alias).normalize('NFKC').match(/[\p{L}\p{N}]+/gu);
 if(!words?.length)return [];
 const pattern=words.map(escape).join('[^\\p{L}\\p{N}]*');
 const japanese=/^[\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}ー]+$/u.test(words.join(''));
 const ending=japanese?'(?=$|[^\\p{L}\\p{N}]|(?:の)?(?:戦闘|モーション|基本コンボ|通常攻撃))':'(?![\\p{L}\\p{N}])';
 return [...title.matchAll(new RegExp('(?<![\\p{L}\\p{N}])'+pattern+ending,'giu'))].map(m=>({start:m.index,end:m.index+m[0].length}));
}
function identifiedCharacters(video,characters){
 const title=[video.title,...(Array.isArray(video.localizedTitles)?video.localizedTitles:[])].map(t=>String(t||'')).join(' | ').normalize('NFKC').replace(/[丨｜]/g,' ');
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
  const {earliest,latest}=publicationBounds(video);
  // A reviewed regional release (such as the PGR China server) can predate the global sort date.
  const footageRelease=video.reviewedAfterCharacterRelease&&validDate(video.reviewedCharacterReleaseDate)
   ?video.reviewedCharacterReleaseDate:release;
  if(video.sourceKind==='creator'&&found.length>1){excluded.push({...video,exclusionReason:'여러 캐릭터 합본'});continue;}
  if(video.sourceKind==='creator'&&validDate(release)&&release>asOf){excluded.push({...video,exclusionReason:'미출시 캐릭터'});continue;}
  const publishedBeforeRelease=validDate(footageRelease)&&validDate(latest)&&latest<footageRelease;
  if(video.sourceKind==='creator'&&publishedBeforeRelease){excluded.push({...video,exclusionReason:'정식 출시 전 게시'});continue;}
  if(video.sourceKind==='creator'&&video.requiresReleaseWindow&&(!validDate(footageRelease)||!validDate(earliest)||earliest<footageRelease)){excluded.push({...video,exclusionReason:'출시 후 게시 여부 미확인'});continue;}
  const officialPreview=video.sourceKind==='official'&&c?.kind!=='weapon'&&publishedBeforeRelease;
  const scope=officialPreview?'official-preview':video.referenceScope||(video.sourceKind==='creator'&&/overview and combo guide/i.test(video.title)?'commentary-guide':null);
  const scopeType={'basic-attacks':'기본 공격 모션','skill-excerpt':'개별 기술 모션','motion-excerpt':'개별 모션','commentary-guide':'해설 가이드','official-preview':'출시 전 공식 시연','official-weapon-showcase':'공식 무기 시연','official-combat-showcase':'전투 모션'}[scope];
  output.push({...video,...(scope?{referenceScope:scope}:{}),...(scopeType?{type:scopeType}:{}),characterId:c?.id||null,characterName:c?.name||null,characterKind:c?.kind||'character',characterReleaseDate:validDate(release)?release:null,characterReleaseOrder:c?.releaseOrder??null,characterReleaseBasis:c?.releaseBasis||null});
 }
 return {videos:output,excluded};
}
export function compareRelease(a,b,{descending=false}={}){
 const knownA=validDate(a.characterReleaseDate),knownB=validDate(b.characterReleaseDate);
 if(knownA!==knownB)return knownA?-1:1;
 const date=knownA?a.characterReleaseDate.localeCompare(b.characterReleaseDate):0;
 if(date)return descending?-date:date;
 if(!knownA&&!knownB){
  const game=String(a.gameId).localeCompare(String(b.gameId));if(game)return game;
  const orderedA=Number.isFinite(a.characterReleaseOrder),orderedB=Number.isFinite(b.characterReleaseOrder);
  if(orderedA!==orderedB)return orderedA?-1:1;
  if(orderedA){const order=a.characterReleaseOrder-b.characterReleaseOrder;if(order)return descending?-order:order;}
 }
 const name=String(a.characterName||a.title).localeCompare(String(b.characterName||b.title),'ko');
 if(name)return name;
 const korean=v=>v.language==='ko'||/[가-힣]/.test(v.title||'');
 return Number(korean(b))-Number(korean(a))||String(a.title).localeCompare(String(b.title),'ko')||String(a.id).localeCompare(String(b.id));
}
