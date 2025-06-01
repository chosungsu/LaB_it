# Segment Tool (SAM 기반 객체 분할)

이 프로젝트는 Meta의 Segment Anything Model(SAM)을 활용하여 이미지를 업로드하고, 클릭을 통해 객체를 마스킹할 수 있는 Streamlit 기반 웹 UI를 제공합니다.

## 사용 방법

1. 가상환경(venv) 생성 및 활성화

```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

2. 패키지 설치

```bash
pip install .
```

3. SAM 가중치 다운로드

아래 링크에서 SAM 가중치 파일(`sam_vit_b_01ec64.pth`)을 다운로드 받아 `sam_weights` 폴더에 넣어주세요.

- [SAM sam_vit_b_01ec64.pth 다운로드](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth)

4. 앱 실행

```bash
python SegT/app.py
```

## 폴더 구조 예시

```
root/
├── SegT
│   └── annotations
│   └── assets
│   └── sam_weights
│   └── tasks
│   ├── __init__.py
│   ├── __main__.py
│   └── app.py
├── service_account.json
├── setup.py
└── requirements.txt
```

## 참고
- SAM 공식 저장소: https://github.com/facebookresearch/segment-anything 