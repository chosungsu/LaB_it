# LaB_it (라벨링 도구)

[English](README.md) | [한국어](README.ko.md)

CustomTkinter를 사용한 현대적인 GUI 인터페이스를 제공하며, 이미지 내의 객체를 쉽게 분할하고 분석할 수 있는 라벨링 도구입니다.

## 주요 기능

- 직관적인 GUI 인터페이스
- 이미지 업로드 및 관리
- 클릭 기반 객체 분할
- 분할된 객체 저장 및 관리
- Google Drive 연동 지원

## 설치 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv .venv
# Windows
source .venv/Scripts/activate
# Linux/Mac
source .venv/bin/activate
```

2. 필요한 패키지 설치
```bash
pip install .
```

3. Google Cloud Service Account 설정
   1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
   2. 새 프로젝트 생성 또는 기존 프로젝트 선택
   3. 좌측 메뉴에서 'IAM 및 관리' > '서비스 계정' 선택
   4. '서비스 계정 만들기' 클릭
   5. 서비스 계정 이름 입력 (예: lab-it-service)
   6. '만들기 및 계속' 클릭
   7. 역할 선택: 'Editor' 권한 부여
   8. '완료' 클릭
   9. 생성된 서비스 계정 클릭
   10. '키' 탭 선택 > '키 추가' > '새 키 만들기' > JSON 선택
   11. 다운로드된 JSON 파일을 프로젝트 루트 폴더에 `service_account.json` 이름으로 저장

4. 앱 실행
```bash
python -m LaB_it
```

## 프로젝트 구조
```
LaB_it/
├── LaB_it/
│   ├── annotations/     # 분할 결과 저장
│   ├── assets/         # 이미지 및 리소스
│   ├── dialog/         # UI 모듈
│   ├── tasks/         # 작업 관련 모듈
│   ├── __init__.py
│   ├── __main__.py    # 메인 실행 파일
│   ├── setting.py    # 아이콘, 폴더경로, 색상 등 설정 파일
│   └── app.py    # 메인 로직
├── .gitignore
├── README.md
├── requirements.txt    # 필수 패키지 목록
└── setup.py           # 설치 설정
```

## 필수 패키지
- torch & torchvision: 딥러닝 프레임워크
- customtkinter: 모던 GUI 인터페이스
- opencv-python: 이미지 처리
- google-api-python-client: Google Drive 연동

## 참고 자료
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

## 라이선스
이 프로젝트는 MIT License with Commons Clause 하에 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

### 허용되는 사항
- 개인적인 용도로 소프트웨어 사용
- 코드 수정 및 배포
- 교육 및 연구 목적으로 사용
- 비상업적 프로젝트에 통합

### 제한되는 사항
- 소프트웨어 판매
- 소프트웨어 기반의 유료 서비스 제공
- 소프트웨어의 상업적 호스팅
- 소프트웨어 관련 유료 컨설팅/지원 서비스

모든 수정 및 배포 시 원본 저작권 및 라이선스 고지를 포함해야 합니다. 