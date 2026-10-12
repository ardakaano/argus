<p align="center">
  <img src="assets/logo.svg" alt="Argus" width="380">
</p>

<h3 align="center">Lansmanın üzerinde yüz göz.</h3>

Yunan mitolojisinde Argus Panoptes, yüz gözlü bekçiydi ve gözlerinden bir kısmı her zaman açıktı. Bu Agent Skill, yapay zeka ajanına SaaS, uygulama veya bağımsız ürün lansmanında aynı alışkanlığı kazandırır: ürünü, müşterileri, rakipleri, toplulukları ve kanalları birlikte izler ve planın yanlış olduğunu gösteren kanıta karşı bir gözünü hep açık tutar.

Ürününe bir kontrol listesi değil, bir dağıtım stratejisi lazım. Argus on beş kanal yerine üç kanal seçer, kaynaklarını gösterir ve doğrulayamadığını açıkça söyler.

[English README](README.md)

## Ne üretir

- Ürün ve konumlandırma denetimi
- Birincil ve ikincil ideal müşteri profilleri
- Rakip ve topluluk araştırması, **kanıt defteri** ile (kaynak URL'si + erişim tarihi)
- **Çürütücü kanıt ve durdurma kriterleri**: plan yanlışsa bunu baştan görürsün
- Tanıtımın yasak olduğu yerde asla tanıtım önermeyen ağırlıklı kanal sıralaması
- Haftalık dur/devam kapılarıyla 30 günlük sprint
- Konumlandırma cümlesi, üç kanca, lansman gönderisi ve spam olmayan bir yanıt taslağı
- Ölçülebilir beş deney; en az biri 48 saat içinde başlayabilir

İki mod: **Quick** (tek ekran) ve **Full** (hepsi). Kullanıcının diliyle yanıt verir.

## Kurulum

```bash
git clone https://github.com/ardakaano/argus.git && cd argus
```

Sonra içteki `argus/` klasörünü (skill'in kendisi) ajanının skills dizinine kopyala. Klasör adı skill adıyla (`argus`) aynı olmalı.

```bash
# OpenCode
mkdir -p ~/.config/opencode/skills && cp -R argus ~/.config/opencode/skills/
# Claude Code
mkdir -p ~/.claude/skills && cp -R argus ~/.claude/skills/
# OpenAI Codex
mkdir -p ~/.agents/skills && cp -R argus ~/.agents/skills/
```

Diğer ajanlar ve proje kapsamlı konumlar: [`argus/references/platforms.md`](argus/references/platforms.md).

## Kullanım

```text
/argus https://example.com adresini TR pazarı ve 5.000 TL bütçeyle analiz et.
/argus Web erişimi yok: B2B takvim uygulaması için hipotez odaklı lansman planı hazırla.
/argus İlk 20 kullanıcıyı nereden bulabilirim? Ürün: küçük bir onboarding analitik aracı.
```

Web erişimi yoksa Argus, açıkça **yalnızca hipotez** etiketli bir plan üretir; URL'ni denetlemiş gibi davranmaz.

## Rapor oluşturucu (isteğe bağlı)

Python 3.10+, bağımlılık yok:

```bash
python3 argus/scripts/render_report.py --template > bulgular.json
python3 argus/scripts/render_report.py bulgular.json --lang tr -o plan.md
python3 argus/scripts/render_report.py bulgular.json --lang tr -o plan.html   # tek dosyalık HTML rapor
python3 argus/scripts/render_report.py bulgular.json --check --strict
```

HTML rapor tek ve bağımsız bir dosyadır: satır içi CSS, script yok, dış istek yok, koyu/açık tema, yazdırmaya hazır. Ekibe gönderebilir ya da PDF'e yazdırabilirsin.

Türkçe örnekler (ürün kurgusaldır): [`example-report.tr.html`](argus/examples/example-report.tr.html) ve [`example-report.tr.md`](argus/examples/example-report.tr.md).

## Çalışıyor mu? Eval'ler

[`evals/`](evals/README.md) altında dört davranış senaryosu var: canlı URL denetimi, web'siz hipotez modu, prompt-injection içeren bir sayfa ve tanıtımı yasaklayan forumla ilgili Türkçe bir istek. Her biri skill'li ve skill'siz koşturuldu. Sonuçlar: [`evals/RESULTS.md`](evals/RESULTS.md).

## Geliştirme

```bash
make test       # 64 test
make examples   # örnek raporları yeniden üret
make zip        # Claude.ai için argus-skill.zip
```

## Yazar

[Arda Kaan Özcan](https://github.com/ardakaano) tarafından geliştirildi.

## Lisans

MIT. Bkz. [LICENSE](LICENSE). `assets/` altındaki logo © Arda Kaan Özcan, aynı lisans altındadır.
