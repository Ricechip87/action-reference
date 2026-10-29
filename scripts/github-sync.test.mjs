import test from 'node:test';
import assert from 'node:assert/strict';
import {GitHubSettings} from '../github-sync.mjs';
const payload={games:[{id:'ww',name:'명조',channels:['@WW_KR_Official'],keywords:['명조'],includeKeywords:['전투 모션']}]};
test('settings roundtrip uses UTF-8, expected SHA, and excludes personal videos',async()=>{
 const requests=[];
 const fake=async(url,options)=>{requests.push({url,options});return {ok:true,status:200,json:async()=>options.method==='PUT'?{content:{sha:'next'},commit:{sha:'commit'}}:{sha:'base',content:Buffer.from(JSON.stringify(payload)).toString('base64')}};};
 const client=new GitHubSettings('private-test-token',fake);
 assert.deepEqual(await client.read(),payload);
 assert.equal(await client.save({...payload,videos:[{id:'personal'}]}),'commit');
 const body=JSON.parse(requests[1].options.body);
 assert.equal(body.sha,'base');assert.deepEqual(JSON.parse(Buffer.from(body.content,'base64').toString()),payload);
 assert.equal(requests[1].options.headers.Authorization,'Bearer private-test-token');
 assert.ok(requests.every(r=>new URL(r.url).origin==='https://api.github.com'));
});
test('conflict refuses overwriting someone else’s settings',async()=>{
 let put=false;const client=new GitHubSettings('token',async()=>({ok:!put,status:put?409:200,json:async()=>({sha:'base',content:Buffer.from(JSON.stringify(payload)).toString('base64')})}));
 await client.read();put=true;await assert.rejects(()=>client.save(payload),/다른 곳에서/);
});
test('cannot save before reading revision or save without connection',async()=>{
 assert.throws(()=>new GitHubSettings(''),/토큰/);
 const client=new GitHubSettings('token',()=>{throw Error('Should not fetch');});
 await assert.rejects(()=>client.save(payload),/먼저/);
});
