# tokencrush: LLM 토큰 최적화 CLI 도구

## TL;DR

> **Quick Summary**: LLMLingua-2를 활용한 프롬프트 압축 + LiteLLM 기반 멀티 프로바이더 지원 CLI 도구 개발. 사용자가 API 키만 설정하면 토큰 압축을 통해 LLM API 비용을 50-80% 절감.
> 
> **Deliverables**:
> - `tokencrush compress` - 프롬프트 압축 명령어
> - `tokencrush chat` - 압축 + API 호출 통합 명령어  
> - `tokencrush config` - API 키 설정/관리
> - PyPI 패키지 (`pip install tokencrush`)
> 
> **Estimated Effort**: Medium (3-5 days)
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 6 → Task 8

---

## Context

### Original Request
LLM API 토큰 비용을 절감하는 CLI 도구 개발. API 키 입력 후 프롬프트를 자동 압축하여 "거의 무제한 사용" 느낌을 제공. GPT, Gemini, Claude 등 주요 모델 지원, 향후 100+ LLM 확장 목표. MIT 오픈소스.

### Interview Summary
**Key Discussions**:
- **패키지 매니저**: uv 선택 (현대적, 빠름)
- **MVP 범위**: compress, chat, config 3개 핵심 명령어만 (stats, 파이프, 캐싱은 2차)
- **테스트 전략**: TDD + pytest
- **GPU 지원**: CPU 기본, `--gpu` 플래그로 선택적 활성화
- **코드 주석 언어**: 영어 only (docstrings, comments 모두)

**Research Findings**:
- **LLMLingua-2** (Microsoft): 2-5x 압축률, task-agnostic, LangChain/LlamaIndex 통합 지원
- **LiteLLM**: 100+ LLM 프로바이더 지원, OpenAI 호환 인터페이스
- **Typer**: 현대적 Python CLI, 자동 --help, 타입 힌트 기반

### Gap Analysis (Self-Review)
**Identified Gaps** (addressed):
- API 키 저장 방식 미명시 → 환경변수 우선, `~/.config/tokencrush/config.toml` 백업
- 에러 핸들링 전략 미명시 → 압축 실패 시 원본 전송 + 경고 출력
- CLI 출력 형식 미명시 → Rich 라이브러리로 컬러풀한 출력
- 압축률 기본값 미명시 → rate=0.5 (50% 압축) 기본값

**Additional Requirements** (added):
- 모든 코드 주석은 영어로 작성 (docstrings, inline comments 포함)

---

## Work Objectives

### Core Objective
프롬프트 압축을 통해 LLM API 토큰 비용을 절감하는 간편한 CLI 도구 개발

### Concrete Deliverables
- `/Users/jnnj92/projects/tokencrush/` 프로젝트 구조
- `src/tokencrush/cli.py` - Typer CLI 엔트리포인트
- `src/tokencrush/compressor.py` - LLMLingua-2 래퍼
- `src/tokencrush/providers.py` - LiteLLM 래퍼
- `src/tokencrush/config.py` - API 키/설정 관리
- `pyproject.toml` - uv 패키지 설정
- `tests/` - pytest 테스트 스위트
- `README.md` - 사용법 문서

### Definition of Done
- [ ] `tokencrush compress "긴 텍스트"` → 압축된 텍스트 출력
- [ ] `tokencrush chat "질문" --model gpt-4` → 압축 후 API 호출, 응답 출력
- [ ] `tokencrush config set openai sk-xxx` → API 키 저장
- [ ] `pytest` → 모든 테스트 통과
- [ ] `pip install .` → 로컬 설치 성공

### Must Have
- LLMLingua-2 기반 프롬프트 압축 (2-5x)
- GPT, Claude, Gemini 3대 프로바이더 지원
- API 키 안전 저장 (~/.config/tokencrush/)
- CPU 기본 동작 (GPU 없어도 사용 가능)
- 압축 전/후 토큰 수 표시
- **모든 코드 주석은 영어로 작성** (docstrings, inline comments 포함)

### Must NOT Have (Guardrails)
- 자체 LLM 모델 훈련/호스팅 금지 (기존 라이브러리만 사용)
- API 키를 코드나 로그에 노출 금지
- 과도한 추상화 금지 (단순한 래퍼 유지)
- MVP 범위 외 기능 (stats, 파이프, 캐싱) 구현 금지
- 복잡한 설정 시스템 금지 (최소한의 config만)
- 불필요한 의존성 추가 금지
- **한국어/비영어 코드 주석 금지** (모든 주석, docstrings는 영어로)

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (새 프로젝트)
- **User wants tests**: TDD
- **Framework**: pytest

