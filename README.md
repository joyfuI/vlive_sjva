# V LIVE_sjva

[SJVA](https://sjva.me/) 용 V LIVE 플러그인  
SJVA에서 V LIVE를 자동으로 다운로드할 수 있습니다.

## 설치

> **반드시 [youtube-dl 플러그인](https://github.com/joyfuI/youtube-dl)이 설치되어 있어야지만 작동합니다!**

SJVA에서 "시스템 → 설정 → 플러그인 → 플러그인 목록 → 플러그인 수동 설치" 칸에 저장소 주소를 넣고 설치 버튼을 누르면 됩니다.  
`https://github.com/joyfuI/vlive`

## 잡담

cookiefile 경로를 지정하면 가입이 필요한 영상도 다운로드 할 수 있습니다.  
cookiefile 추출 방법은 [여기](https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl)를 참고해주세요.  
유료 영상은 안되는 듯...?

## Changelog

v2.0.1

- 파이썬 3.8 호환성 문제 수정

v2.0.0

- 최신 플러그인 구조로 변경
- 스케줄 추가가 안 되는 문제 수정

v1.1.0

- 최근 방송 기능 추가  
  최근 방송 목록을 확인하고 바로 다운로드 요청을 보낼 수 있습니다.
- 설정에 cookiefile 경로 지정 추가
- 라이브 도중 다시보기가 올라오면 라이브 다운로드를 시작하지 않는 문제 개선

v1.0.0

- SJVA3 대응
- 설정에 경로 선택 버튼 추가

v0.1.5

- 스케줄링 중지가 안되는 문제 수정

v0.1.4

- 마지막 실행이 업데이트되지 않는 문제 수정

v0.1.3

- 스케줄러 다운로드 실패 시 예외처리 추가

v0.1.2

v0.1.1

- 스케줄러가 더 빠르게 동작하도록 수정

v0.1.0

- 최초 공개
