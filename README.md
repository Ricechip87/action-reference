# FRAME — 공식 전투 모션 레퍼런스

GitHub Pages: https://ricechip87.github.io/action-reference/

## 현재 수집 범위

API 키 없이 아래 한국어 공식 채널의 공개 RSS를 약 6시간마다 확인합니다. 명조는 제목에 **전투 모션**, 이환은 **캐릭터 쇼케이스**가 들어간 영상만 수집합니다. 각 게임 전용 공식 채널이므로 게임명이 제목에 없어도 제목 조건에 맞으면 포함합니다. 젠레스 존 제로는 제목에 **캐릭터 플레이**가 들어간 영상만 수집합니다. 한국어 영상이 먼저 표시됩니다.

- 명조: https://www.youtube.com/@WW_KR_Official/videos — 기존 26개
- 젠레스 존 제로: https://www.youtube.com/@ZZZ_KO/videos — 캐릭터 플레이 (캐릭터 PV 제외)
- 이환: https://www.youtube.com/@NTE_KO/videos — 기존 캐릭터 쇼케이스 10개 (캐릭터 PV 제외)

## 사이트에서 채널과 수집 조건 변경

1. 오른쪽 위 **관리자 연결**을 누릅니다.
2. GitHub에서 이 저장소(action-reference)만 선택한 Fine-grained personal access token을 만듭니다. Contents 권한만 Read and write로 지정합니다. Actions 쓰기 권한은 필요하지 않습니다.
3. 토큰을 사이트의 관리자 연결 창에 입력합니다. 채팅에 보내거나 저장소 파일에 넣지 마세요.
4. **게임 · 채널 관리**에서 게임 이름, 채널 주소, 제목 조건을 입력하고 **저장하고 수집 시작**을 누릅니다. 기존 게임은 수정·삭제·수집 켜기/끄기도 가능합니다.

설정 파일을 따로 올릴 필요가 없습니다. 사이트가 GitHub Contents API로 config.json을 저장하면 해당 변경으로 Actions 수집·배포가 실행됩니다. 보통 1~3분 뒤 결과가 반영되며 진행 상태를 관리 창에서 확인할 수 있습니다. 새 채널은 최근 RSS 목록부터 수집합니다. 전체 과거 영상은 별도 초기 수집 작업이 필요합니다.

GitHub 토큰은 공개 코드·설정 파일·내보내기에 포함하지 않습니다. api.github.com으로만 전송하며 현재 탭의 sessionStorage에 보관하므로 탭을 닫거나 연결 해제 시 재연결이 필요합니다. 저장소를 수정할 권한이 없는 방문자는 설정을 변경할 수 없습니다. 연결 해제 후에도 이미 저장한 예약 수집은 계속 실행됩니다. 기존 로컬 설정을 공유 설정으로 옮기려면 연결 후 설정 가져오기를 이용할 수 있습니다.

공유 설정은 페이지를 열 때마다 갱신됩니다. 직접 추가한 영상은 현재 브라우저에만 저장됩니다. 설정 내보내기/가져오기는 백업용으로 유지합니다. 다른 곳에서 동시에 설정을 바꾸면 SHA 충돌을 감지하여 덮어쓰지 않으므로 다시 연결하여 최신 설정으로 수정하세요.

## RSS 범위와 중복

최초 한 번 공식 채널의 전체 동영상 탭·채널 내부 검색·공개 검색을 대조하고, 영상별 공식 채널 ID와 제목·게시일을 확인하여 data/archive.json에 초기 목록을 보관합니다. 검색 결과의 영어 번역 제목도 후보에 포함하고 한국어 원제를 다시 확인합니다. 이후에는 RSS의 최근 목록에서 신규 영상을 추가하며, 과거 영상은 기간 제한 없이 유지합니다. 전체 목록 재수집은 자동 실행하지 않습니다. 이전 배포 결과를 읽지 못하면 수집·배포를 중단하여 누적 내역을 보호합니다. RSS 범위를 넘어서는 빠른 업로드나 수집 중단 중 영상은 놓칠 수 있습니다.

동일 영상 ID는 한 번만 표시합니다. 한국어를 우선하며, 이번 실험은 한국어 채널만 수집합니다. RSS에는 길이·번역 제목이 없어 서로 다른 ID의 언어별 내용 중복은 자동으로 확정하지 않습니다. 기존 메타데이터 기반 중복 함수는 해당 정보가 제공된 경우에만 작동합니다.

## 자동화와 실패 처리

.github/workflows/pages.yml에서 Python 표준 라이브러리로 공개 RSS를 읽고 Node로 중복을 정리한 뒤 배포합니다. API 키나 GitHub Secrets 등록은 필요하지 않습니다. 전체 채널 수집 실패 시 배포를 중단하고 기존 사이트를 유지합니다. 일부 실패는 사이트에 표시하고 이전 수집 데이터를 가능한 범위에서 유지합니다. 예약 작업은 GitHub 사정에 따라 지연되거나 비활성화될 수 있으며 Actions에서 확인할 수 있습니다. 최신 확인 시간은 사이트에 표시됩니다.

채널이 공식인지 자동 인증하지 않으므로 등록 전 출처를 확인하세요. 사이트에 배포된 설정과 영상 목록은 공개됩니다. 외부 재생 제한 영상은 유튜브에서 열기를 이용하세요.

## 로컬 실행 및 검증

Python 3.12 이상과 Node 24 기준입니다. 예약 수집과 사이트 실행에는 추가 패키지가 필요하지 않습니다.

- 수집: node scripts/collect.mjs
- 테스트: python -m unittest discover -s scripts -p rss_test.py
- 중복 테스트: node --test scripts/dedupe.test.mjs
- 미리보기: python -m http.server 8000 → http://localhost:8000

## 기본 채널 출처

명조 한국어 채널은 개발사의 Google Play 안내에 링크되어 있습니다: https://play.google.com/store/apps/details?hl=ko&id=com.kurogame.wutheringwaves.global

최초 전체 목록 다시 만들기(필요할 때만): yt-dlp 설치 후 `python scripts/backfill.py --game wuthering-waves` 또는 `python scripts/backfill.py --game neverness-to-everness`. 영상 파일은 받지 않고 공개 메타데이터만 읽습니다. 예약 수집에는 yt-dlp 설치가 필요하지 않습니다.

젠레스 존 제로 최초 목록 재확인: `python scripts/backfill.py --game zenless-zone-zero`. 게임별 카테고리에 적재하며 기존 명조·이환 목록도 보존합니다.

저장소 연결 테스트: `node --test scripts/github-sync.test.mjs`. 실 토큰 없이 UTF-8 저장, 개인 영상 제외, SHA 충돌, 미연결 차단을 검증합니다.