### TDD Workflow

각 TODO는 RED-GREEN-REFACTOR 패턴을 따름:

**Task Structure:**
1. **RED**: 실패하는 테스트 먼저 작성
   - Test file: `tests/test_*.py`
   - Test command: `uv run pytest tests/test_*.py -v`
   - Expected: FAIL (테스트 존재, 구현 없음)
2. **GREEN**: 테스트 통과하는 최소 구현
   - Command: `uv run pytest tests/test_*.py -v`
   - Expected: PASS
3. **REFACTOR**: 테스트 통과 유지하며 정리
   - Command: `uv run pytest -v`
   - Expected: PASS (전체)

### Test Setup Task
- [ ] 0. pytest 설정 및 첫 테스트 작성
  - Config: `pyproject.toml`에 pytest 설정 추가
  - Verify: `uv run pytest --help` → 도움말 출력
  - Example: `tests/test_example.py` 생성
  - Verify: `uv run pytest` → 1 test passes

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: 프로젝트 초기화 (uv, pyproject.toml)
└── (독립 작업 없음 - 순차 진행)

Wave 2 (After Task 2 - Test Setup):
├── Task 3: Compressor 모듈 (TDD)
├── Task 4: Config 모듈 (TDD)
└── Task 5: Providers 모듈 (TDD)

Wave 3 (After Wave 2):
├── Task 6: CLI 통합 (compress, chat, config)
└── Task 7: 통합 테스트

Wave 4 (Final):
└── Task 8: README 및 패키지 마무리
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2 | None |
| 2 | 1 | 3, 4, 5 | None |
| 3 | 2 | 6 | 4, 5 |
| 4 | 2 | 6 | 3, 5 |
| 5 | 2 | 6 | 3, 4 |
| 6 | 3, 4, 5 | 7 | None |
| 7 | 6 | 8 | None |
| 8 | 7 | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2 | Sequential - 프로젝트 셋업 |
| 2 | 3, 4, 5 | `run_in_background=true` 병렬 실행 |
| 3 | 6, 7 | Sequential - CLI 통합 |
| 4 | 8 | Single task - 마무리 |

---

## TODOs

### Task 1: 프로젝트 초기화

- [ ] 1. 프로젝트 디렉토리 및 uv 환경 설정

  **What to do**:
  - `~/projects/tokencrush/` 디렉토리 생성
  - `uv init` 으로 프로젝트 초기화
  - `pyproject.toml` 설정 (name, version, dependencies, scripts)
  - `src/tokencrush/` 패키지 구조 생성
  - 의존성 설치: `llmlingua`, `litellm`, `typer`, `rich`

  **Must NOT do**:
  - 복잡한 빌드 시스템 설정 금지
  - 불필요한 디렉토리 생성 금지

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순한 프로젝트 셋업 작업, 복잡한 로직 없음
  - **Skills**: [`git-master`]
    - `git-master`: git init 및 초기 커밋에 필요
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: CLI 프로젝트, 프론트엔드 없음

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (첫 번째 작업)
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  
  **External References**:
  - uv 공식 문서: https://docs.astral.sh/uv/
  - pyproject.toml 스펙: https://packaging.python.org/en/latest/specifications/pyproject-toml/

  **예상 구조**:
  ```
  ~/projects/tokencrush/
  ├── pyproject.toml
  ├── README.md
  ├── src/
  │   └── tokencrush/
  │       ├── __init__.py
  │       ├── cli.py
  │       ├── compressor.py
  │       ├── providers.py
  │       └── config.py
  └── tests/
      └── __init__.py
  ```

  **Acceptance Criteria**:
  
  **TDD - RED phase**: N/A (셋업 작업)
  
  **Manual Execution Verification**:
  - [ ] `cd ~/projects/tokencrush && ls -la` → 프로젝트 디렉토리 존재
  - [ ] `uv run python -c "import tokencrush"` → ImportError 없음
  - [ ] `cat pyproject.toml` → name = "tokencrush" 확인

  **Commit**: YES
  - Message: `chore: initialize tokencrush project with uv`
  - Files: `pyproject.toml`, `src/tokencrush/__init__.py`, `README.md`
  - Pre-commit: N/A

