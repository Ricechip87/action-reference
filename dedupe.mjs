// Conservative metadata matching: never infer visual identity from duration alone.
const normalize=t=>String(t||'').normalize('NFKC').toLowerCase()
 .replace(/[\[（(]\s*(?:en|eng|english|kr|ko|kor|korean|jp|ja|japanese|cn|zh|한국어|日本語|中文)(?:\s*(?:ver\.?|version))?\s*[\]）)]/g,'')
 .replace(/[^\p{L}\p{N}]/gu,'');
function seconds(value){const m=/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$/.exec(value||'');return m?Number(m[1]||0)*3600+Number(m[2]||0)*60+Number(m[3]||0):0;}
function titles(v){return new Set([v.title,...(Array.isArray(v.localizedTitles)?v.localizedTitles:[])].map(normalize).filter(t=>t.length>=8));}
function match(a,b){if(a.id===b.id)return true;if(a.gameId!==b.gameId)return false;const x=seconds(a.duration),y=seconds(b.duration);if(!x||!y||Math.abs(x-y)>2)return false;const gap=Math.abs(Date.parse(a.publishedAt)-Date.parse(b.publishedAt));if(!Number.isFinite(gap)||gap>7*86400000)return false;const names=titles(a);return [...titles(b)].some(t=>names.has(t));}
function preference(v){const language=String(v.language||'').toLowerCase();if(/^ko(?:-|$)/.test(language))return 3;if(/[가-힣]/.test(v.title||''))return 2;return 0;}
export function deduplicate(videos){const groups=[];for(const video of videos){const group=groups.find(g=>g.every(member=>match(member,video)));if(group)group.push(video);else groups.push([video]);}return groups.map(group=>{const preferred=[...group].sort((a,b)=>preference(b)-preference(a))[0];const variants=new Map();for(const v of group)for(const item of v.variants||[v])variants.set(item.id,{id:item.id,title:item.title,language:item.language||''});return {...preferred,variants:[...variants.values()]};});}
