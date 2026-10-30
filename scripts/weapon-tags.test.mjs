import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeWeaponTags,weaponTagsFor,matchesWeapon,updateWeaponTags} from '../weapon-tags.mjs';
const characters=[{id:'ww:jinhsi',weaponTags:['greatsword']},{id:'ww:unknown'}];
const video={id:'abcdefghijk',characterId:'ww:jinhsi',variants:[{id:'translated1'}]};

test('tags are a clean ordered set and unknown labels are not accepted',()=>{
 assert.deepEqual(normalizeWeaponTags(['sword','greatsword','sword','<script>']),['sword','greatsword']);
 assert.deepEqual(normalizeWeaponTags('greatsword'),[]);
});
test('video overrides, including an intentional empty list, win over character defaults',()=>{
 assert.deepEqual(weaponTagsFor(video,{characters}),['greatsword']);
 assert.deepEqual(weaponTagsFor(video,{characters,characterWeaponTags:{'ww:jinhsi':['sword','spear']}}),['sword','spear']);
 assert.deepEqual(weaponTagsFor(video,{characters,videoWeaponTags:{abcdefghijk:[]}}),[]);
 assert.deepEqual(weaponTagsFor(video,{characters,videoWeaponTags:{translated1:['bow']}}),['bow']);
});
test('weapon filtering supports all, unclassified, and one of multiple weapon tags',()=>{
 assert.equal(matchesWeapon(['greatsword','fist'],'greatsword'),true);
 assert.equal(matchesWeapon(['sword'],'greatsword'),false);
 assert.equal(matchesWeapon([],'unclassified'),true);
 assert.equal(matchesWeapon(['sword'],'unclassified'),false);
 assert.equal(matchesWeapon([],''),true);
});

test('a class awakening uses that style weapon, while an explicit video override still wins',()=>{
 const classes=[{id:'bdo:warrior',weaponTags:['sword','shield'],weaponTagVariants:[{keywords:['Awakening','각성'],tags:['greatsword']}]}];
 const original={id:'classnormal',characterId:'bdo:warrior',title:'Warrior Class Skills'};
 const awakening={...original,title:'Warrior Awakening Skills'};
 assert.deepEqual(weaponTagsFor(original,{characters:classes}),['sword','shield']);
 assert.deepEqual(weaponTagsFor(awakening,{characters:classes}),['greatsword']);
 assert.deepEqual(weaponTagsFor({...awakening,weaponTags:['fist']},{characters:classes}),['fist']);
});
test('a single-video edit covers language variants without affecting another video; character edit clears its stale overrides',()=>{
 const config={games:[{id:'ww'}],videoWeaponTags:{other:['bow']}};
 const one=updateWeaponTags(config,video,['spear']);
 assert.deepEqual(one.videoWeaponTags,{other:['bow'],abcdefghijk:['spear'],translated1:['spear']});
 assert.equal(config.videoWeaponTags.abcdefghijk,undefined);
 const both=updateWeaponTags(one,video,['greatsword'],{sameCharacter:true,videos:[video,{id:'other',characterId:'ww:jinhsi'},{id:'unrelated',characterId:'ww:unknown'}]});
 assert.deepEqual(both.characterWeaponTags,{'ww:jinhsi':['greatsword']});
 assert.equal(both.videoWeaponTags.abcdefghijk,undefined);
 assert.equal(both.videoWeaponTags.other,undefined);
 assert.deepEqual(both.games,config.games);
});