---

### Task 2: 테스트 인프라 설정

- [ ] 2. pytest 설정 및 테스트 구조 생성

  **What to do**:
  - `pyproject.toml`에 pytest 설정 추가
  - `tests/conftest.py` 생성 (공통 fixtures)
  - `tests/test_example.py` 생성 (셋업 검증)
  - pytest-mock, pytest-asyncio 의존성 추가

  **Must NOT do**:
  - 복잡한 테스트 설정 금지
  - 실제 API 호출하는 테스트 금지 (mock 사용)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 간단한 테스트 설정 작업
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `git-master`: 단순 파일 생성, git 작업 최소화

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Tasks 3, 4, 5
  - **Blocked By**: Task 1

  **References**:
  
  **External References**:
  - pytest 공식 문서: https://docs.pytest.org/
  - pytest-mock: https://pytest-mock.readthedocs.io/

  **Acceptance Criteria**:
  
  **Manual Execution Verification**:
  - [ ] `uv run pytest --help` → pytest 도움말 출력
  - [ ] `uv run pytest tests/ -v` → 1 passed (example test)
  - [ ] `cat tests/conftest.py` → fixtures 정의 확인

  **Commit**: YES
  - Message: `test: add pytest infrastructure`
  - Files: `pyproject.toml`, `tests/conftest.py`, `tests/test_example.py`
  - Pre-commit: `uv run pytest`

---

### Task 3: Compressor 모듈 (TDD)

- [ ] 3. LLMLingua-2 기반 프롬프트 압축 모듈 구현

  **What to do**:
  - `tests/test_compressor.py` 작성 (RED)
  - `src/tokencrush/compressor.py` 구현 (GREEN)
  - 클래스: `TokenCompressor`
  - 메서드: `compress(text, rate=0.5) -> CompressResult`
  - 반환값: `CompressResult(original_tokens, compressed_tokens, compressed_text, ratio)`
  - GPU 선택적 지원: `use_gpu=False` 기본값

  **Must NOT do**:
  - LLMLingua 내부 수정 금지
  - 과도한 추상화 금지 (단순 래퍼)
  - 실제 모델 로드 없이 mock으로 테스트
  - 한국어/비영어 주석 금지 (모든 docstrings, comments는 영어로)

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: 외부 라이브러리 통합, API 이해 필요
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: 백엔드 로직

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 2

  **References**:
  
  **External References**:
  - LLMLingua-2 사용법: https://github.com/microsoft/LLMLingua
  - 코드 예시:
    ```python
    from llmlingua import PromptCompressor
    llm_lingua = PromptCompressor(
        model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
        use_llmlingua2=True,
        device_map="cpu"  # or "cuda"
    )
    result = llm_lingua.compress_prompt(prompt, rate=0.5)
    # result: {"compressed_prompt": str, "origin_tokens": int, "compressed_tokens": int, ...}
    ```

  **Acceptance Criteria**:
  
  **TDD - RED phase**:
  - [ ] `tests/test_compressor.py` 생성
  - [ ] 테스트 케이스: compress 기본 동작, rate 파라미터, GPU 플래그
  - [ ] `uv run pytest tests/test_compressor.py -v` → FAIL

  **TDD - GREEN phase**:
  - [ ] `src/tokencrush/compressor.py` 구현
  - [ ] `uv run pytest tests/test_compressor.py -v` → PASS

  **Manual Execution Verification**:
  - [ ] `uv run python -c "from tokencrush.compressor import TokenCompressor; print(TokenCompressor)"` → 클래스 출력

  **Commit**: YES
  - Message: `feat(compressor): add LLMLingua-2 based prompt compression`
  - Files: `src/tokencrush/compressor.py`, `tests/test_compressor.py`
  - Pre-commit: `uv run pytest tests/test_compressor.py`

---

### Task 4: Config 모듈 (TDD)

