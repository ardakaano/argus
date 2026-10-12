# Argus 👁️

**Lansmanın üzerinde yüz göz.**

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
python3 argus/scripts/render_report.py bulgular.json --check --strict
```

Türkçe örnek rapor: [`example-report.tr.md`](argus/examples/example-report.tr.md). Ürün kurgusaldır.

## Geliştirme

```bash
make test       # 43 test
make examples   # örnek raporları yeniden üret
make zip        # Claude.ai için argus-skill.zip
```

## Lisans

MIT. Bkz. [LICENSE](LICENSE).
