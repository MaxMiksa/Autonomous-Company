# scripts/ops/rfq-send.py · [[rfq-send-pipeline]]

CLI that sends anonymous OPEX RFQ emails to vendors, fail-closed on §15 sponsor approval, daily/total caps, and anonymity scan.

- _load_key · function · L61-L82 — API anahtarını env → runtime.env → macOS Keychain sırasıyla yükler ve env'e yazar.
- _app_dir · function · L85-L87 — Script'in iki üst dizinini (repo kökü) mutlak yol olarak döndürür.
- _air · function · L91-L103 — Airtable REST isteğini (GET/PATCH) yürütüp JSON yanıtını döndüren genel yardımcı.
- _record · function · L106-L107 — Tek bir Airtable kaydını ID ile çeker.
- _all_rows · function · L110-L121 — Tablodaki tüm kayıtları offset sayfalama ile toplar.
- _sponsor_ok · function · L125-L126 — §15 kapısı: 'Sponsor İzni' checkbox'ı tam olarak True ise izin verir, aksi halde fail-closed reddeder.
- _opted_out · function · L129-L130 — Vendor'ın opt-out bayrağının set edilip edilmediğini döndürür.
- _already_sent · function · L133-L134 — Kaydın daha önce gönderilip gönderilmediğini (Durum veya Gönderim TS) kontrol eder.
- _email_of · function · L137-L139 — Kanal alanından ilk e-posta adresini regex ile çıkarır, yoksa None.
- _caps_now · function · L142-L152 — Bugünkü ve toplam gönderim sayısını UTC tarihine göre hesaplar.
- render · function · L155-L163 — Şablon adından scope'u çözüp vendor kümesi için subject/plain-text/HTML içeriği üretir.
- anonymity_scan · function · L166-L171 — Render edilen metinde denylist (wowcar) sızıntısı olup olmadığını arar.
- decide · function · L174-L197 — Bir vendor kaydını opt-out, never-twice, e-posta varlığı, anonimlik, cap'ler ve §15 izni sırasıyla değerlendirip ALLOW/REFUSE kararı döndürür.
- send_fe · function · L201-L226 — Delivers the rendered RFQ email to ForwardEmail's /v1/emails endpoint using Nodemailer JSON format with Basic auth.
- _mark_sent · function · L229-L232 — Gönderim sonrası kaydı 'Gönderildi' ve zaman damgası ile PATCH'ler.
- main · function · L236-L278 — CLI girişi: --report ile cap/eligibility özeti, --record ile tek vendor kararı ve --send ile gerçek gönderim sonrası kaydı işaretler.