- [ ] 4. API 키 설정 및 관리 모듈 구현

  **What to do**:
  - `tests/test_config.py` 작성 (RED)
  - `src/tokencrush/config.py` 구현 (GREEN)
  - 클래스: `ConfigManager`
  - 기능:
    - API 키 저장: `~/.config/tokencrush/config.toml`
    - 환경변수 우선 읽기 (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY)
    - 키 마스킹 출력 (sk-xxx...xxx)
  - TOML 파싱: `tomllib` (Python 3.11+) 또는 `tomli`

  **Must NOT do**:
  - API 키 평문 로깅 금지
  - 복잡한 설정 구조 금지 (단순 key-value)
  - 암호화 구현 금지 (MVP 범위 외)
  - 한국어/비영어 주석 금지 (모든 docstrings, comments는 영어로)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순한 파일 I/O 및 환경변수 처리
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `git-master`: 단순 구현 작업

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 2

  **References**:
  
  **External References**:
  - Python tomllib: https://docs.python.org/3/library/tomllib.html
  - XDG Base Directory: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

  **예상 config.toml 구조**:
  ```toml
  [api_keys]
  openai = "sk-..."
  anthropic = "sk-ant-..."
  google = "AIza..."
  
  [defaults]
  model = "gpt-4"
  compression_rate = 0.5
  ```

  **Acceptance Criteria**:
  
  **TDD - RED phase**:
  - [ ] `tests/test_config.py` 생성
  - [ ] 테스트 케이스: 키 저장, 키 로드, 환경변수 우선, 마스킹
  - [ ] `uv run pytest tests/test_config.py -v` → FAIL

  **TDD - GREEN phase**:
  - [ ] `src/tokencrush/config.py` 구현
  - [ ] `uv run pytest tests/test_config.py -v` → PASS

  **Manual Execution Verification**:
  - [ ] `uv run python -c "from tokencrush.config import ConfigManager; cm = ConfigManager(); print(cm)"` → 객체 출력

  **Commit**: YES
  - Message: `feat(config): add API key management with TOML storage`
  - Files: `src/tokencrush/config.py`, `tests/test_config.py`
  - Pre-commit: `uv run pytest tests/test_config.py`

---

### Task 5: Providers 모듈 (TDD)

- [ ] 5. LiteLLM 기반 멀티 프로바이더 래퍼 구현

  **What to do**:
  - `tests/test_providers.py` 작성 (RED)
  - `src/tokencrush/providers.py` 구현 (GREEN)
  - 클래스: `LLMProvider`
  - 메서드: `chat(prompt, model="gpt-4") -> str`
  - 지원 모델 매핑:
    - `gpt-4`, `gpt-3.5-turbo` → OpenAI
    - `claude-3-sonnet`, `claude-3-opus` → Anthropic
    - `gemini-1.5-pro`, `gemini-1.5-flash` → Google
  - API 키는 ConfigManager에서 주입

  **Must NOT do**:
  - LiteLLM 내부 수정 금지
  - 스트리밍 구현 금지 (MVP 범위 외)
  - 직접 HTTP 호출 금지 (LiteLLM 사용)
  - 한국어/비영어 주석 금지 (모든 docstrings, comments는 영어로)

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: 외부 API 통합, 에러 핸들링 복잡성
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: 백엔드 로직

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 4)
  - **Blocks**: Task 6
  - **Blocked By**: Task 2

  **References**:
  
  **External References**:
  - LiteLLM 공식 문서: https://docs.litellm.ai/
  - 지원 모델 목록: https://docs.litellm.ai/docs/providers
  - 코드 예시:
    ```python
    from litellm import completion
    import os
    os.environ["OPENAI_API_KEY"] = "sk-..."
    
    response = completion(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.choices[0].message.content)
    ```

  **Acceptance Criteria**:
  
  **TDD - RED phase**:
  - [ ] `tests/test_providers.py` 생성
  - [ ] 테스트 케이스: chat 기본 동작, 모델 선택, 에러 핸들링 (mock)
  - [ ] `uv run pytest tests/test_providers.py -v` → FAIL

  **TDD - GREEN phase**:
  - [ ] `src/tokencrush/providers.py` 구현
  - [ ] `uv run pytest tests/test_providers.py -v` → PASS

  **Manual Execution Verification**:
  - [ ] `uv run python -c "from tokencrush.providers import LLMProvider; print(LLMProvider)"` → 클래스 출력

  **Commit**: YES
  - Message: `feat(providers): add LiteLLM based multi-provider support`
  - Files: `src/tokencrush/providers.py`, `tests/test_providers.py`
  - Pre-commit: `uv run pytest tests/test_providers.py`

---

### Task 6: CLI 통합

