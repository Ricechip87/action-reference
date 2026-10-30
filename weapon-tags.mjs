export const WEAPON_TYPES=[
 ['sword','한손검'],['greatsword','대검'],['katana','도검·태도'],['dual-blades','쌍검'],['dagger','단검'],
 ['spear','창·폴암'],['axe','도끼'],['hammer','해머'],['scythe','낫'],['fist','격투·권갑'],
 ['pistol','권총'],['firearm','총기·포'],['bow','활'],['staff','지팡이'],['focus','법구·마법'],
 ['whip','채찍·사슬'],['shield','방패'],['summon','소환·인형'],['special','특수 무기']
].map(([id,label])=>({id,label}));
const allowed=new Set(WEAPON_TYPES.map(t=>t.id));
const own=(value,key)=>Object.prototype.hasOwnProperty.call(value||{},key);
export const normalizeWeaponTags=tags=>Array.isArray(tags)?[...new Set(tags.filter(t=>allowed.has(t)))]:[];
export function weaponTagsFor(video,{characters=[],videoWeaponTags={},characterWeaponTags={}}={}){
 for(const id of [video.id,...(video.variants||[]).map(v=>v.id)])if(own(videoWeaponTags,id))return normalizeWeaponTags(videoWeaponTags[id]);
 if(video.characterId&&own(characterWeaponTags,video.characterId))return normalizeWeaponTags(characterWeaponTags[video.characterId]);
 if(own(video,'weaponTags'))return normalizeWeaponTags(video.weaponTags);
 return normalizeWeaponTags(characters.find(c=>c.id===video.characterId)?.weaponTags);
}
export const matchesWeapon=(tags,selected)=>!selected||(selected==='unclassified'?tags.length===0:tags.includes(selected));
export function updateWeaponTags(config,video,tags,{sameCharacter=false,videos=[]}={}){
 const next={...config,videoWeaponTags:{...config.videoWeaponTags},characterWeaponTags:{...config.characterWeaponTags}};
 const clean=normalizeWeaponTags(tags);
 if(sameCharacter&&video.characterId){
  next.characterWeaponTags[video.characterId]=clean;
  for(const row of [video,...videos.filter(v=>v.characterId===video.characterId)])for(const id of [row.id,...(row.variants||[]).map(v=>v.id)])delete next.videoWeaponTags[id];
 }else for(const id of [video.id,...(video.variants||[]).map(v=>v.id)])next.videoWeaponTags[id]=clean;
 return next;
}
