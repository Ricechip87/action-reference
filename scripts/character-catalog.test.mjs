import test from 'node:test';
import assert from 'node:assert/strict';
import {identifyCharacter,enrichVideos,compareRelease} from '../character-catalog.mjs';
const characters=[
 {id:'anby',gameId:'zzz',name:'엔비',aliases:['Anby','Anby Demara'],releaseDate:'2024-07-04'},
 {id:'silver',gameId:'zzz',name:'0호·엔비',aliases:['Silver Soldier Anby','Soldier 0 - Anby'],releaseDate:'2025-03-12'},
 {id:'plume',gameId:'pgr',name:'루시아·아우',aliases:['Lucia: Plume'],releaseDate:'2021-12-22'},
 {id:'dawn',gameId:'pgr',name:'루시아·여명',aliases:['Lucia: Dawn'],releaseDate:'2021-07-16'},
 {id:'future',gameId:'zzz',name:'미출시',aliases:['Future'],releaseDate:'2026-11-04'}
];
test('release order wins over upload date and Korean preference applies within a character',()=>{
 const videos=enrichVideos([
  {id:'late',gameId:'zzz',title:'Silver Soldier Anby showcase',publishedAt:'2024-01-01',language:'ko'},
  {id:'early-en',gameId:'zzz',title:'Anby showcase',publishedAt:'2026-01-01',language:'en'},
  {id:'early-ko',gameId:'zzz',title:'엔비 전투 모션',publishedAt:'2026-02-01',language:'ko'}
 ],characters,{asOf:'2026-10-30'}).videos.sort(compareRelease);
 assert.deepEqual(videos.map(v=>v.id),['early-ko','early-en','late']);
});
test('longer variant name wins, frame variants and games stay distinct',()=>{
 assert.equal(identifyCharacter({gameId:'zzz',title:'Silver Soldier Anby Skill Showcase'},characters)?.id,'silver');
 assert.equal(identifyCharacter({gameId:'pgr',title:'Lucia Plume | Moveset Showcase'},characters)?.id,'plume');
 assert.equal(identifyCharacter({gameId:'pgr',title:'Lucia: Dawn | Moveset Showcase'},characters)?.id,'dawn');
 assert.equal(identifyCharacter({gameId:'other',title:'Anby Showcase'},characters),null);
 assert.equal(identifyCharacter({gameId:'pgr',title:'Lucia showcase'},characters),null);
});
test('unknown and multi-character titles never borrow upload dates as release dates',()=>{
 assert.equal(identifyCharacter({gameId:'zzz',title:'Anby and Future compilation'},characters),null);
 const {videos}=enrichVideos([{gameId:'zzz',title:'Unknown',publishedAt:'2000-01-01'}, {gameId:'zzz',title:'Anby',publishedAt:'2026-01-01'}],characters);
 assert.equal(videos.sort(compareRelease)[1].title,'Unknown');
 assert.equal(videos[1].characterReleaseDate,null);
});
test('pre-release creator footage is removed while official previews remain',()=>{
 const {videos,excluded}=enrichVideos([{gameId:'zzz',title:'Future showcase',sourceKind:'creator'},{gameId:'zzz',title:'Future official',sourceKind:'official'}],characters,{asOf:'2026-10-30'});
 assert.equal(videos.length,1);assert.equal(videos[0].sourceKind,'official');assert.equal(excluded.length,1);
});
test('multi-character creator compilations are excluded and pre-release upload alone does not prove CBT',()=>{
 const {videos,excluded}=enrichVideos([{gameId:'zzz',title:'Anby and Future skills',sourceKind:'creator'},{gameId:'zzz',title:'Anby skills',sourceKind:'creator',publishedAt:'2024-07-01'}],characters,{asOf:'2026-10-30'});
 assert.equal(videos.length,1);assert.equal(videos[0].title,'Anby skills');assert.equal(excluded.length,1);
});
test('verified localized metadata identifies characters without changing the displayed title',()=>{
 const video={gameId:'pgr',title:'ルシアのモーション',localizedTitles:['Lucia: Plume Moveset'],sourceKind:'creator'};
 assert.equal(identifyCharacter(video,characters)?.id,'plume');
 assert.equal(enrichVideos([video],characters).videos[0].title,video.title);
});
test('reviewed partial motion scope stays explicit after a feed refresh',()=>{
 const result=enrichVideos([{id:'partial',gameId:'zzz',title:'Anby moves',sourceKind:'creator',type:'캐릭터 무브셋',referenceScope:'basic-attacks'}],characters).videos[0];
 assert.equal(result.type,'기본 공격 모션');
 assert.equal(result.referenceScope,'basic-attacks');
});

test('Japanese motion titles accept grammatical suffixes without matching another name',()=>{
 const catalog=[{id:'jp-danjin',gameId:'ww',name:'단근',aliases:['Danjin','丹瑾']},{id:'jp-jean',gameId:'gi',name:'진',aliases:['Jean','ジン']}];
 assert.equal(identifyCharacter({gameId:'ww',title:'≪鳴潮≫丹瑾の戦闘モーションを見るだけ',sourceKind:'creator'},catalog)?.id,'jp-danjin');
 assert.equal(identifyCharacter({gameId:'gi',title:'【原神】ジン戦闘モーション',sourceKind:'creator'},catalog)?.id,'jp-jean');
 assert.equal(identifyCharacter({gameId:'gi',title:'オリジンの戦闘モーション',sourceKind:'creator'},catalog),null);
 const forms=[{id:'havoc',gameId:'ww',name:'방랑자·인멸',aliases:['漂泊者(男)・消滅']},{id:'spectro',gameId:'ww',name:'방랑자·회절',aliases:['漂泊者(男)・回折']}];
 assert.equal(identifyCharacter({gameId:'ww',title:'≪鳴潮≫漂泊者(男)・消滅の戦闘モーションを見るだけ',sourceKind:'creator'},forms)?.id,'havoc');
});

test('new public-list entries require a release-safe publication window; known records remain',()=>{
 const rows=[{id:'uncertain',gameId:'zzz',title:'Anby skills',sourceKind:'creator',requiresReleaseWindow:true,publicationWindow:{earliest:'2024-06-01',latest:'2024-08-01'}},{id:'safe',gameId:'zzz',title:'Anby skills',sourceKind:'creator',requiresReleaseWindow:true,publicationWindow:{earliest:'2025-01-01',latest:'2025-02-01'}},{id:'known',gameId:'zzz',title:'Anby skills',sourceKind:'creator',requiresReleaseWindow:false,publicationWindow:{earliest:'2024-06-01',latest:'2024-08-01'}}];
 const result=enrichVideos(rows,characters,{asOf:'2026-10-30'});
 assert.deepEqual(result.videos.map(v=>v.id),['safe','known']);
 assert.equal(result.excluded[0].id,'uncertain');
});