- [ ] 6. Typer CLI 엔트리포인트 구현 (compress, chat, config)

  **What to do**:
  - `tests/test_cli.py` 작성 (RED)
  - `src/tokencrush/cli.py` 구현 (GREEN)
  - 명령어:
    - `tokencrush compress <text> [--rate 0.5] [--gpu]`
    - `tokencrush chat <prompt> --model <model> [--rate 0.5] [--gpu]`
    - `tokencrush config set <provider> <key>`
    - `tokencrush config show`
  - Rich 라이브러리로 컬러풀한 출력
  - `pyproject.toml`에 `[project.scripts]` 추가

  **Must NOT do**:
  - 복잡한 서브커맨드 구조 금지
  - 인터랙티브 모드 금지 (MVP 범위 외)
  - stats, 파이프 지원 금지 (2차 범위)
  - 한국어/비영어 주석 금지 (모든 docstrings, comments는 영어로)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Typer는 단순하고 직관적, 통합 작업
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: TUI 아님, 단순 CLI

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Sequential)
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 3, 4, 5

  **References**:
  
  **Pattern References** (이전 Tasks에서 생성):
  - `src/tokencrush/compressor.py:TokenCompressor` - compress 명령에서 사용
  - `src/tokencrush/config.py:ConfigManager` - config 명령에서 사용
  - `src/tokencrush/providers.py:LLMProvider` - chat 명령에서 사용

  **External References**:
  - Typer 공식 문서: https://typer.tiangolo.com/
  - Rich 공식 문서: https://rich.readthedocs.io/
  - 코드 예시:
    ```python
    import typer
    from rich.console import Console
    
    app = typer.Typer()
    console = Console()
    
    @app.command()
    def compress(text: str, rate: float = 0.5, gpu: bool = False):
        """Compress prompt to reduce tokens."""
        console.print(f"[green]Compressing...[/green]")
        # ...
    
    @app.command()
    def chat(prompt: str, model: str = "gpt-4", rate: float = 0.5):
        """Compress and send to LLM."""
        # ...
    ```

  **Acceptance Criteria**:
  
  **TDD - RED phase**:
  - [ ] `tests/test_cli.py` 생성
  - [ ] 테스트 케이스: compress 명령, chat 명령, config 명령 (CliRunner 사용)
  - [ ] `uv run pytest tests/test_cli.py -v` → FAIL

  **TDD - GREEN phase**:
  - [ ] `src/tokencrush/cli.py` 구현
  - [ ] `uv run pytest tests/test_cli.py -v` → PASS

  **Manual Execution Verification**:
  - [ ] `uv run tokencrush --help` → 명령어 목록 출력
  - [ ] `uv run tokencrush compress --help` → compress 도움말 출력
  - [ ] `uv run tokencrush config show` → 설정 출력 (또는 빈 상태 안내)

  **Commit**: YES
  - Message: `feat(cli): add compress, chat, config commands with Typer`
  - Files: `src/tokencrush/cli.py`, `tests/test_cli.py`, `pyproject.toml`
  - Pre-commit: `uv run pytest`

---

### Task 7: 통합 테스트

- [ ] 7. End-to-End 통합 테스트 작성

  **What to do**:
  - `tests/test_integration.py` 작성
  - 시나리오 테스트:
    1. config set → config show → 키 확인
    2. compress → 압축률 확인
    3. chat → (mock) 응답 확인
  - 실제 API 호출 없이 mock으로 전체 플로우 검증

  **Must NOT do**:
  - 실제 LLM API 호출 금지 (비용 발생)
  - 실제 LLMLingua 모델 로드 금지 (시간 소요)
  - 복잡한 E2E 시나리오 금지 (핵심만)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 이미 구현된 코드의 통합 테스트
  - **Skills**: []
    - 특별한 스킬 불필요
  - **Skills Evaluated but Omitted**:
    - `playwright`: CLI 테스트, 브라우저 불필요

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Sequential)
  - **Blocks**: Task 8
  - **Blocked By**: Task 6

  **References**:
  
  **Pattern References**:
  - `tests/test_cli.py` - CLI 테스트 패턴
  - `tests/conftest.py` - 공통 fixtures

  **External References**:
  - pytest-mock: https://pytest-mock.readthedocs.io/

  **Acceptance Criteria**:
  
  **Manual Execution Verification**:
  - [ ] `uv run pytest tests/test_integration.py -v` → 모든 통합 테스트 통과
  - [ ] `uv run pytest -v` → 전체 테스트 스위트 통과 (0 failures)

  **Commit**: YES
  - Message: `test: add end-to-end integration tests`
  - Files: `tests/test_integration.py`
  - Pre-commit: `uv run pytest`

