# Cisco SD-WAN CI/CD Pipeline PoC

Git 기반 Infrastructure-as-Code로 Cisco SD-WAN을 관리하는 CI/CD 파이프라인 PoC.

## 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Git Repo   │────▶│  GitHub      │────▶│  Python CLI     │────▶│  vManage     │
│  (YAML)     │     │  Actions     │     │  (validate →    │     │  REST API    │
│             │     │              │     │   plan → deploy) │     │              │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
```

### 파이프라인 단계

| 단계 | 트리거 | 설명 |
|------|--------|------|
| **validate** | PR 생성 | YAML 문법, JSON Schema, 상호참조 검증 |
| **plan** | PR 생성 | 현재 상태 vs 원하는 상태 diff 생성 |
| **deploy** | main 머지 | vManage API로 변경사항 적용 |

## 프로젝트 구조

```
sdwan-cicd-poc/
├── configs/                    # SD-WAN 설정 (YAML)
│   ├── templates/              #   Feature/Device 템플릿
│   ├── policies/               #   트래픽 정책, SLA 클래스
│   ├── devices/                #   디바이스별 변수
│   └── schemas/                #   JSON Schema (검증용)
├── sdwan_client/               # vManage REST API 클라이언트
│   ├── auth.py                 #   인증 (세션 + XSRF 토큰)
│   ├── templates.py            #   템플릿 CRUD
│   ├── policies.py             #   정책 CRUD
│   └── devices.py              #   디바이스 조회/관리
├── pipeline/                   # CI/CD 파이프라인 로직
│   ├── cli.py                  #   CLI 엔트리포인트
│   ├── validate.py             #   설정 검증
│   ├── plan.py                 #   변경 계획 (diff)
│   └── deploy.py               #   배포 실행
├── tests/                      # 테스트
├── .github/workflows/          # GitHub Actions
└── pyproject.toml
```

## 빠른 시작

### 1. 환경 설정

```bash
cd sdwan-cicd-poc
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # vManage 접속 정보 설정
```

### 2. 설정 검증 (오프라인)

```bash
python -m pipeline.cli validate
```

### 3. 변경 계획 확인

```bash
# 로컬 전용 (vManage 연결 없이)
python -m pipeline.cli plan --local

# vManage 연결하여 실제 diff
python -m pipeline.cli plan
```

### 4. 배포

```bash
# Dry-run (실제 변경 없음)
python -m pipeline.cli deploy --dry-run

# 실제 배포
python -m pipeline.cli deploy
```

### 5. 디바이스 상태 확인

```bash
python -m pipeline.cli status
```

## Cisco DevNet Sandbox 테스트

Cisco에서 무료로 제공하는 [Always-On SD-WAN Sandbox](https://developer.cisco.com/sdwan/sandbox/)로 테스트 가능:

```bash
export VMANAGE_URL=https://sandbox-sdwan-2.cisco.com
export VMANAGE_USERNAME=devnetuser
export VMANAGE_PASSWORD='RG!_Yw919_83'

python tests/test_sandbox_connection.py
```

## 설정 작성 가이드

### Feature Template (configs/templates/)

```yaml
feature_templates:
  - name: "MY-SYSTEM-TEMPLATE"        # UPPER-KEBAB-CASE 필수
    description: "System template"
    template_type: "cisco_system"
    device_type: ["vedge-C8000V"]
    definition:
      site_id: "{{site_id}}"          # {{변수}} = 디바이스별 값
      system_ip: "{{system_ip}}"
```

### Device 변수 (configs/devices/)

```yaml
devices:
  - hostname: "BRANCH-01"
    device_id: "C8K-SERIAL-NUMBER"
    system_ip: "10.255.1.1"
    site_id: "1001"
    device_template: "BRANCH-DEVICE-TEMPLATE"
    variables:                         # 템플릿 변수 매핑
      hostname: "BRANCH-01"
      system_ip: "10.255.1.1"
      site_id: "1001"
```

## GitHub Actions 설정

Repository Settings > Secrets에 추가:

| Secret | 설명 |
|--------|------|
| `VMANAGE_URL` | vManage URL (e.g., `https://vmanage.example.com`) |
| `VMANAGE_USERNAME` | API 사용자 이름 |
| `VMANAGE_PASSWORD` | API 비밀번호 |
| `VMANAGE_PORT` | 포트 (기본값: 443) |

Repository Variables:

| Variable | 설명 |
|----------|------|
| `ENABLE_REMOTE_PLAN` | `true` 설정 시 PR에서 vManage diff 실행 |
| `ENABLE_DEPLOY` | `true` 설정 시 main 머지 시 자동 배포 |

## 확장 가이드

이 PoC를 프로덕션으로 확장하려면:

1. **Terraform 전환**: `CiscoDevNet/sdwan` Terraform provider 사용 → state 관리 자동화
2. **catalystwan SDK**: `pip install catalystwan` → Cisco 공식 Python SDK로 전환
3. **승인 게이트**: GitHub Environment protection rules로 배포 승인 프로세스
4. **롤백**: 이전 config snapshot 저장 + 원클릭 롤백 기능
5. **모니터링**: 배포 후 SLA 메트릭 자동 검증
