# 🔍 고급 백링크 분석 도구 (Advanced Backlink Analyzer)

사이트 URL을 입력하면 모든 방법을 동원해서 백링크를 분석하고 결과를 보여주는 프로그램입니다.

## ✨ 주요 기능

### 다중 방식 백링크 수집
1. **검색 엔진 크롤링** - Google, Bing의 link: 쿼리
2. **공개 백링크 체커 스크래핑** - SmallSEOTools, SEOReviewTools, BacklinksProfile
3. **Wayback Machine** - Internet Archive에서 과거 링크 정보
4. **Common Crawl** - 웹 크롤 인덱스 쿼리
5. **직접 웹 크롤링** - robots.txt 준수하면서 수집

### 분석 기능
- ✅ 백링크 수 집계
- ✅ 고유 도메인 분석
- ✅ 링크 품질 점수 평가
- ✅ 상위 참조 도메인 식별
- ✅ 복사 가능한 백링크 목록 제공

### 사용자 인터페이스
- 웹 기반 UI (FastAPI + HTML/CSS/JS)
- CLI 도구
- JSON 결과 출력

---

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
git clone https://github.com/01066865223a-hub/backlink-analyzer.git
cd backlink-analyzer

pip install -r requirements.txt
```

### 2. 웹 인터페이스 실행
```bash
python app.py
# 또는
uvicorn app:app --reload
```

접속: **http://localhost:8000**

### 3. CLI 사용
```bash
# 기본 사용
python backlink_analyzer.py example.com

# JSON 출력
python backlink_analyzer.py example.com --json
```

---

## 📊 출력 예시

```
================================================================================
백링크 분석 보고서: example.com
================================================================================

[요약]
  총 백링크: 245
  고유 도메인: 89
  평균 품질 점수: 72.5/100

[상위 10개 백링크]
  1. https://news.example.org/article-123
     점수: 85/100
  
  2. https://blog.example.com/post-456
     점수: 78/100

[상위 참조 도메인]
  1. news.example.org: 12개
  2. blog.example.com: 8개

[복사 가능한 백링크 목록]
https://news.example.org/article-123
https://blog.example.com/post-456
...
```

---

## 🎯 품질 점수 계산 기준

- **기본 점수**: 50점
- **짧은 URL** (+10점): URL 길이 < 100자
- **높은 신뢰 도메인** (+15-20점): .edu, .gov, .org
- **오래된 도메인** (+0-20점): 도메인 이름 길이 기준
- **HTTPS** (+5점): 보안 연결

**최대 점수**: 100점

---

## 📁 API 엔드포인트

### GET /
웹 인터페이스 로드

### GET /api/analyze
백링크 분석 수행

**파라미터**:
- `domain` (string): 분석할 도메인

**응답**:
```json
{
  "domain": "example.com",
  "total_backlinks": 245,
  "unique_domains": 89,
  "average_quality_score": 72.5,
  "top_backlinks": [
    {
      "url": "https://example.org/page",
      "quality_score": 85
    }
  ],
  "all_backlinks": [...]
}
```

---

## ⚙️ 고급 설정

### 환경변수
```bash
# .env 파일 생성
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_DELAY=1
```

### 커스텀 헤더
```python
analyzer.session.headers.update({
    'User-Agent': 'Custom User Agent',
    'Referer': 'https://example.com'
})
```

---

## ⚠️ 주의사항

1. **robots.txt 준수**: 크롤링 시 각 사이트의 robots.txt를 준수합니다
2. **Rate Limiting**: 과도한 요청을 방지하기 위해 요청 사이에 지연을 둡니다
3. **법적 준수**: 각 사이트의 약관을 따라야 합니다
4. **정확성**: 공개 데이터만 사용하므로 모든 백링크를 포함하지 않을 수 있습니다

---

## 📈 개선 방향

- [ ] Playwright 기반 동적 렌더링 크롤링
- [ ] DNS 레코드 분석
- [ ] WHOIS 정보 통합
- [ ] 머신러닝 기반 품질 점수
- [ ] 다국어 지원
- [ ] 일정 기반 자동 분석
- [ ] 데이터베이스 저장 기능
- [ ] 엑셀/PDF 리포트 내보내기

---

## 📝 라이선스

MIT License

---

## 🤝 기여

Pull Request를 환영합니다!

---

## 📞 지원

문제 발생 시 GitHub Issues에서 보고해주세요.
