const base='https://api.github.com/repos/Ricechip87/action-reference';
function encode(value){const bytes=new TextEncoder().encode(JSON.stringify(value,null,2)+'\n');return btoa(Array.from(bytes,b=>String.fromCharCode(b)).join(''));}
function decode(value){return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(value.replace(/\s/g,'')),c=>c.charCodeAt(0))));}
export class GitHubSettings {
 constructor(token,request=fetch){if(!token?.trim())throw Error('GitHub 접근 토큰을 입력하세요.');this.token=token.trim();this.request=request;this.sha=null;}
 async call(method,path,body){const result=await this.request(base+path,{method,headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+this.token,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
  if(!result.ok){if([409,422].includes(result.status))throw Error('다른 곳에서 설정이 변경됐습니다. 저장소를 다시 연결한 뒤 수정해주세요.');if([401,403,404].includes(result.status))throw Error('GitHub 연결을 확인해주세요. 토큰의 저장소 선택, Contents 쓰기 권한, 만료 여부를 확인하세요.');throw Error('GitHub 요청 실패 (HTTP '+result.status+'). 잠시 후 다시 시도해주세요.');}return result.json();}
 async read(){const file=await this.call('GET','/contents/config.json?ref=main');const value=decode(file.content);if(!Array.isArray(value.games))throw Error('저장소 설정 형식이 올바르지 않습니다.');this.sha=file.sha;return value;}
 async save(value){if(!this.sha)throw Error('먼저 저장소를 연결해주세요.');const result=await this.call('PUT','/contents/config.json',{message:'chore: update collection rules from FRAME',branch:'main',sha:this.sha,content:encode({games:value.games})});this.sha=result.content.sha;return result.commit.sha;}
 disconnect(){this.token='';this.sha=null;}
}
export async function collectionStatus(sha){const response=await fetch(base+'/actions/runs?per_page=30',{cache:'no-store',headers:{Accept:'application/vnd.github+json'}});if(!response.ok)throw Error('진행 상태를 읽지 못했습니다. GitHub Actions에서 확인해주세요.');const result=await response.json();return result.workflow_runs?.find(run=>run.head_sha===sha);}
