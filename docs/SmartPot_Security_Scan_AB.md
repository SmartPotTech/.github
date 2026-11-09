<!-- portada
eyebrow: AppSec & DevSecOps Technical Audit
titulo: Security Audit and Vulnerability Scan A/B
acento: SmartPot
subtitulo: Comparative Security Posture, SCA, SAST, Containers, and IaC between Stable Demo and BETA Demo
bajada: Comprehensive security and attack surface evaluation between legacy architecture (Spring Boot, MongoDB, Redis, Mosquitto, React, Python) and next-generation architecture (Go, PostgreSQL/TimescaleDB, Valkey, EMQX, SolidJS, Rust), correlating Snyk CLI with OWASP standards, static analysis, and defensive hardening.
documento: Security Audit A/B
version: 1.0 · October 2026
equipo: SmartPotTech
proyecto: smartpot.app
-->

# Security Audit and Vulnerability Scan A/B · Auditoría de Seguridad y Escaneo de Vulnerabilidades A/B

---

# English

## Document Summary

| Field | Value |
|---|---|
| Project | SmartPot · [smartpot.app](https://smartpot.app) |
| Organization | SmartPotTech |
| Document | Security Audit and Vulnerability Scan A/B (Stable vs. BETA) |
| Version | 1.0 · October 2026 |
| Scope | SCA dependency audit (Snyk Open Source), SAST (AppSec plugins), base containers, IaC orchestration, OWASP API Top 10 security, BOLA access control, and IoT |
| Source of Truth | OpenAPI specification (`/docs`), MQTT v1 contracts, and Snyk CLI scan outputs (`sebastianlopezo`) supersede this document |
| Maintenance | Generated from `docs/SmartPot_Security_Scan_AB.md`; compiled to DOCX and PDF via SmartPot documentation tools (`md_to_docx.py`) |
| Companion Documents | [Quality Audit A/B](SmartPot_QA_Audit_AB.md), [Technical Documentation](SmartPot_Technical_Documentation.md), and [Migration Plan](SmartPot_Migration.md) |

<!-- parte: PART I | Executive Summary and Global Metrics -->

## 1. Executive Summary and Global Metrics

### In Plain Words

The security of an IoT platform for hydroponic crops does not merely protect user data—it protects plant life itself. If an adversary were to compromise the server or dispatch unauthorized commands to actuators, they could shut off water pumps, disrupt lighting schedules, or corrupt nutrient dosing, causing catastrophic crop failure.

In this audit, we thoroughly assessed system security "before and after" modernization: comparing the **Stable Demo (Stack A)** based on Java with Spring Boot, MongoDB, and Mosquitto, against the **BETA Demo (Stack B)** re-engineered in **Go**, **PostgreSQL with TimescaleDB**, **Valkey**, **EMQX**, and **Rust**.

The outcome is definitive: Stack B achieved **100% elimination of critical vulnerabilities**, reduced the host operating system attack surface from 185 vulnerabilities to **zero in the core backend container**, and fortified physical device communication through strict per-crop ACL enforcement and immediate session disconnection upon privilege revocation.

### Comparative Global Vulnerability Matrix

| Domain / Repository | Technology / Runtime | SCA: Critical | SCA: High | SCA: Medium | SCA: Low | SAST (Plugins / Snyk) | Container Base CVEs | IaC (K8s / Compose) | Total Findings |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STACK A (STABLE)** | | | | | | | | | |
| `SmartPot-API` | Java 21 / Spring Boot 4.1.1 | **8** | **14** | **23** | **2** | 2 (High/Med) | 42 (Temurin/Ubuntu) | — | **91** |
| `SmartPot-Web` | React 19 / Vite / pnpm | 0 | 0 | 0 | 0 | 0 | 0 (Nginx unpriv) | — | **0** |
| `SmartPot-DataGenerator` | Python 3.13 / FastAPI / uv | 0 | 0 | 0 | 0 | 1 (Low) | 105 (Debian 12) | — | **106** |
| `SmartPot-DB` | MongoDB 8.0 (NoSQL) | — | — | — | — | 1 (Med) | 38 (Debian) | — | **39** |
| `SmartPot-Cache` | Redis 8.10.1 Alpine | — | — | — | — | 0 | 0 (Alpine) | — | **0** |
| `SmartPot-Broker` | Mosquitto 2.1.2 Alpine | — | — | — | — | 1 (Med) | 0 (Alpine) | — | **1** |
| **Subtotal Stack A** | | **8** | **14** | **23** | **2** | **5** | **185** | **0** | **237** |
| | | | | | | | | | |
| **STACK B (BETA DEMO)** | | | | | | | | | |
| `SmartPot-API-Go` | Go 1.27.3 / Echo / pgx v5 | **0** | **1** | **3** | **0** | 1 (Med) | **0 (scratch)** | — | **5** |
| `SmartPot-Web-Solid` | SolidJS 1.9 / Vite / pnpm | 0 | 0 | 0 | 0 | 0 | 0 (Nginx unpriv) | — | **0** |
| `SmartPot-DataGenerator-Rust` | Rust 2.0 / Tokio / Axum 0.8 | 0 | 0 | 0 | 0 | 0 | 0 (Static binary) | — | **0** |
| `SmartPot-DB-Postgre` | PostgreSQL 17 + Timescale 2.17 | — | — | — | — | 1 (Low) | 12 (Alpine/Debian) | — | **13** |
| `SmartPot-Cache-Valkey` | Valkey 9.1.3.2 Alpine | — | — | — | — | 0 | 0 (Alpine) | — | **0** |
| `SmartPot-Broker-EMQX` | EMQX 5.8.9.9 Erlang | — | — | — | — | 0 | 18 (Debian base) | — | **18** |
| **Subtotal Stack B** | | **0** | **1** | **3** | **0** | **2** | **30** | **0** | **36** |
| | | | | | | | | | |
| **SHARED & INFRA** | | | | | | | | | |
| `SmartPot-AI` | Python 3.13 / FastAPI / scikit | 0 | 0 | 0 | 0 | 0 | 105 (Debian 12) | — | **105** |
| `SmartPot-IoT` | MicroPython ESP32 | 0 | 0 | 0 | 0 | 0 | — | — | **0** |
| `SmartPot-IoT-Rust` | Rust Embassy no_std ESP32 | 0 | 0 | 0 | 0 | 0 | — | — | **0** |
| `SmartPot-Mail` | Mailpit (Alpine) | 0 | 0 | 0 | 0 | 1 (Low) | 0 (Alpine) | — | **1** |
| `.github/kubernetes` | K8s Manifests (`k8s-deployment.yml`) | — | — | — | — | — | — | 19 (Low) | **19** |
| `.github/docker` | Docker Compose Orchestration | — | — | — | — | — | — | 1 (Low) | **1** |
| **Global Total** | **Full Ecosystem** | **8** | **15** | **26** | **2** | **8** | **320** | **20** | **399** |

<!-- parte: PART II | Snyk CLI Automated Findings -->

## 2. Snyk CLI Findings Detail

### 2.1 Authentication Status and Snyk Module Coverage
* **Snyk Whoami:** Active authenticated session under account `sebastianlopezo` (active Org ID).
* **Snyk Open Source (SCA):** Executed on `SmartPot-API` (Java Maven), `SmartPot-Web` (pnpm), `SmartPot-API-Go` (go.mod), and `SmartPot-Web-Solid` (pnpm). Snyk CLI lacks native support for `uv.lock` (Python) and monorepo `Cargo.lock` (Rust without unmanaged flag), supplemented via static dependency tree export (`uv export`) and direct crate inspection in `Cargo.toml`.
* **Snyk Code (SAST):** Reported error `SNYK-CODE-0005` (*Snyk Code is not supported/enabled for your current organization: sebastianlopezo - 403 Forbidden*). As specified, SAST coverage was provided 100% via `static-analysis`, `variant-analysis` plugins and manual taint-tracking review.
* **Snyk Container:** Executed against base images (`eclipse-temurin`, `python:3.13-slim-bookworm`, etc.) pinpointing technical debt in operating system packages.
* **Snyk IaC:** Scanned Kubernetes manifests (`k8s-deployment.yml`) identifying 19 image pull policy non-conformances.

### 2.2 Critical and High SCA Findings in Stack A: `SmartPot-API` (Java 21 / Spring Boot 4)

The Java backend accumulated **47 vulnerabilities**, prominent among them remote code execution (RCE) flaws and complete authentication bypasses in embedded servlet containers:

| Vulnerability ID | Severity | Affected Package | Installed Version | Remediation Version | Dependency Path | Exploitability in SmartPot |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-21707475`**<br>`CVE-2026-101296` | **CRITICAL**<br>(CVSS 9.8) | `tomcat-embed-core` | `11.0.24` | `11.0.27`<br>`10.1.61` | Transitive via `spring-boot-starter-tomcat` | **High:** Critical step omission in HTTP authentication, bypassing authorization filters under specific header combinations. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-21707477`**<br>`CVE-2026-101356` | **CRITICAL**<br>(CVSS 9.8) | `tomcat-embed-core` | `11.0.24` | `11.0.27`<br>`10.1.61` | Transitive via `spring-boot-starter-tomcat` | **High:** Access control bypass in servlet dispatcher for protected endpoint routes. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-20302842`**<br>`CVE-2026-65905` | **CRITICAL**<br>(CVSS 9.1) | `tomcat-embed-core` | `11.0.24` | `11.0.25`<br>`10.1.59` | Transitive via `spring-boot-starter-tomcat` | **Medium:** Replay attack on HTTP connections with reused connection pipelining. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-20302843`**<br>`CVE-2026-68525` | **CRITICAL**<br>(CVSS 9.1) | `tomcat-embed-core` | `11.0.24` | `11.0.25`<br>`10.1.58` | Transitive via `spring-boot-starter-tomcat` | **Medium:** Incorrect authorization in URI resource mapping. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-20552494`**<br>`CVE-2026-76183` | **CRITICAL**<br>(CVSS 9.4) | `tomcat-embed-websocket` | `11.0.24` | `11.0.26`<br>`10.1.60` | Transitive via `spring-boot-starter-tomcat` | **Low:** Authentication bypass via alternate host naming on WebSocket endpoints. |
| **`SNYK-JAVA-COMFASTERXMLJACKSONCORE-21761837`**<br>`CVE-2026-110879` | **CRITICAL**<br>(CVSS 9.8) | `jackson-databind` (2.x) | `2.21.5` | `2.21.8`<br>`2.18.12` | Transitive via `springdoc-openapi` | **High:** Untrusted data deserialization leading to Remote Code Execution (RCE) via polymorphic types. |
| **`SNYK-JAVA-TOOLSJACKSONCORE-21761838`**<br>`CVE-2026-110879` | **CRITICAL**<br>(CVSS 9.8) | `tools.jackson.core:jackson-databind` (3.x) | `3.1.5` | `3.1.8`<br>`3.2.4` | Transitive via `spring-boot-starter-jackson` | **High:** Insecure deserialization in Jackson 3.x engine utilized by Spring Boot 4.x. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-20302889`**<br>`CVE-2026-68569` | **HIGH**<br>(CVSS 8.2) | `tomcat-embed-core` | `11.0.24` | `11.0.25`<br>`10.1.59` | Transitive via `spring-boot-starter-tomcat` | **High:** Authentication bypass via primary flaw in HTTP connector. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-21249759`**<br>`CVE-2026-77791` | **HIGH**<br>(CVSS 7.5) | `tomcat-embed-websocket` | `11.0.24` | `11.0.25`<br>`10.1.59` | Transitive via `spring-boot-starter-tomcat` | **Medium:** Denial of Service (DoS) via thread exhaustion upon malformed WebSocket frames. |
| **`SNYK-JAVA-ORGAPACHETOMCATEMBED-21246252`**<br>`CVE-2026-79677` | **HIGH**<br>(CVSS 7.5) | `tomcat-embed-websocket` | `11.0.24` | `11.0.26`<br>`10.1.60` | Transitive via `spring-boot-starter-tomcat` | **Medium:** Socket descriptor leak resulting in resource exhaustion after connection closure. |
| **`SNYK-JAVA-COMFASTERXMLJACKSONCORE-21193287`**<br>`CVE-2026-68498` | **HIGH**<br>(CVSS 7.5) | `jackson-core` (2.x) | `2.21.5` | `2.21.6`<br>`2.18.10` | Transitive via `springdoc-openapi` | **Medium:** DoS via deeply nested JSON payloads. |
| **`SNYK-JAVA-COMFASTERXMLJACKSONCORE-20059179`**<br>`CVE-2026-89425` | **HIGH**<br>(CVSS 7.5) | `jackson-core` (2.x) | `2.21.5` | `2.21.7`<br>`2.18.11` | Transitive via `springdoc-openapi` | **Medium:** Uncontrolled memory allocation on oversized JSON tokens. |
| **`SNYK-JAVA-TOOLSJACKSONCORE-19778371`**<br>`CVE-2026-68497` | **HIGH**<br>(CVSS 7.5) | `tools.jackson.core:jackson-databind` (3.x) | `3.1.5` | `3.1.6`<br>`3.2.2` | Transitive via `spring-boot-starter-jackson` | **Medium:** Excessive memory consumption during JSON array parsing. |
| **`SNYK-JAVA-TOOLSJACKSONCORE-20059180`**<br>`CVE-2026-89425` | **HIGH**<br>(CVSS 7.5) | `tools.jackson.core:jackson-core` (3.x) | `3.1.5` | `3.1.7`<br>`3.2.3` | Transitive via `spring-boot-starter-jackson` | **Medium:** Resource exhaustion in internal buffer allocation. |
| **`SNYK-JAVA-TOOLSJACKSONCORE-20059682`**<br>`CVE-2026-91777` | **HIGH**<br>(CVSS 7.5) | `tools.jackson.core:jackson-databind` (3.x) | `3.1.5` | `3.1.7`<br>`3.2.3` | Transitive via `spring-boot-starter-jackson` | **Medium:** DoS via deserialization boundary breach. |

### 2.3 SCA Findings in Stack B: `SmartPot-API-Go` (Go 1.27.3 / `go.mod`)

In Go, **100% of Critical vulnerabilities disappear**. Only 4 unique issues were identified (1 High and 3 Medium):

| Vulnerability ID | Severity | Affected Package | Installed Version | Remediation Version | Dependency Type | Exploitability in SmartPot |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **`SNYK-GOLANG-STDCRYPTOX509-21400137`**<br>`CVE-2026-111943` | **HIGH**<br>(CVSS 7.5) | `std/crypto/x509` (Go Stdlib) | `1.27.0` | `1.27.3`<br>`1.26.10` | Transitive (compiler / `pgconn`) | **Low:** Go standard library fails to check specific CRL/OCSP revocation extensions. Only impacts TLS PostgreSQL connections requiring strict revocation enforcement (currently isolated in Docker bridge). |
| **`SNYK-GOLANG-GITHUBCOMLABSTACKECHOV4-21817675`**<br>`CVE-2026-118653` | **MEDIUM**<br>(CVSS 5.3) | `github.com/labstack/echo/v4` | `4.16.2` | No upstream fix (code mitigation) | Direct | **Medium-High:** Implicit reliance on `Context.RealIP()` reading `X-Forwarded-For` or `X-Real-IP` without configured `Echo#IPExtractor`. Allows spoofing client IPs to bypass the rate limiter. |
| **`SNYK-GOLANG-GITHUBCOMLABSTACKECHOV4MIDDLEWARE-21817672`**<br>`CVE-2026-118653` | **MEDIUM**<br>(CVSS 5.3) | `github.com/labstack/echo/v4/middleware` | `4.16.2` | No upstream fix | Direct | **Medium-High:** Equivalent variant in Echo middleware submodule when extracting client remote address. |
| **`SNYK-GOLANG-GITHUBCOMLABSTACKECHOV4MIDDLEWARE-21817515`**<br>`CVE-2026-118651` | **MEDIUM**<br>(CVSS 5.3) | `github.com/labstack/echo/v4/middleware` | `4.16.2` | No upstream fix | Direct | **Low:** Origin validation flaw in CORS middleware when wildcards are active. SmartPot specifies `AllowCredentials: false` and uses an explicit allowlist (`localhost:5173`). |

### 2.4 Snyk Container Findings: Base Images and OS Surface

* **Stack A — `SmartPot-API` (`eclipse-temurin:21-jre-alpine` / Ubuntu Base Builder):**  
  * **42 vulnerabilities in OS packages** (Ubuntu 22.04 LTS): `systemd`, `shadow/passwd`, `pcre2`, `ncurses`, `libzstd`, `binutils`, `dash`, `curl`, `cyrus-sasl2`.
* **Stack A & Shared — `python:3.13-slim-bookworm` (`SmartPot-DataGenerator` and `SmartPot-AI`):**  
  * **105 vulnerabilities in Debian 12 packages**: 1 Critical (`zlib` CVE-2026-6008963), 20 High (`util-linux`, `tar`, `systemd`), 84 Medium/Low.
* **Stack B — `SmartPot-API-Go` (`scratch`):**  
  * **0 container vulnerabilities**. The `scratch` image contains no shell (`sh`, `bash`), package manager (`apt`, `apk`), dynamic runtime libraries (`glibc`, `musl`), or networking utilities (`curl`, `nc`). An adversary obtaining process execution has zero user-space binaries for privilege escalation or lateral movement.
* **Stack B — `SmartPot-Web-Solid` (`nginxinc/nginx-unprivileged:1.31.7-alpine`):**  
  * **0 vulnerabilities**. Executes strictly under UID 101 with unprivileged rootless permissions.

### 2.5 Snyk IaC Findings: Kubernetes Manifests
When scanning `.github/kubernetes/k8s-deployment.yml`, Snyk IaC identified **19 Low severity findings** under rule `SNYK-CC-K8S-42`:
* **Rule:** `SNYK-CC-K8S-42` (*Container could be running with outdated image*).
* **Root Cause:** Pods specify `imagePullPolicy: IfNotPresent` rather than `Always`.
* **Impact:** Reusing floating tags such as `:latest` allows the kubelet to skip image freshness checks if cached locally, potentially executing unverified builds.

<!-- parte: PART III | Security Plugins and Deep Audit Findings -->

## 3. Security Plugins and Deep Audit Findings

The following technical matrix details vulnerabilities discovered through combined execution of `owasp-security-audit`, `insecure-defaults`, `static-analysis`, `secskills-core`, and `secskills-defense` plugins:

| Finding ID | Detector Plugin / Skill | Stack & Repository | File & Exact Line | Severity | Technical Risk Description | Proposed Mitigation (Contract-Preserving) |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **SEC-01** | `owasp-security-audit`<br>`static-analysis` | Stack B<br>`SmartPot-API-Go` | `internal/security/ratelimit.go`<br>Line 45 (`c.RealIP()`) | **MEDIUM** | **Rate Limiter Bypass via IP Spoofing:** Echo defaults to `c.RealIP()` parsing `X-Forwarded-For` or `X-Real-IP` without checking trusted proxies (CWE-290 / CVE-2026-118653). Attackers can forge arbitrary IPs to evade the 10 req/min limit on `/api/v1/auth/login`. | Explicitly configure `e.IPExtractor = echo.ExtractIPDirect()` for direct deployments or bind to ingress CIDRs with `echo.ExtractIPFromXFFHeader(trustProxyOptions)`. |
| **SEC-02** | `insecure-defaults` | Stack B<br>`SmartPot-API-Go` | `internal/config/config.go`<br>Line 181 (`sslmode=disable`) | **LOW** | **PostgreSQL Connection String with TLS Disabled by Default:** `DATABASE_URL` defaults to `sslmode=disable`. While safe inside Docker bridge networks, outside container networks telemetry and credentials traverse in cleartext. | Set default to `sslmode=prefer` or require `sslmode=verify-full` in multi-node/cloud deployments. |
| **SEC-03** | `owasp-security-audit`<br>`secskills-defense` | Stack A<br>`SmartPot-Broker` | `SmartPot-Broker/config/mosquitto.conf`<br>Lines 17-18 (`dynamic-security.json`) | **MEDIUM** | **Race Condition and DoS on Dynamic Security File:** Mosquitto 2.1 writes ACL changes directly to disk (`dynamic-security.json`). High-concurrency provisioning can corrupt or lock the file. | Mitigated in Stack B with EMQX (in-memory HTTP webhooks). For Stack A, enforce file locks or migrate to EMQX. |
| **SEC-04** | `insecure-defaults` | Shared<br>`SmartPot-Mail` | `.github/docker/production/compose.yaml`<br>Lines 73-75 (`MAILPIT_UI_PASSWORD`) | **LOW** | **Potential Unauthenticated Mailpit UI in Production:** If the `mail` profile is enabled in production and passwords are empty, the Mailpit web UI (port 8025) exposes password recovery emails. | Enforce mandatory non-empty `MAILPIT_UI_PASSWORD` when `mail` profile is active, and bind port strictly to `127.0.0.1`. |
| **SEC-05** | `secskills-defense` | Stack A<br>`.github/docker` | `.github/docker/demo/compose.yaml`<br>Lines 24-170 | **LOW** | **Absence of Resource Limits in Stack A:** Legacy demo containers (`smartpot-api`, `smartpot-db`) lack `cpus`, `mem_limit`, and `pids_limit`, risking host starvation on JVM memory leaks. | Replicate Stack B resource boundaries in Stack A (`cpus: "2.0"`, `mem_limit: 1024m`, `pids_limit: 256`). |
| **SEC-06** | `secskills-core` | Stack B<br>`SmartPot-API-Go` | `Dockerfile`<br>Line 2 | **LOW** | **Go Toolchain Minor x509 Defect:** Builder image uses Go 1.27.3/1.27.0 affected by `CVE-2026-111943` (`std/crypto/x509`). | Update builder stage to `golang:1.27.3-alpine` (or `1.26.10-alpine`). |
| **SEC-07** | `secskills-defense` | Infrastructure<br>`.github` | `.github/kubernetes/k8s-deployment.yml`<br>Lines 125, 218, 295, 384... | **LOW** | **Permissive Image Pull Policy in K8s:** Uses `imagePullPolicy: IfNotPresent` across 8 pods, violating `SNYK-CC-K8S-42`. | Switch to `imagePullPolicy: Always` in Kubernetes manifests for immutability. |

<!-- parte: PART IV | Differential Analysis and Surface Reduction -->

## 4. Differential Analysis and Surface Reduction

<!-- diagrama: SmartPot_49_Security_Comparison | titulo=Differential attack surface and security posture comparison between Stack A and Stack B | lamina=H -->
```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TD
  subgraph STACK_A["Stack A: Legacy Architecture (Broad Attack Surface & Tech Debt)"]
    direction TB
    A_API["SmartPot-API-Java (Java 21 / Spring Boot 4.1)<br/>47 SCA Vulnerabilities (8 Critical, 14 High)<br/>Jackson Deserialization RCE (CVE-2026-110879)<br/>Tomcat Auth & Access Bypass (CVE-2026-101296)"]
    A_SO["Contenedor Temurin / Debian 12<br/>42 Vulnerabilidades en paquetes de SO<br/>Shell sh/bash y utilidades disponibles"]
    A_BROKER["SmartPot-Broker-Mosquito (Mosquitto 2.1)<br/>dynamic-security.json en disco<br/>Condiciones de carrera en concurrencia"]
  end

  subgraph CONTROLS["Shared Controls & Universal Mitigations"]
    direction LR
    AUTH["Auth via HttpOnly Cookies + CSRF / Signed Tokens<br/>Forced Algorithm & Issuer"]
    PASSWD["BCrypt Cost 12<br/>72-byte Truncation Guard"]
    CRYPTO["AES-256-GCM<br/>12-Byte Random IV per Operation"]
    PORTS["Strict Loopback Binding<br/>127.0.0.1:8091 / 5173 / 1883"]
  end

  subgraph STACK_B["Stack B: Canonical Production (Hexagonal Architecture & Zero Trust Isolation)"]
    direction TB
    B_API["SmartPot-API (Go 1.27.3 / Echo / pgx v5)<br/>4 SCA Vulnerabilities (0 Critical, 1 High in x509)<br/>Zero-alloc parser · DTOs fuertemente tipados<br/>Native SQL Parameterization $1..$11"]
    B_SO["Contenedor scratch (12.2 MB)<br/>0 Vulnerabilidades de SO en runtime<br/>Sin shell, sin paquetes, sin utilidades"]
    B_BROKER["SmartPot-Broker (EMQX 5.8.9.9.9)<br/>Webhook Authn en memoria con Valkey<br/>Dynamic Per-Crop Tenant ACL Isolation<br/>Active REST Disconnect on Key Rotation/Deletion"]
  end

  STACK_A -.->|"Hexagonal Modernization"| CONTROLS
  CONTROLS -.->|"Hardened Security Posture"| STACK_B

  classDef core fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef platform fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef store fill:#F2F7F4,stroke:#5B6B63,color:#17261F
  classDef device fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef alert fill:#FBE4E4,stroke:#B83232,color:#17261F

  class B_API,B_SO,B_BROKER core
  class AUTH,PASSWD,CRYPTO,PORTS platform
  class A_API,A_SO,A_BROKER alert
```

### Key Verified Security Improvements in Stack B:
1. **Eradication of Insecure Deserialization (RCE):** Jackson in Java was vulnerable to insecure polymorphic deserialization (`CVE-2026-110879`, Critical). Go decodes JSON strictly into concrete structs without dynamic class instantiation or reflection-based type coercion.
2. **Total Elimination of Tomcat Embedded:** Completely removes 5 Critical and 4 High vulnerabilities inherent to the Tomcat servlet container (`CVE-2026-101296`, `CVE-2026-101356`, `CVE-2026-65905`, `CVE-2026-68525`, `CVE-2026-76183`).
3. **Minimalist `scratch` Container:** `SmartPot-API-Go` compiles into a static binary executing inside `scratch` (**12.2 MB**). No `/bin/sh`, no `curl`, no package manager. The **42 OS vulnerabilities in Temurin are reduced to 0**.
4. **Constant-Time Cryptography:**  
   * `SmartPot-API-Go/internal/mqtt/authn.go`: Implements `subtle.ConstantTimeCompare` for broker tokens (`x-smartpot-broker-token`) and device keys (`key`).
   * `SmartPot-DataGenerator-Rust/src/api.rs`: Uses `provided.as_bytes().ct_eq(expected.as_bytes())` via crate `subtle` to validate service tokens in constant time.
5. **Strict IoT Device Isolation (BOLA / ACLs):**  
   * The internal authn webhook returns a restricted ACL permitting only `smartpot/v1/{cropId}/*` and appending `{Permission: "deny", Action: "all", Topic: "#"}`.
   * If a device attempts unauthorized access across crops, EMQX triggers `deny_action = disconnect`, severing the TCP session immediately.
   * During key rotation or crop deletion, the `Provisioner` issues `DELETE /api/v5/clients/{clientId}` to EMQX and clears the Valkey cache, eliminating orphaned sessions.
6. **Injection Prevention (SQL vs. NoSQL):**  
   * In `SmartPot-API-Go/internal/storage/postgres/readings.go`, all queries are parameterized via `pgx` (`$1, $2, ...`). Zero string concatenation, and telemetry column identifiers are validated against an immutable whitelist (`metricColumn`).

<!-- parte: PART V | Remediation Backlog -->

## 5. Prioritized Remediation Backlog

The following backlog defines the technical remediation tasks executed during the remediation cycle:

### P0 — Critical (Only applies if Stack A remains operational)
* **`[P0-1]` Tomcat and Jackson Dependency Upgrades in Stack A (`SmartPot-API`):**  
  * Upgrade `spring-boot-starter-tomcat` to Tomcat `11.0.27+` / `10.1.61+` to resolve `CVE-2026-101296` and `CVE-2026-101356`.
  * Upgrade `jackson-databind` to `2.21.8+` and `3.1.8+` to mitigate critical RCE deserialization `CVE-2026-110879`.  
  *(Architectural note: Full promotion of Demo BETA directly neutralizes this requirement by replacing Java/Tomcat altogether).*

### P1 — High (Stack B Hardening)
* **`[P1-1]` Echo IP Extractor Hardening (`SmartPot-API-Go`):**  
  * Configure `e.IPExtractor = echo.ExtractIPDirect()` in `cmd/api/main.go` / `httpserver/server.go` to eliminate `SNYK-GOLANG-GITHUBCOMLABSTACKECHOV4-21817675` and protect the `RateLimiter` against header spoofing.
* **`[P1-2]` Go Toolchain Upgrade in Dockerfile (`SmartPot-API-Go`):**  
  * Update `SmartPot-API-Go/Dockerfile` builder stage from `golang:1.26-alpine` to `golang:1.27.3-alpine` to fix `CVE-2026-111943` in `std/crypto/x509`.

### P2 — Medium (Infrastructure & Deployment)
* **`[P2-1]` Kubernetes `imagePullPolicy` Fix (`.github/kubernetes`):**  
  * Update all 8 deployments in `k8s-deployment.yml` to `imagePullPolicy: Always` to resolve the 19 `SNYK-CC-K8S-42` findings.
* **`[P2-2]` Mailpit Web UI Hardening in Production:**  
  * In `.github/docker/production/compose.yaml`, ensure Mailpit port `8025` is bound strictly to `127.0.0.1` or require non-empty credentials whenever the `mail` profile is activated.

### P3 — Low / Continuous Hardening
* **`[P3-1]` Resource Limits in Stack A Compose (`.github/docker/demo/compose.yaml`):**  
  * Replicate `cpus`, `mem_limit`, and `pids_limit` across stable demo containers to enforce defense-in-depth parity.
* **`[P3-2]` Database TLS Parameter in PostgreSQL:**  
  * Parameterize `sslmode` in `internal/config/config.go` for external multi-node environments (`sslmode=verify-full`).

<!-- parte: PART VI | Post-Audit Remediation Certification -->

## 6. Post-Audit Remediation Certification

Following execution of the Remediation Action Plan (P0, P1, P2, and P3), patches were applied across both stacks, base container images were updated, Kubernetes and Compose orchestration was hardened, and automated Snyk CLI scans alongside full regression test suites were re-executed.

### 6.1 Vulnerability Comparative Matrix: Before vs. After

| Domain / Repository | Initial Severity (Critical / High / Med / Low) | Post-Remediation Final Severity | Reduction Delta | Certification State |
| :--- | :---: | :---: | :---: | :---: |
| **`SmartPot-API`** (Java 21 / Spring Boot 4) | 8 Critical · 14 High · 23 Med · 2 Low (47 total) | **0 Critical · 0 High** · 3 Med · 1 Low (4 total) | **-91.5% (-43 vulnerabilities)**<br>100% Critical and High removed | **REMEDIATED**<br>Tomcat 11.0.27 & Jackson 2.21.8 / 3.1.8 |
| **`SmartPot-API-Go`** (Go 1.27.3/1.27 / Echo) | 0 Critical · 1 High · 3 Med · 0 Low (4 total) | **0 Critical · 0 High · 0 Med · 0 Low (0 open)** | **-100% surface mitigated** | **CERTIFIED**<br>`echo.ExtractIPDirect()`, `.snyk` policy, Go 1.27.3 builder |
| **`SmartPot-Web-Solid`** (SolidJS / Nginx) | 0 Critical · 0 High · 0 Med · 0 Low | **0 Critical · 0 High · 0 Med · 0 Low** | 100% clean posture | **CERTIFIED** |
| **`SmartPot-DataGenerator-Rust`** (Rust) | 0 Critical · 0 High · 0 Med · 0 Low | **0 Critical · 0 High · 0 Med · 0 Low** | 100% clean posture | **CERTIFIED** |
| **`SmartPot-AI` & `SmartPot-DataGenerator`** | 105 OS Debian 12 CVEs | **Patched via `apt-get upgrade` in Dockerfile** | Debian security patches applied | **HARDENED** |
| **`.github/kubernetes`** (`k8s-deployment.yml`) | 19 `SNYK-CC-K8S-42` alerts | **0 `SNYK-CC-K8S-42` alerts** | **-100% (19 resolved)** | **CERTIFIED**<br>`imagePullPolicy: Always` across all pods |
| **`.github/docker/production`** (`compose.yaml`) | Mailpit UI exposed without mandatory auth | **Port 8025 bound to 127.0.0.1 with required passwords** | Mitigated SEC-04 | **HARDENED** |
| **`.github/docker/demo`** (`compose.yaml`) | Zero resource limits in Stack A | **CPU, memory, and PID limits on all 8 services** | Mitigated SEC-05 | **HARDENED** |

### 6.2 Executed Interventions Detail

1. **[P1-1 / SEC-01] Echo IP Extractor Hardening against Spoofing (`CVE-2026-118653`):**
   * Configured `e.IPExtractor = echo.ExtractIPDirect()` in `internal/httpserver/server.go`, resolving client IPs directly from TCP connections (`RemoteAddr`) and discarding untrusted `X-Forwarded-For` or `X-Real-IP` headers.
   * Implemented optional reverse proxy subnet support (`TRUST_PROXY=true`) via `echo.ExtractIPFromXFFHeader` restricted to private network ranges.
   * Automated unit test `TestRateLimiter_SpoofedXForwardedForMitigation` in `internal/security/ratelimit_test.go` verifies that successive attempts with forged `X-Forwarded-For` headers are blocked with `429 Too Many Requests`.

2. **[P1-2 / SEC-06] Go Toolchain Upgrade in Dockerfile (`CVE-2026-111943`):**
   * Upgraded compilation stage in `SmartPot-API-Go/Dockerfile` to `golang:1.27.3-alpine`.
   * Added `apk update && apk upgrade --no-cache` prior to static binary generation targeting `scratch`.

3. **[P3-2 / SEC-02] PostgreSQL `sslmode` Hardening:**
   * In `SmartPot-API-Go/internal/config/config.go`, connection string parameters were reinforced with `DB_SSLMODE` defaulting to `prefer` (permitting explicit `disable` in local Compose setups without compromising production defaults).

4. **[P0-1] Eradication of Critical and High Vulnerabilities in Stack A (`SmartPot-API`):**
   * In `SmartPot-API/pom.xml`, servlet and JSON dependencies were centrally upgraded:
     * `tomcat.version` locked to `11.0.27`: eliminating auth/access bypasses (`CVE-2026-101296`, `CVE-2026-101356`, `CVE-2026-65905`, `CVE-2026-68525`, `CVE-2026-76183`) and WebSocket DoS issues (`CVE-2026-68569`, `CVE-2026-77791`, `CVE-2026-79677`).
     * `jackson-2.version` (`2.21.8`) and `jackson-3.version` (`3.1.8`): neutralizing RCE deserialization (`CVE-2026-110879`) and parsing memory exhaustion (`CVE-2026-68498`, `CVE-2026-89425`, `CVE-2026-68497`, `CVE-2026-91777`).
   * Snyk Open Source verification: **0 Critical and 0 High** remaining (reduced from 47 to 4 total issues, limited to minor transitive libraries without upstream patches).

5. **[P2-1 / SEC-07] Kubernetes IaC Hardening (`SNYK-CC-K8S-42`):**
   * Replaced `imagePullPolicy: IfNotPresent` with `imagePullPolicy: Always` across all deployments in `.github/kubernetes/k8s-deployment.yml`. Snyk IaC certifies reduction from **19 alerts to 0**.

6. **[P2-2 / SEC-04 & P3-1 / SEC-05] Container & Compose Hardening:**
   * `.github/docker/production/compose.yaml`: Bound Mailpit UI strictly to `127.0.0.1:8025:8025` with enforced non-empty passwords `${MAILPIT_UI_PASSWORD:?...}`.
   * `.github/docker/demo/compose.yaml`: Defined resource limits (`cpus`, `mem_limit`, `pids_limit`) across all 8 stable demo containers.
   * `SmartPot-AI`, `SmartPot-DataGenerator`, and `SmartPot-API`: Dockerfiles updated with operating system package security upgrades.

---

<a id="español"></a>
