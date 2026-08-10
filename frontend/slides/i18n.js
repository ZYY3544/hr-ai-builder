/* ═══════════════════════════════════════════════════════════
   i18n.js —— 全站多语言运行时（zh / en / ko）
   语言由文件名后缀决定：9-1.html → zh，9-1.en.html → en，9-1.ko.html → ko
   必须在 lesson.js / nav-inject.js / exam-engine.js 之前加载。
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var m = location.pathname.match(/\.(en|ko)\.html?$/);
  var LANG = m ? m[1] : 'zh';

  /* ── UI 词典 ─────────────────────────────────────────── */
  var STR = {
    zh: {
      toc: '目录',
      tocTitle: '在课程阅读器中打开，左侧带完整目录',
      askAuthor: '请教作者',
      today: '今日',
      total: '总学习',
      backHomeTitle: '返回首页 (Cmd+↑返回目录)',
      prevTitle: '上一页 (Cmd+←)',
      nextTitle: '下一页 (Cmd+→)',
      lastPage: '已是最后一页',
      navHint: '→ 下一步<br>⌘→ 换页',
      rotateTitle: '请横屏观看',
      rotateSub: '横屏后内容会按比例完整显示<br/>竖屏可关闭后继续浏览',
      rotateClose: '继续竖屏浏览',
      qrText: '扫码关注 <b>洛小山</b> 公众号，获取更多 AI 实战干货',
      close: '关闭',
      langSwitchLabel: '切换语言'
    },
    en: {
      toc: 'Contents',
      tocTitle: 'Open in the course reader with full table of contents',
      askAuthor: 'Ask the Author',
      today: 'Today',
      total: 'All-time',
      backHomeTitle: 'Back to home (Cmd+↑ for contents)',
      prevTitle: 'Previous (Cmd+←)',
      nextTitle: 'Next (Cmd+→)',
      lastPage: 'Last page',
      navHint: '→ next step<br>⌘→ turn page',
      rotateTitle: 'Please rotate to landscape',
      rotateSub: 'Content scales to fit in landscape<br/>You can dismiss this and keep browsing in portrait',
      rotateClose: 'Continue in portrait',
      qrText: 'Scan to follow <b>Luo Xiaoshan (洛小山)</b> on WeChat for more hands-on AI insights',
      close: 'Close',
      langSwitchLabel: 'Change language'
    },
    ko: {
      toc: '목차',
      tocTitle: '전체 목차가 있는 코스 리더에서 열기',
      askAuthor: '저자에게 질문',
      today: '오늘',
      total: '누적 학습',
      backHomeTitle: '홈으로 (Cmd+↑ 목차)',
      prevTitle: '이전 페이지 (Cmd+←)',
      nextTitle: '다음 페이지 (Cmd+→)',
      lastPage: '마지막 페이지입니다',
      navHint: '→ 다음 단계<br>⌘→ 페이지 넘김',
      rotateTitle: '가로 모드로 봐 주세요',
      rotateSub: '가로 모드에서 내용이 비율에 맞게 표시됩니다<br/>닫고 세로 모드로 계속 볼 수도 있습니다',
      rotateClose: '세로 모드로 계속 보기',
      qrText: 'QR 코드를 스캔해 <b>뤄샤오산(洛小山)</b> 위챗 공식 계정을 팔로우하고 AI 실전 노하우를 받아보세요',
      close: '닫기',
      langSwitchLabel: '언어 변경'
    }
  };

  /* ── 课件页导航标题（file → 译名），由翻译流程填充 ────── */
  /* @@TITLES_EN_BEGIN@@ */
  var TITLES_EN = {
'llm-story.html': 'Full Table of Contents',
  'zero-0.html': 'The Amazing Things AI Can Do',
  'zero-1.html': 'It Plays "Finish the Sentence"',
  'zero-2.html': 'It Is Not a Search Engine',
  'zero-3.html': 'It Bluffs with a Straight Face',
  'zero-4.html': 'Treat It Like a New Colleague',
  'zero-5.html': 'Magic Opener: Ask Me First',
  'zero-6.html': 'Trust It, or Verify?',
  'zero-final.html': 'Your Next Step',
  'zero-q-prompt.html': 'How to Write a Good Prompt',
  'zero-q-prompt-engineering.html': 'Why Prompt Engineering Matters',
  'zero-q-model-agent-app.html': 'Model vs Agent vs App',
  'zero-q-agent.html': 'What Makes Agents Powerful',
  'zero-q-skill.html': 'What Is a Skill, Exactly?',
  'zero-q-china-models.html': 'Chinese AI Models: How to Choose',
  'zero-q-companies.html': 'Other Major AI Companies',
  'zero-q-multimodal.html': 'Why Some AI Can\'t See Images',
  'zero-q-image-cost.html': 'Why AI Images Cost More',
  'zero-q-video-cost.html': 'Why AI Video Is Priced per Second',
  'zero-q-relay.html': 'What Are API Resellers?',
  'zero-q-reverse-proxy.html': 'What Are Shared Accounts?',
  '0-intro.html': 'Where We Are',
  '0-how.html': 'How to Learn Effectively',
  '0-why.html': 'Why Build Foundations',
  'training-data.html': 'Training Data Scale',
  'train-vs-infer.html': 'Training vs Inference',
  '1-2-vocab.html': 'Vocabulary & Training',
  '1-2-base.html': 'Base Model',
  '1-2-gpt.html': 'The GPT Breakthrough',
  '1-2-api.html': 'chat/completions Mystery',
  '1-2-fake-chat.html': 'Faking Chat History',
  '1-2-sft.html': 'Chat Template + SFT',
  '1-2-prompt-power.html': 'Context Window Is Key',
  '1-2-hallucination.html': 'LLM Hallucinations',
  '1-2-mitigation-prompt.html': 'Prompt Engineering',
  '1-2-mitigation-rag.html': 'RAG Augmented Retrieval',
  'rag-advanced.html': 'RAG Cost & Optimization',
  '1-2-mitigation-temp.html': 'Temperature & Top-P',
  '1-2-mitigation-eval.html': 'Evaluation + Human Review',
  'summary-1.html': 'Part 1 Recap (A)',
  'summary-1b.html': 'Part 1 Recap (B)',
  'interview-1.html': 'Quiz · 7 Questions',
  '5-1.html': 'Context Window',
  '5-2.html': 'Context Overflow Strategies',
  '6-0a.html': 'Why Markdown',
  '6-0b.html': 'MD Syntax & Rendering',
  '6-1.html': 'Prompt Role-Play',
  '6-2.html': 'Advanced Prompt Techniques',
  '6-3.html': 'Output Format Trade-offs',
  '6-4.html': 'Streaming & Formatting',
  'prompt-attack.html': 'Prompt Injection Explained',
  'prompt-attack-cases.html': '12 Attack Cases',
  'prompt-defense.html': 'Prompt Defense in Practice',
  '7-1.html': 'Agent Concepts',
  '7-2.html': 'Tool Calling',
  '7-2a.html': '5 Messages Behind a Chat',
  '7-2b.html': 'Art of Tool Descriptions',
  '7-2c.html': 'Multi-Tool Orchestration',
  '7-2d.html': 'MCP Protocol',
  '7-3.html': 'ReAct in Practice',
  '7-3a.html': 'Context Window',
  '7-3b.html': 'Context Compression 4 Layers',
  '7-3c.html': 'Long-Term Memory',
  '7-4a.html': 'ReAct Loop',
  '7-4b.html': '5 Agent Deadlock Patterns',
  '7-4c.html': 'Permissions & Security',
  '7-5.html': 'Skill',
  '7-5a.html': 'Essence of Skill',
  '7-5b.html': 'Dissecting a Real Skill',
  '7-4.html': 'Scaffolding Engineering',
  '7-6a.html': '5 Engineering Guardrails',
  '7-6b.html': 'Multi-Agent Collaboration',
  '7-6c.html': 'Observability',
  '7-summary.html': 'Agent Engineering Overview',
  '8-1.html': 'Multi-Turn Cost',
  '8-2.html': 'KV Cache',
  '8-2b.html': 'Explicit Caching',
  '8-3.html': 'Dynamic Timestamps',
  '8-4.html': 'Cost Optimization',
  '8-5.html': 'Image Token Billing',
  '8-5b.html': 'Match Resolution to Task',
  '8-6.html': 'Syntax-Layer Optimization',
  '8-7.html': 'Semantic-Layer Optimization',
  '8-8.html': 'Output Layer + KV Advanced',
  'cost-eval.html': 'Model Selection: Cap vs Cost',
  'engineering-philosophy.html': 'Simplicity First',
  'summary-2.html': 'Part 2 Recap (A)',
  'summary-2b.html': 'Part 2 Recap (B)',
  'ai-tips-boundary.html': 'Human-AI Boundary',
  'ai-tips-context.html': 'Good vs Bad Questions',
  'ai-tips-verify.html': 'Can You Trust AI?',
  'ai-tips-iterate.html': 'Art of Iteration',
  'ai-tips-scenarios.html': 'Scenario Cheat Sheet',
  'summary-final.html': 'Course Summary',
  'summary-final-1.html': 'Summary (A)',
  'summary-final-2.html': 'Summary (B)',
  'interview-2.html': 'Quiz · 7 Questions',
  '9-1.html': 'Text-to-Image vs Img-to-Img',
  '9-2.html': 'AI Writes Prompts for AI',
  '9-3.html': 'Character Consistency',
  '9-4.html': 'Models Go Down, Then What',
  '9-5.html': 'Image Gen Checklist',
  '9-6.html': 'Textbook vs Real N Steps',
  '9-7.html': 'Why Agents Get Stuck',
  '9-8.html': 'Fool-Proof Design',
  '9-9.html': 'Streaming UX',
  '9-10.html': 'True Cost of One Message',
  '9-11.html': 'Longer = Costlier + Dumber',
  '9-12.html': 'Art of Compression',
  '9-13.html': 'Can User Words Be Deleted?',
  '9-14.html': 'Local vs LLM Compression',
  '9-15.html': 'Context ≠ Memory',
  '9-16.html': 'What\'s Worth Remembering',
  '9-17.html': 'Memory Conflicts',
  '9-18.html': 'Cost of Memory Injection',
  '9-19.html': 'System Prompt Layering',
  '9-20.html': 'On-Demand Loading',
  '9-21.html': 'Skill Modularization',
  '9-22.html': 'Prompts & Cache Interplay',
  '9-23.html': 'When Multi-Agent',
  '9-24.html': 'Price of Concurrency',
  '9-25.html': 'Brainstorm Mode',
  '9-26.html': 'Scheduled Task Cost',
  '9-27.html': 'AI\'s Degree of Freedom',
  '9-28.html': 'Popups vs Safety Balance',
  '9-29.html': 'Observability',
  '9-30.html': 'MCP Bidirectional Protocol',
  '9-31.html': 'Lazy Connections',
  '9-32.html': 'AI Adds Its Own Tools',
  '9-summary.html': 'Practice Overview',
  '9-final.html': 'Chat Wrapper vs Agent',
  'interview-3.html': 'Quiz · 7 Questions',
  '10-1.html': 'Workflow vs Agent',
  '10-2.html': 'Five Workflow Patterns',
  '10-3.html': 'Context Engineering',
  '10-4.html': 'Three Context Tactics',
  '10-5.html': 'ACI Tool Interface Design',
  '10-6.html': 'Think Tool',
  '10-7.html': 'Agent Optimizes Tools',
  '10-8.html': 'Evaluation Methodology',
  '10-9.html': 'Three Graders',
  '10-10.html': 'Eval Pitfalls',
  '10-11.html': 'Long-Task Failures',
  '10-12.html': 'Dual-Role Harness',
  '10-13.html': 'Managed Agent',
  '10-14.html': 'Session vs Context',
  '10-15.html': 'Three Security Risks',
  '10-16.html': 'Sandbox & Credential Isolation',
  '10-17.html': 'Contextual Retrieval',
  '10-summary.html': 'Advanced Overview',
  '10-final.html': 'Do the Simplest Thing',
  'interview-4.html': 'Quiz · 7 Questions',
  '11-1.html': 'Scaffolding to Self-Improvement',
  '11-2.html': '3 Harness Design Patterns',
  '11-3.html': 'Context Auto-Evolution',
  '11-4.html': 'Workflow Auto-Search',
  '11-5.html': 'Harness Improves Itself',
  '11-6.html': 'Evolutionary Search',
  '11-7.html': 'Future: Seven Barriers',
  'interview-5.html': 'Quiz · 6 Questions',
  'exam.html': 'Test Center',
  'exam-1.html': 'Part 1 Test · 50 Questions',
  'exam-2.html': 'Part 2 Test · 50 Questions',
  'exam-3.html': 'Part 3 Test · 50 Questions',
  'exam-4.html': 'Part 4 Test · 50 Questions',
  'exam-5.html': 'Part 5 Test · 50 Questions',
  'exam-6.html': 'Part 6 Test · 50 Questions',
  'exam-7.html': 'Part 7 Test · 50 Questions',
  'exam-all.html': 'Comprehensive · 35 Questions',
  'oss-1.html': 'What Are Weights',
  'oss-2.html': 'Real vs. Fake Open Source',
  'oss-3.html': 'Open Source Is a Business',
  'oss-4.html': 'Emergence',
  'oss-5.html': 'Why Make Models Smaller',
  'oss-6.html': 'How Distillation Works',
  'oss-7.html': 'The Cost of Distillation',
  'oss-8.html': 'What Your Computer Can Run',
  'oss-9.html': 'Ollama and LM Studio'
  };
  /* @@TITLES_EN_END@@ */

  /* @@TITLES_KO_BEGIN@@ */
  var TITLES_KO = {
'llm-story.html': '전체 목차',
  'zero-0.html': 'AI가 해내는 신기한 일들',
  'zero-1.html': 'AI는 「말 잇기」를 한다',
  'zero-2.html': '검색 엔진이 아니다',
  'zero-3.html': '천연덕스럽게 지어낸다',
  'zero-4.html': '나를 모르는 새 동료처럼',
  'zero-5.html': '만능 오프닝: 먼저 물어봐 줘',
  'zero-6.html': '믿을까, 확인할까?',
  'zero-final.html': '다음 단계',
  'zero-q-prompt.html': '좋은 프롬프트 쓰는 법',
  'zero-q-prompt-engineering.html': '프롬프트 엔지니어링의 의미',
  'zero-q-model-agent-app.html': '모델 vs 에이전트 vs 앱',
  'zero-q-agent.html': '에이전트는 왜 강력한가',
  'zero-q-skill.html': '요즘 화제인 Skill이란?',
  'zero-q-china-models.html': '중국 AI 모델 고르는 법',
  'zero-q-companies.html': '주요 AI 기업들',
  'zero-q-multimodal.html': '이미지를 못 보는 AI가 있는 이유',
  'zero-q-image-cost.html': 'AI 이미지가 비싼 이유',
  'zero-q-video-cost.html': 'AI 영상이 초당 과금인 이유',
  'zero-q-relay.html': 'API 중계 판매란?',
  'zero-q-reverse-proxy.html': '공유 계정이란?',
  '0-intro.html': '우리는 어디에 있는가',
  '0-how.html': '효과적으로 배우는 법',
  '0-why.html': '왜 기초를 다져야 하나',
  'training-data.html': '훈련 데이터 규모',
  'train-vs-infer.html': '훈련 vs 추론',
  '1-2-vocab.html': '어휘와 훈련',
  '1-2-base.html': 'Base 모델',
  '1-2-gpt.html': 'GPT의 도약',
  '1-2-api.html': 'chat/completions의 비밀',
  '1-2-fake-chat.html': '가짜 채팅 기록',
  '1-2-sft.html': 'Chat Template + SFT',
  '1-2-prompt-power.html': '컨텍스트 윈도우가 핵심',
  '1-2-hallucination.html': '대규모 모델 환각',
  '1-2-mitigation-prompt.html': 'Prompt Engineering',
  '1-2-mitigation-rag.html': 'RAG 검색 증강',
  'rag-advanced.html': 'RAG 비용과 최적화',
  '1-2-mitigation-temp.html': 'Temperature & Top-P',
  '1-2-mitigation-eval.html': '평가 + 수동 검토',
  'summary-1.html': '1부 요약(상)',
  'summary-1b.html': '1부 요약(하)',
  'interview-1.html': '이렇게 물어본다 · 7문',
  '5-1.html': '컨텍스트 윈도우',
  '5-2.html': '컨텍스트 오버플로 전략',
  '6-0a.html': '왜 Markdown인가',
  '6-0b.html': 'MD 문법과 렌더링',
  '6-1.html': 'Prompt 역할극',
  '6-2.html': 'Prompt 심화 기법',
  '6-3.html': '출력 포맷 트레이드오프',
  '6-4.html': '스트리밍 반환과 포맷',
  'prompt-attack.html': 'Prompt 인젝션 원리',
  'prompt-attack-cases.html': '12가지 공격 사례',
  'prompt-defense.html': 'Prompt 방어 실전',
  '7-1.html': 'Agent 개념',
  '7-2.html': '도구 호출',
  '7-2a.html': '한 대화 뒤의 5개 메시지',
  '7-2b.html': '도구 설명의 학문',
  '7-2c.html': '다중 도구 오케스트레이션',
  '7-2d.html': 'MCP 프로토콜',
  '7-3.html': 'ReAct 실전',
  '7-3a.html': '컨텍스트 윈도우',
  '7-3b.html': '컨텍스트 압축 4단계',
  '7-3c.html': '장기 기억',
  '7-4a.html': 'ReAct 루프',
  '7-4b.html': 'Agent 멈춤 5패턴',
  '7-4c.html': '권한과 보안',
  '7-5.html': 'Skill 기능',
  '7-5a.html': 'Skill의 본질',
  '7-5b.html': '실제 Skill 해부',
  '7-4.html': '스캐폴딩 엔지니어링',
  '7-6a.html': '5가지 엔지니어링 가드레일',
  '7-6b.html': '다중 Agent 협업',
  '7-6c.html': '관측 가능성',
  '7-summary.html': 'Agent 엔지니어링 전경도',
  '8-1.html': '멀티턴 대화 비용',
  '8-2.html': 'KV Cache',
  '8-2b.html': '명시적 캐시',
  '8-3.html': '동적 타임스탬프',
  '8-4.html': '종합 비용 최적화',
  '8-5.html': '이미지 Token 과금',
  '8-5b.html': '태스크별 해상도 매칭',
  '8-6.html': '구문 계층 최적화',
  '8-7.html': '의미 계층 최적화',
  '8-8.html': '출력 계층+KV 심화',
  'cost-eval.html': '모델 선택: 능력 vs 비용',
  'engineering-philosophy.html': '대도지간',
  'summary-2.html': '2부 요약(상)',
  'summary-2b.html': '2부 요약(하)',
  'ai-tips-boundary.html': '인간-AI 지식 경계',
  'ai-tips-context.html': '좋은 질문 vs 나쁜 질문',
  'ai-tips-verify.html': 'AI 말을 믿어도 되나',
  'ai-tips-iterate.html': '반복의 기술',
  'ai-tips-scenarios.html': '시나리오 속성 참조',
  'summary-final.html': '과정 총정리',
  'summary-final-1.html': '총정리(상)',
  'summary-final-2.html': '총정리(하)',
  'interview-2.html': '이렇게 물어본다 · 7문',
  '9-1.html': '텍스트-투-이미지 vs 참조 이미지',
  '9-2.html': 'AI에게 AI용 Prompt 쓰기',
  '9-3.html': '캐릭터 일관성',
  '9-4.html': '모델 다운 시 대응',
  '9-5.html': '이미지 생성 제품화 체크리스트',
  '9-6.html': '교과서 vs 실제 N단계',
  '9-7.html': 'Agent가 왜 멈추나',
  '9-8.html': '바보 방지 설계',
  '9-9.html': '스트리밍 경험',
  '9-10.html': '한 메시지의 실제 비용',
  '9-11.html': '길수록 비싸고 멍청해진다',
  '9-12.html': '압축의 기술',
  '9-13.html': '사용자의 말을 삭제해도 되나',
  '9-14.html': '로컬 vs LLM 압축',
  '9-15.html': '컨텍스트 ≠ 기억',
  '9-16.html': '무엇을 기억할 것인가',
  '9-17.html': '기억 충돌',
  '9-18.html': '기억 주입의 비용',
  '9-19.html': 'System Prompt 계층화',
  '9-20.html': '온디맨드 로딩',
  '9-21.html': 'Skill 모듈화',
  '9-22.html': '프롬프트와 캐시',
  '9-23.html': '언제 다중 Agent가 필요한가',
  '9-24.html': '동시성의 대가',
  '9-25.html': '브레인스토밍 모드',
  '9-26.html': '예약 작업 비용',
  '9-27.html': 'AI의 자유도',
  '9-28.html': '팝업과 보안 밸런스',
  '9-29.html': '관측 가능성',
  '9-30.html': 'MCP 양방향 프로토콜',
  '9-31.html': '지연 연결',
  '9-32.html': 'AI 자가 도구 추가',
  '9-summary.html': '실전 전경도',
  '9-final.html': '채팅 래퍼 vs Agent 제품',
  'interview-3.html': '이렇게 물어본다 · 7문',
  '10-1.html': 'Workflow vs Agent',
  '10-2.html': '5가지 Workflow 패턴',
  '10-3.html': '컨텍스트 엔지니어링 방법론',
  '10-4.html': '컨텍스트 세 가지 무기',
  '10-5.html': 'ACI 도구 인터페이스 설계',
  '10-6.html': 'Think Tool',
  '10-7.html': 'Agent로 도구 최적화',
  '10-8.html': '평가 방법론',
  '10-9.html': '3가지 Grader',
  '10-10.html': '평가의 함정',
  '10-11.html': '장시간 작업 실패 패턴',
  '10-12.html': '이중 역할 Harness',
  '10-13.html': 'Managed Agent',
  '10-14.html': 'Session vs Context',
  '10-15.html': '3가지 보안 리스크',
  '10-16.html': '샌드박스와 자격증명 격리',
  '10-17.html': 'Contextual Retrieval',
  '10-summary.html': '심화 전경도',
  '10-final.html': 'Do the simplest thing',
  'interview-4.html': '이렇게 물어본다 · 7문',
  '11-1.html': '스캐폴딩에서 자기 개선으로',
  '11-2.html': 'Harness 3대 설계 패턴',
  '11-3.html': '컨텍스트 자동 진화',
  '11-4.html': '워크플로 자동 탐색',
  '11-5.html': 'Harness가 스스로를 개선',
  '11-6.html': '진화 탐색',
  '11-7.html': '미래 도전 7가지 관문',
  'interview-5.html': '이렇게 물어본다 · 6문',
  'exam.html': '자가 테스트 센터',
  'exam-1.html': '1부 테스트 · 50문제',
  'exam-2.html': '2부 테스트 · 50문제',
  'exam-3.html': '3부 테스트 · 50문제',
  'exam-4.html': '4부 테스트 · 50문제',
  'exam-5.html': '5부 테스트 · 50문제',
  'exam-6.html': '6부 테스트 · 50문제',
  'exam-7.html': '7부 테스트 · 50문제',
  'exam-all.html': '전체 종합시험 · 35문제',
  'oss-1.html': '가중치란 무엇인가',
  'oss-2.html': '진짜 vs 가짜 오픈소스',
  'oss-3.html': '오픈소스는 하나의 사업이다',
  'oss-4.html': '창발',
  'oss-5.html': '모델을 왜 작게 만드는가',
  'oss-6.html': '증류는 어떻게 하는가',
  'oss-7.html': '증류의 대가',
  'oss-8.html': '내 컴퓨터가 돌릴 수 있는 모델',
  'oss-9.html': 'Ollama와 LM Studio'
  };
  /* @@TITLES_KO_END@@ */

  var TITLES = { en: TITLES_EN, ko: TITLES_KO };

  /* ── 工具函数 ────────────────────────────────────────── */
  function baseFile(file) {
    return String(file || '').replace(/\.(en|ko)\.html$/, '.html');
  }
  function locFile(file, lang) {
    lang = lang || LANG;
    var base = baseFile(file);
    if (lang === 'zh') return base;
    return base.replace(/\.html$/, '.' + lang + '.html');
  }

  window.XUEAI_I18N = {
    lang: LANG,
    t: function (key) {
      return (STR[LANG] && STR[LANG][key]) || STR.zh[key] || key;
    },
    baseFile: baseFile,
    locFile: locFile,
    slideTitle: function (file, zhTitle) {
      if (LANG === 'zh') return zhTitle;
      var map = TITLES[LANG];
      return (map && map[baseFile(file)]) || zhTitle;
    }
  };

  /* ── 语言切换器（iframe 嵌入模式不渲染） ─────────────── */
  var EMBED = (function () {
    try {
      if (/[?&]embed=1\b/.test(location.search)) return true;
      if (window.self !== window.top) return true;
    } catch (e) { return true; }
    return false;
  })();
  if (EMBED) return;

  function injectSwitcher() {
    if (document.getElementById('lang-switcher')) return;
    /* 页面自带语言切换 UI 时，声明 data-no-floating-switcher 可禁用浮动切换器 */
    if (document.documentElement.hasAttribute('data-no-floating-switcher')) return;
    var cur = location.pathname.split('/').pop() || 'home.html';
    if (!/\.html?$/.test(cur)) cur = 'home.html';

    var style = document.createElement('style');
    style.textContent = [
      '#lang-switcher{position:fixed;top:14px;right:14px;z-index:10000;',
      'font-family:-apple-system,"PingFang SC","Apple SD Gothic Neo",sans-serif;}',
      '#lang-switcher .ls-btn{display:flex;align-items:center;gap:5px;height:32px;padding:0 10px;',
      'background:rgba(255,255,255,0.85);backdrop-filter:blur(16px);border:1px solid rgba(0,0,0,0.08);',
      'border-radius:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08);cursor:pointer;',
      'font-family:inherit;font-size:12px;font-weight:700;color:#6b6b70;white-space:nowrap;',
      'transition:color .15s;}',
      '#lang-switcher .ls-btn:hover{color:#0066ff;}',
      '#lang-switcher .ls-globe{width:15px;height:15px;flex-shrink:0;}',
      '#lang-switcher .ls-caret{width:10px;height:10px;flex-shrink:0;opacity:.55;transition:transform .2s;}',
      '#lang-switcher.open .ls-caret{transform:rotate(180deg);}',
      '#lang-switcher .ls-menu{position:absolute;top:38px;right:0;min-width:126px;display:none;',
      'background:rgba(255,255,255,0.96);backdrop-filter:blur(16px);border:1px solid rgba(0,0,0,0.08);',
      'border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,0.12);padding:4px;}',
      '#lang-switcher.open .ls-menu{display:block;}',
      '#lang-switcher .ls-menu a{display:block;padding:7px 11px;border-radius:8px;',
      'font-size:12px;font-weight:700;color:#6b6b70;text-decoration:none;white-space:nowrap;',
      'transition:background .15s,color .15s;}',
      '#lang-switcher .ls-menu a:hover{background:rgba(0,102,255,0.06);color:#0066ff;}',
      '#lang-switcher .ls-menu a.active{background:#0066ff;color:#fff;pointer-events:none;}',
      '@media (max-width:768px){#lang-switcher{top:8px;right:8px;}}'
    ].join('');
    document.head.appendChild(style);

    var langs = [
      { id: 'zh', label: '中文' },
      { id: 'en', label: 'English' },
      { id: 'ko', label: '한국어' }
    ];

    var box = document.createElement('div');
    box.id = 'lang-switcher';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ls-btn';
    btn.setAttribute('aria-haspopup', 'true');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', (STR[LANG] || STR.zh).langSwitchLabel);
    btn.innerHTML = '<svg class="ls-globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
      + '<span></span>'
      + '<svg class="ls-caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';
    /* 按钮固定显示 Language：当前语种在菜单里高亮即可，
       按钮位置写当前语言反而像是「点了会切到这个语言」 */
    btn.querySelector('span').textContent = 'Language';
    box.appendChild(btn);

    var menu = document.createElement('div');
    menu.className = 'ls-menu';
    langs.forEach(function (l) {
      var a = document.createElement('a');
      a.textContent = l.label;
      a.setAttribute('lang', l.id === 'zh' ? 'zh-CN' : l.id);
      if (l.id === LANG) {
        a.className = 'active';
        a.href = 'javascript:void(0)';
      } else {
        a.href = locFile(cur, l.id) + location.hash;
        a.addEventListener('click', function () {
          try { localStorage.setItem('xueai_lang', l.id); } catch (e) {}
        });
      }
      menu.appendChild(a);
    });
    box.appendChild(menu);

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = box.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function () {
      box.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        box.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    document.body.appendChild(box);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSwitcher);
  } else {
    injectSwitcher();
  }
})();
