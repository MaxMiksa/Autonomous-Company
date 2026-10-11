# RUNBOOK — Container içinde jcode + Claude (Sonnet 5.5) ajanı çalıştırma

> Hedef okur: Hetzner/Coolify/container uzman oturumu ("Efe"). AutoCompany prod
> loop'unda 2026-10-11 itibarıyla ÇALIŞAN düzenin damıtılmış hâli; her madde
> `Dockerfile`, `docker-entrypoint.sh` ve `scripts/core/auto-loop.sh`'tan alınmıştır.
> Kendi container'ına uyarlarken komut sözdizimini Context7'den (jcode / Docker) teyit et.

## 0. Ne kuruyoruz

- **jcode** (https://github.com/1jehuang/jcode): tek binary ajan harness'i. `jcode -p claude
  -m <model> run "<istem>" --ndjson` ile headless koşar, olayları ndjson olarak basar.
- **Kimlik**: Claude Max aboneliğinin uzun ömürlü OAuth token'ı (`sk-ant-oat…`, operatörün
  makinesinde `claude setup-token` ile üretilir). API anahtarı DEĞİL; "$" rakamları liste
  fiyatı eşdeğeri tahmindir, fatura değildir.
- **Model**: `claude-sonnet-5-5`, efor `high` (cache-read fiyatı Sonnet 5'in yarısı).

## 1. İmaj (Dockerfile)

```dockerfile
FROM node:22-trixie-slim            # jcode GLIBC >= 2.39 ister; bookworm (2.36) ÇALIŞMAZ
ARG JCODE_VERSION=v0.94.0           # v0.64.2 bilinmeyen model id'yi SESSİZCE opus-5'e çevirdi
RUN set -eu; cd /tmp; \
    curl -fsSLO "https://github.com/1jehuang/jcode/releases/download/${JCODE_VERSION}/jcode-linux-x86_64.tar.gz"; \
    curl -fsSLO "https://github.com/1jehuang/jcode/releases/download/${JCODE_VERSION}/SHA256SUMS"; \
    grep "jcode-linux-x86_64.tar.gz" SHA256SUMS | sha256sum -c -; \
    mkdir -p /opt/jcode; tar xzf jcode-linux-x86_64.tar.gz -C /opt/jcode; chmod +x /opt/jcode/*; \
    ln -s /opt/jcode/jcode-linux-x86_64 /usr/local/bin/jcode; rm -f /tmp/jcode-linux-* /tmp/SHA256SUMS
ENV JCODE_NO_TELEMETRY=1
```

Notlar: tarball bir başlatıcı script + `.bin` çiftidir, ikisi yan yana kalmalı ve symlink
başlatıcıya bakmalı. `python3` ve `jq` imajda olmalı (token sarma ve olay ayrıştırma için).
Non-root kullanıcı (`app`, uid 10001) ile koş.

## 2. Boot (entrypoint) — jcode'un üç sessiz ihtiyacı

```sh
export JCODE_NO_TELEMETRY=1
export JCODE_HOME=/app/logs/.jcode        # KALICI volume; container fs her deploy'da sıfırlanır
mkdir -p "$JCODE_HOME"; chmod 700 "$JCODE_HOME"
# (a) Claude Code kimliğine güven — tek seferlik onay, idempotent ekle
grep -q claude_code_native_credentials "$JCODE_HOME/config.toml" 2>/dev/null || \
  printf '[auth]\ntrusted_external_sources = ["claude_code_native_credentials"]\n' >> "$JCODE_HOME/config.toml"
# (b) Yerel hafıza/embedding kapalı (~270 MB RSS ve run'lar arası sızan bağlam)
grep -q '^\[features\]' "$JCODE_HOME/config.toml" 2>/dev/null || \
  printf '\n[features]\nmemory = false\nswarm = false\nmermaid = false\n\n[agents]\nmemory_sidecar_enabled = false\n' >> "$JCODE_HOME/config.toml"
# (c) MCP: jcode YALNIZ kendi $JCODE_HOME/mcp.json dosyasını okur (repo .mcp.json'ı değil), stdio
#     python3 scripts/core/jcode-mcp-config.py --src .mcp.json --dest "$JCODE_HOME/mcp.json"
```

`CLAUDE_CODE_OAUTH_TOKEN` yoksa boot'ta FATAL ver (bizde Coolify env katmanında durur;
`runtime.env` dosyasında değil). Değeri hiçbir log/çıktıya basma.

## 3. Çağrı kalıbı (her ajan koşusu)

Token sarma **alt süreçte** yapılır; global env'de HAM `sk-ant-oat…` kalır (rollback'te
`claude` CLI ham token ister; globalde sarılı blob 401 üretir).

```sh
(
  cd "$PROJECT_DIR" || exit 1
  case "${CLAUDE_CODE_OAUTH_TOKEN:-}" in sk-ant-oat*)
    _exp=$(( ($(date +%s) + 86400*300) * 1000 ))
    export CLAUDE_CODE_OAUTH_TOKEN=$(python3 -c 'import json,os,sys; print(json.dumps({"claudeAiOauth":{"accessToken":os.environ["CLAUDE_CODE_OAUTH_TOKEN"],"refreshToken":"","expiresAt":int(sys.argv[1]),"scopes":["user:inference"],"subscriptionType":"max"}}))' "$_exp")
  ;; esac
  export JCODE_ANTHROPIC_REASONING_EFFORT=high
  jcode -p claude -C "$PROJECT_DIR" -m claude-sonnet-5-5 \
    --disabled-tools "$JCODE_TOOLS_DENY" \
    --mcp-tools eager \
    run "$PROMPT" --quiet --no-update --no-selfdev --ndjson
) > events.ndjson 2> stderr.txt
```

- `--mcp-tools eager`: v0.87+ varsayılanı `auto`, belli eşikten sonra MCP araçlarını
  `mcp_search` arkasına gizler; isimle çağıran istemler kör kalır.
- `--disabled-tools`: araç ön-ekini küçültür (bizde ~85% tasarruf); `--tools` izin listesi
  TOTAL'dir (MCP dahil), eksik sayarsan koşu ölür — opt-in bırak.
- İstem argv ile gidiyorsa 126 000 bayt üstünü reddet (kernel tek-arg sınırı 131 072).
- Zaman aşımı bekçisi şart (bizde `CYCLE_TIMEOUT_ACTIVE`); süreç grubunu öldür.
- Hata olayları STDOUT'taki ndjson'da (`"type":"error"`), stderr'de değil — ikisini birleştir.

## 4. Koşu sonrası doğrulama (atlanırsa sessiz yanlışlık)

```sh
jq -r 'select(.type=="done") | .model'          events.ndjson   # == istenen model, BİREBİR
jq -r 'select(.type=="done") | .status_detail'  events.ndjson   # "instead of requested" içermemeli
python3 scripts/core/jcode-final-text.py events.ndjson           # done.text TEK blok; son metin bu
```

Model farklıysa koşuyu BAŞARISIZ say (sessiz ikame hem maliyeti hem muhakeme seviyesini
değiştirir). Katalog statik değildir; boot'ta `jcode model list -p claude` ile merdivendeki
modelleri kontrol et, ama asıl otorite `done.model`'dir.

## 5. Kanarya (yeni imaj / yeni model / yeni jcode sürümünde ZORUNLU)

Scratchpad'deki `canary-model.sh` deseni: geçici `-C` dizini, istem "Reply with exactly one
word: PONG", yukarıdaki sarma + bayraklar; çıktıda `done.model`, `status_detail`, usage ve
hata olaylarına bak. 2026-10-11 dersi: v0.64.2'de `-m claude-sonnet-5-5` → `done.model =
claude-opus-5`, status_detail BOŞ. Kontrol koşusu olarak bilinen bir modelle (sonnet-5) tekrar et.

## 6. Maliyet ölçümü

`engine-usage-cost.py` done olayındaki usage'ı liste fiyatıyla çarpar: Sonnet 5 = 5.5 =
2 / 10 $/M; 5.5 cache-read 0,05×; bilinmeyen model en pahalı satır ×5 (bütçe kapısını
sahte tetikler → tabloya ekle). Tur başına cache-read hacmi asıl sürücüdür; tur sayısını
sınırla (turn-audit / turn-bloat-brake).

## 7. Tuzaklar (yaşanmış)

- Sürüm atlarken (30 sürüm birden) yeniden doğrula: stdin/argv taşıma, `--disabled-tools`,
  done olayı şeması, MCP maruziyeti. Bizde şema aynı kaldı, MCP varsayılanı değişti.
- `set -e` + pipefail altında tek kötü satır = restart loop; her entrypoint satırını koru.
- OpenAI kimliği DOSYA (`$JCODE_HOME/openai-auth.json`) → kalıcı volume şart.
- Deploy sırası: ajan çalışırken redeploy ETME; yarım koşu 5× fiyatlanabilir.
- Teşhis çıktıları (`ps`, `env`, `inspect`) argv'den secret sızdırır; yalnız gerekli kolon.
- Bu runbook jcode'u anlatır; prod loop'un bütçe kapıları, direktif ve OPREQ makinesi
  AutoCompany'ye özgüdür, başka container'a taşınmaz.

## 8. Alternatif yol: `claude` CLI (Hetzner-Efe saha notu, 2026-10-11)

Hedef uygulama zaten `claude --print` çağırıyorsa jcode'a gerek yok; Efe'nin SAP stok uygulamasında
(stok.appricode.tr, Coolify, cx23, 1 GiB/1 CPU container) bu yol kuruldu ve ölçüldü:

- **İmaj:** `python:3.12-slim-bookworm` + Node 22 ikilisi (`node:22-bookworm-slim`'den COPY) +
  `@anthropic-ai/claude-code` npm ile sürüm sabit (`deploy/claude-cli.version`). Bookworm claude CLI için
  yeterli; GLIBC sorunu yalnız jcode'da.
- **Env:** `DISABLE_AUTOUPDATER=1`, `DISABLE_TELEMETRY=1`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`;
  `CLAUDE_CODE_OAUTH_TOKEN` operatörün `claude setup-token` (1 yıl) çıktısı, Coolify env katmanında, **HAM**
  (claudeAiOauth sarmalaması YALNIZ jcode içindir); model `ANTHROPIC_MODEL` env'den (koda yazılmaz). HOME kalıcı
  olmasa da CLI her deploy'da sıfır HOME ile sorunsuz çalıştı.
- **`--bare` KULLANMA:** dokümanda "scripted -p için kanonik" denir ama API anahtarı / apiKeyHelper ister ve
  OAuth'u kapatır; abonelik token'ı yolunda çalışmaz.
- **Çağrı:** `claude --print --output-format json --strict-mcp-config --mcp-config <dosya> --allowedTools …
  --max-turns N`. Alt sürece env geçiren bir whitelist varsa `CLAUDE_CODE_OAUTH_TOKEN` ve `ANTHROPIC_MODEL`
  listede olmalı (Efe'de eksikti, ilk arıza buydu).
- **Kanarya:** `claude -p "Sadece PONG yaz." --output-format json --max-turns 1` → `result`, `is_error`,
  `modelUsage` anahtarı (model adı birebir), `total_cost_usd` (liste eşdeğeri). Ölçülen: Haiku 4.5, 0,0156 $, rc 0.
- **Gerçek koşu:** uygulama → claude → tek stdio MCP sunucusu; 5,4 sn, araç kullanımıyla cevap. Tur/usage
  ayrıntısı uygulama yalnız metin döndürdüğü için ölçülmedi; ölçmek istiyorsan JSON çıktısındaki `usage` ve
  `num_turns` alanlarını logla.
- **Runbook dışı ama deploy'u 11 saat düşüren hata:** `/health` dış servisi (Airtable, 4 tablo) tarıyordu,
  16-20 sn; Dockerfile HEALTHCHECK 3 sn → sürekli unhealthy/503. Sağlık ucu ucuz ve yerel olmalı.
- Coolify API deploy logunu boş döndürebiliyor; UI'dan oku.
