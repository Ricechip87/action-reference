import {execFileSync} from 'node:child_process';
import {readFile,writeFile,unlink} from 'node:fs/promises';
import {deduplicate} from '../dedupe.mjs';
execFileSync(process.env.PYTHON||'python',['scripts/rss.py'],{stdio:'inherit'});
const result=JSON.parse(await readFile('data/rss-candidates.json','utf8'));
result.videos=deduplicate(result.videos).sort((a,b)=>Number(b.language==='ko')-Number(a.language==='ko')||b.publishedAt.localeCompare(a.publishedAt));
await writeFile('data/videos.json',JSON.stringify(result,null,2)+'\n');
await unlink('data/rss-candidates.json');
console.log(`Saved ${result.videos.length} RSS videos`);
