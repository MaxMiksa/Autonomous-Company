# scripts/session-brief.py · [[session-brief-hook]]

SessionStart hook'u: oturum başlarken ölçülen git/repo durumunu ve resume/preflight bilgisini doğrudan bağlama enjekte eden, bayatlayamayan brifing betiği.

- sh · function · L24-L28 — Runs a shell command safely, returning stripped stdout or empty string on any failure/timeout.
- main · function · L31-L78 — Git durumu, stash, brief-extra.sh çıktısı ve resume/preflight dosya yaşlarını toplayıp tek bir brifing metni olarak stdout'a basar.
