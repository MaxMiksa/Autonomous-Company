# scripts/compact-preflight.py · [[compact-ritual-tooling]]

PreCompact hook'u otomatik/manuel koşan, compact öncesi açık kalemleri (resume tazeliği, git riskleri, proje ek kontrolleri) sayıp raporlayan ve otomatik compact'i resume hazır değilken bir kez erteleyen ön-kontrol betiği.

- sh · function · L52-L56 — Runs a shell command safely, returning its trimmed stdout or empty string on any failure/timeout.
- hook_payload · function · L59-L68 — PreCompact hook'unun stdin'den verdiği JSON payload'ı okur; elle koşulduğunda (tty) boş sözlük döndürerek erteleme yolunu hiç açmaz.
- resume_lint_gecer_mi · function · L71-L87 — compact-resume-lint.py'yi subprocess ile koşup exit 0'a göre resume içeriğinin yeşil olup olmadığını ve ilk hata satırını döndürür; lint kurallarını tek dosyada tutarak kural ayrışmasını önler.
- resume_durumu · function · L90-L100 — Resume dosyasının tazeliğini iki koşulun birlikte sağlanmasıyla belirler: mtime 3 saatten genç VE lint yeşil; aksi halde bayat/yok/lint-kırmızı nedenini döndürür.
- repo_report · function · L103-L120 — Inspects a git repo and counts open risks (unpushed commits, uncommitted changes, stashes) to flag what a compact could lose.
- main · function · L123-L193 — Tüm ön-kontrolü toplar: git köklerindeki riskleri, resume durumunu ve proje ek kontrollerini sayıp rapor dosyasına yazar; otomatik compact'i resume hazır değilken marker ile bir kez erteleyip karar JSON'u basar.
