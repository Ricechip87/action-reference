import test from 'node:test';
import assert from 'node:assert/strict';
import {deduplicate} from '../dedupe.mjs';
const base={gameId:'game',title:'Astra Character Trailer',duration:'PT2M',publishedAt:'2026-10-28T00:00:00Z',language:'en',localizedTitles:['아스트라 캐릭터 트레일러']};
test('localized versions collapse and Korean wins regardless of order',()=>{
 const en={...base,id:'english'},ko={...base,id:'korean',title:'아스트라 캐릭터 트레일러',language:'ko',localizedTitles:[]};
 for(const entries of [[en,ko],[ko,en]]){const out=deduplicate(entries);assert.equal(out.length,1);assert.equal(out[0].id,'korean');assert.equal(out[0].variants.length,2);}
});
test('different footage lengths, episodes, games and distant dates stay separate',()=>{
 const a={...base,id:'a'};
 for(const changes of [{duration:'PT3M'},{title:'Other Trailer',localizedTitles:[]},{gameId:'other'},{publishedAt:'2026-09-01T00:00:00Z'}])assert.equal(deduplicate([a,{...base,id:'b',...changes}]).length,2);
});
test('unknown duration never merges different IDs; same ID always collapses',()=>{
 assert.equal(deduplicate([{...base,id:'a',duration:undefined},{...base,id:'b',duration:undefined}]).length,2);
 assert.equal(deduplicate([{...base,id:'a'},{...base,id:'a',gameId:'other'}]).length,1);
});
test('language labels and punctuation normalize; distinct numbers survive',()=>{
 const a={...base,id:'a',title:'Trailer 2 [EN]',localizedTitles:[]};
 assert.equal(deduplicate([a,{...a,id:'b',title:'Trailer 2 [KR]',language:'ko'}]).length,1);
 assert.equal(deduplicate([a,{...a,id:'b',title:'Trailer 3 [KR]',language:'ko'}]).length,2);
});
