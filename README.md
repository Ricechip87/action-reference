# FRAME — 공식 전투 모션 레퍼런스

GitHub Pages: https://ricechip87.github.io/action-reference/

## 현재 수집 범위

API 키 없이 아래 한국어 공식 채널의 공개 RSS를 약 6시간마다 확인합니다. 명조는 제목에 **전투 모션**, 이환은 **캐릭터 쇼케이스**가 들어간 영상만 수집합니다. 각 게임 전용 공식 채널이므로 게임명이 제목에 없어도 제목 조건에 맞으면 포함합니다. 젠레스 존 제로는 현재 수집을 꺼뒀습니다. 한국어 영상이 먼저 표시됩니다.

- 명조: https://www.youtube.com/@WW_KR_Official/videos — 기존 26개
- 이환: https://www.youtube.com/@NTE_KO/videos — 기존 캐릭터 쇼케이스 10개 (캐릭터 PV 제외)

## 채널과 수집 조건 변경

사이트에서 게임 이름·검색어·공식 채널 주소·제목 조건을 등록할 수 있습니다. @핸들, /videos 주소, UC 채널 ID를 지원합니다. 게임별 수집 켜기·끄기도 제공합니다. 이 설정은 현재 브라우저에만 저장됩니다.

실제 예약 수집에 적용하려면 하단의 **설정 내보내기**로 받은 config.json을 GitHub 저장소의 config.json에 반영하세요. 파일 저장 후 자동 배포됩니다. GitHub Pages에는 설정을 서버에 저장하는 기능이 없어 이 단계가 필요합니다. 수동 추가한 영상 역시 브라우저에 저장되며 다른 기기에 동기화되지 않습니다. 설정 가져오기는 기존 설정을 교체하므로 먼저 백업하세요.

## RSS 범위와 중복

최초 한 번 공식 채널의 전체 동영상 탭·채널 내부 검색·공개 검색을 대조하고, 영상별 공식 채널 ID와 제목·게시일을 확인하여 data/archive.json에 초기 목록을 보관합니다. 검색 결과의 영어 번역 제목도 후보에 포함하고 한국어 원제를 다시 확인합니다. 이후에는 RSS의 최근 목록에서 신규 영상을 추가하며, 과거 영상은 기간 제한 없이 유지합니다. 전체 목록 재수집은 자동 실행하지 않습니다. 이전 배포 결과를 읽지 못하면 수집·배포를 중단하여 누적 내역을 보호합니다. RSS 범위를 넘어서는 빠른 업로드나 수집 중단 중 영상은 놓칠 수 있습니다.

동일 영상 ID는 한 번만 표시합니다. 한국어를 우선하며, 이번 실험은 한국어 채널만 수집합니다. RSS에는 길이·번역 제목이 없어 서로 다른 ID의 언어별 내용 중복은 자동으로 확정하지 않습니다. 기존 메타데이터 기반 중복 함수는 해당 정보가 제공된 경우에만 작동합니다.

## 자동화와 실패 처리

.github/workflows/pages.yml에서 Python 표준 라이브러리로 공개 RSS를 읽고 Node로 중복을 정리한 뒤 배포합니다. API 키나 GitHub Secrets 등록은 필요하지 않습니다. 전체 채널 수집 실패 시 배포를 중단하고 기존 사이트를 유지합니다. 일부 실패는 사이트에 표시하고 이전 수집 데이터를 가능한 범위에서 유지합니다. 예약 작업은 GitHub 사정에 따라 지연되거나 비활성화될 수 있으며 Actions에서 확인할 수 있습니다. 최신 확인 시간은 사이트에 표시됩니다.

채널이 공식인지 자동 인증하지 않으므로 등록 전 출처를 확인하세요. 사이트에 배포된 설정과 영상 목록은 공개됩니다. 외부 재생 제한 영상은 유튜브에서 열기를 이용하세요.

## 로컬 실행 및 검증

Python 3.12 이상과 Node 24 기준입니다. 추가 패키지는 필요하지 않습니다.

- 수집: node scripts/collect.mjs
- 테스트: python -m unittest discover -s scripts -p rss_test.py
- 중복 테스트: node --test scripts/dedupe.test.mjs
- 미리보기: python -m http.server 8000 → http://localhost:8000

## 기본 채널 출처

명조 한국어 채널은 개발사의 Google Play 안내에 링크되어 있습니다: https://play.google.com/store/apps/details?hl=ko&id=com.kurogame.wutheringwaves.global

최초 전체 목록 다시 만들기(필요할 때만): yt-dlp 설치 후 `python scripts/backfill.py --game wuthering-waves` 또는 `python scripts/backfill.py --game neverness-to-everness`. 영상 파일은 받지 않고 공개 메타데이터만 읽습니다. 예약 수집에는 yt-dlp 설치가 필요하지 않습니다.
