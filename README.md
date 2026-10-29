# FRAME — 액션 레퍼런스

설치 과정이 없는 GitHub Pages용 정적 사이트입니다. 게임과 채널 등록, 제목 검색, 게임·종류 필터, 영상 링크 직접 추가, 유튜브 내장 재생, 설정 내보내기·가져오기를 지원합니다. 명조, 젠레스 존 제로, 이환과 각 게임의 글로벌 공식 채널이 기본 등록되어 있습니다. 영상 목록은 자동 수집 연결 후 채워집니다.

## GitHub Pages에 올리기

1. GitHub 저장소를 만들고 이 폴더의 내용을 main 브랜치에 올립니다. 숨김 폴더 `.github`도 포함해야 합니다.
2. 저장소 Settings → Pages → Build and deployment → Source에서 GitHub Actions를 선택합니다.
3. Actions에서 Collect and publish를 실행합니다. 완료 후 Pages 주소로 접속합니다. API 키 없이도 사이트와 직접 영상 추가 기능은 작동합니다.

## 자동 수집 연결

1. 사이트의 게임 · 채널 관리에서 게임명, 다국어 검색어, 공식 채널 ID를 추가합니다. 채널이 공식인지 직접 확인하세요. UC로 시작하는 채널 ID 또는 @핸들을 지원합니다. @핸들 또는 채널 주소를 그대로 입력할 수도 있습니다.
2. 하단의 설정 내보내기를 눌러 받은 config.json으로 저장소의 config.json을 교체합니다. 게임 ID는 유지하세요.
3. Google Cloud에서 YouTube Data API v3를 활성화하고 API 키를 만듭니다. 키의 API 제한을 YouTube Data API v3로 설정합니다.
4. GitHub 저장소 Settings → Secrets and variables → Actions → New repository secret에서 이름을 YOUTUBE_API_KEY로 지정하고 키를 저장합니다.
5. Actions를 실행합니다. 이후 약 6시간마다 갱신합니다. 예약 실행은 지연될 수 있고 저장소 상태에 따라 비활성화될 수 있으므로 Actions에서 확인하세요.

채널별 최신 최대 200개 업로드 중 최근 90일 영상에서 제목·설명에 검색어가 있는 영상을 수집합니다. 누락을 줄이려면 게임의 언어별 이름을 등록하세요. 장기간 영상 보관이 아닌 최근 영상 목록이며, 수집 결과는 배포 결과물에만 저장됩니다. 요청 오류가 나면 배포를 중단하여 기존 배포를 유지합니다.

## 저장과 공개 범위

- 화면에서 추가·삭제한 설정과 직접 추가한 영상은 현재 브라우저 localStorage에 저장됩니다. 다른 기기와 자동 동기화되지 않습니다. 브라우저 데이터를 삭제하면 사라지므로 설정을 내보내 보관하세요.
- 사이트에서 설정을 바꾼 것만으로 GitHub의 자동 수집 대상이 바뀌지는 않습니다. 내보낸 config.json을 저장소에 반영해야 합니다. 화면에서 즉시 서버에 저장하려면 추후 로그인과 별도 서버가 필요합니다.
- 수집된 영상은 등록된 게임 ID가 일치할 때 표시됩니다. 저장소 설정을 바꾼 뒤 기존 브라우저에서도 해당 설정을 가져오세요.
- GitHub Secrets는 API 키를 수집 작업에 전달하기 위한 암호화된 보관 기능입니다. 사이트를 비공개로 만드는 기능이 아닙니다. 키는 웹 파일에 포함하지 않습니다. 워크플로를 변경할 수 있는 저장소 관리자는 키를 사용하는 작업도 변경할 수 있으므로 권한을 신뢰하는 사람에게만 주세요.
- Pages 방문자는 공개된 게임·채널 설정과 영상 목록을 볼 수 있습니다. 개인적인 정보나 비밀을 config.json에 넣지 마세요.
- 공식 여부를 자동 인증하지 않습니다. 직접 추가 영상은 출처 확인 표시가 붙습니다. 외부 재생 차단 영상은 유튜브 링크로 열어주세요.

## 로컬 미리보기

이 폴더에서 `python -m http.server 8000`을 실행하고 http://localhost:8000 으로 접속합니다. 파일을 더블클릭하는 방식 대신 HTTP 주소를 사용하세요.

## 확인

`node --check app.js` 및 `node --check scripts/collect.mjs`로 문법을 확인할 수 있습니다. 실제 수집에는 API 키와 채널 설정이 필요합니다.

## 기본 채널 확인 출처

- 명조 @WutheringWaves: https://wutheringwaves.kurogames.com/en/main/news/detail/738
- 젠레스 존 제로 @ZZZ_Official: https://zenless.hoyoverse.com/vi-vn/news/124214
- 이환 @NTE_Official: https://steamcommunity.com/app/4508340/ (공식 방송 안내)

이전 버전을 이미 사용했다면 하단 설정 가져오기에서 이 폴더의 config.json을 선택하여 기본 게임을 적용하세요. 가져오기는 현재 설정을 교체하므로 기존 설정은 먼저 내보내 보관하세요.

## 중복 처리

같은 유튜브 영상 ID는 전체 게임에서 한 번만 수집·표시합니다. 여러 게임 검색어에 해당하면 config.json에서 먼저 등록된 게임에 배정됩니다. 직접 추가할 때도 같은 ID의 중복을 막습니다. 언어별 영상은 원제·YouTube 번역 제목 중 하나가 일치하고, 길이 차이가 2초 이내이며 게시일이 7일 이내인 경우 같은 게임 안에서 하나로 묶습니다. 한국어 언어 정보가 있는 영상을 먼저, 다음으로 한글 제목 영상을 우선 표시합니다. 묶인 버전 정보는 variants에 보관합니다. 영상·음성 자체를 비교하는 방식은 아니므로 모든 중복을 찾거나 내용 동일성을 보장하지는 않습니다. 번역 제목이나 길이 정보가 없으면 서로 다른 ID는 별개로 남깁니다. 직접 추가한 영상은 길이·번역 정보가 없어 ID 기준으로만 중복을 확인합니다. 한국어 공식 채널을 등록해야 그 채널의 한국어 버전을 수집할 수 있습니다.

검증: `node --test scripts/dedupe.test.mjs`

한국어 기본 채널: @WW_KR_Official, @ZZZ_KO, @NTE_KO. 한국어·글로벌 채널을 함께 수집합니다. 기존 브라우저에서는 새 config.json을 가져와야 채널 추가 설정이 적용됩니다.
한국어 채널 확인: https://play.google.com/store/apps/details?hl=ko&id=com.kurogame.wutheringwaves.global , https://www.youtube.com/@ZZZ_KO , https://play.google.com/store/apps/details?hl=ko&id=com.hottagames.nte