---

### Task 8: README 및 패키지 마무리

- [ ] 8. 문서화 및 PyPI 배포 준비

  **What to do**:
  - `README.md` 작성:
    - 설치 방법 (`pip install tokencrush`)
    - 빠른 시작 가이드
    - 명령어 레퍼런스
    - 지원 모델 목록
    - 라이선스 (MIT)
  - `LICENSE` 파일 생성 (MIT)
  - `pyproject.toml` 최종 검토 (메타데이터, classifiers)
  - `.gitignore` 추가

  **Must NOT do**:
  - 실제 PyPI 배포 금지 (별도 작업)
  - 복잡한 문서 구조 금지 (단일 README)
  - 다국어 문서 금지 (영어만)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 문서 작성 중심 작업
  - **Skills**: [`git-master`]
    - `git-master`: 최종 커밋 및 태그
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: 문서 작업

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (Final)
  - **Blocks**: None
  - **Blocked By**: Task 7

  **References**:
  
  **External References**:
  - PyPI 패키징 가이드: https://packaging.python.org/en/latest/tutorials/packaging-projects/
  - README 베스트 프랙티스: https://www.makeareadme.com/

  **Acceptance Criteria**:
  
  **Manual Execution Verification**:
  - [ ] `cat README.md` → 설치, 사용법, 라이선스 섹션 확인
  - [ ] `cat LICENSE` → MIT 라이선스 텍스트 확인
  - [ ] `uv build` → dist/ 디렉토리에 .whl, .tar.gz 생성
  - [ ] `pip install dist/*.whl && tokencrush --help` → 설치 후 실행 확인

  **Commit**: YES
  - Message: `docs: add README and prepare for PyPI release`
  - Files: `README.md`, `LICENSE`, `pyproject.toml`, `.gitignore`
  - Pre-commit: `uv run pytest`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `chore: initialize tokencrush project with uv` | pyproject.toml, src/tokencrush/__init__.py | import tokencrush |
| 2 | `test: add pytest infrastructure` | tests/conftest.py, tests/test_example.py | pytest passes |
| 3 | `feat(compressor): add LLMLingua-2 based prompt compression` | compressor.py, test_compressor.py | pytest passes |
| 4 | `feat(config): add API key management with TOML storage` | config.py, test_config.py | pytest passes |
| 5 | `feat(providers): add LiteLLM based multi-provider support` | providers.py, test_providers.py | pytest passes |
| 6 | `feat(cli): add compress, chat, config commands with Typer` | cli.py, test_cli.py | pytest passes |
| 7 | `test: add end-to-end integration tests` | test_integration.py | pytest passes |
| 8 | `docs: add README and prepare for PyPI release` | README.md, LICENSE | uv build succeeds |

---

## Success Criteria

### Verification Commands
```bash
# 전체 테스트
uv run pytest -v
# Expected: All tests passed

# CLI 설치 확인
uv run tokencrush --help
# Expected: Usage: tokencrush [OPTIONS] COMMAND [ARGS]...

# 압축 테스트 (mock 없이 실제 동작)
uv run tokencrush compress "This is a very long text that needs compression" --rate 0.5
# Expected: Compressed text output with token stats

# 패키지 빌드
uv build
# Expected: dist/tokencrush-0.1.0-py3-none-any.whl
```

### Final Checklist
- [ ] 모든 Must Have 기능 구현됨
- [ ] 모든 Must NOT Have 항목 준수됨
- [ ] 전체 테스트 통과 (`uv run pytest` → 0 failures)
- [ ] CLI 명령어 3개 동작 (compress, chat, config)
- [ ] README 작성 완료
- [ ] MIT 라이선스 추가됨
- [ ] 패키지 빌드 성공 (`uv build`)

---

## Future Work (2차 범위, 이 계획에서 제외)

- `tokencrush stats` - 압축률, 비용 절감 통계
- 파이프 지원 (`echo "..." | tokencrush compress`)
- 응답 캐싱
- 스트리밍 응답
- 비용 추적 대시보드
- 멀티턴 대화 세션
