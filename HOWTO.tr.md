# Argus nasıl kurulur ve kullanılır

Her platform için adım adım. 🇬🇧 [English](HOWTO.md)

Adımları Ekim 2026'da her platformun kendi resmî dokümanlarına göre kontrol ettim (bağlantılar en altta). Menüler ve yollar değişebilir; bir adım ekrandakiyle uyuşmuyorsa platformun kendi sayfasına güven. ChatGPT ve Claude.ai'a ben yükleme denemedim, o adımlar yardım merkezlerinden geliyor.

## Başlamadan önce

Skill klasörü lazım: bu reponun içindeki `argus/` dizini (içinde `SKILL.md` olan).

```bash
git clone https://github.com/ardakaano/argus.git
cd argus
```

ChatGPT ve Claude.ai'da klasör kopyalamak yerine ZIP yüklenir:

```bash
make zip        # kökünde argus/ klasörü olan argus-skill.zip üretir
```

Platformunu seç:

| Kullandığım | Git |
|---|---|
| OpenCode | [OpenCode](#opencode) |
| Claude Code | [Claude Code](#claude-code) |
| Codex (CLI veya IDE) | [OpenAI Codex](#openai-codex) |
| Hermes | [Hermes](#hermes) |
| ChatGPT | [ChatGPT](#chatgpt) |
| Claude.ai | [Claude.ai](#claudeai) |

## 30 saniyelik test (her platform)

Kurduktan sonra şunu gönder:

```text
Argus: küçük bir alışkanlık takip uygulaması için hızlı bir lansman planı çıkar.
```

Skill çalışıyorsa cevap:

- en üstte, URL vermediğin için **yalnızca hipotez** olduğunu söyler ve URL gönderirsen araştırmayı teklif eder,
- **kill criteria** ile bir **plana karşı** bölümü içerir,
- **48 saatlik bir deney** ve "henüz gönderilmedi" diye işaretli bir taslak gönderi verir,
- kaynak, fiyat ya da dönüşüm oranı uydurmaz.

Bunun yerine genel bir pazarlama kontrol listesi aldıysan skill yüklenmemiştir. Platform bölümündeki "görünmüyorsa" satırına bak.

---

## OpenCode

**Kurulum**

```bash
mkdir -p ~/.config/opencode/skills
cp -R argus ~/.config/opencode/skills/
```

Sadece bir proje için: onun yerine o projede `.opencode/skills/argus` altına kopyala. OpenCode ayrıca `~/.claude/skills`, `~/.agents/skills`, `.claude/skills` ve `.agents/skills` dizinlerini de okur; yani Claude Code ya da Codex için koyduğun kopya da bulunur.

**Kullanım**

```text
@argus https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

`@argus` yazmak skill'i senin yüklemeni sağlar. OpenCode açıklamaya bakıp kendisi de seçebilir.

**Güncelleme**: `git pull`, sonra kopyayı yenile: `rm -rf ~/.config/opencode/skills/argus && cp -R argus ~/.config/opencode/skills/`.
**Kaldırma**: o klasörü sil.

**Görünmüyorsa**: skill kimliği klasör adıdır ve büyük/küçük harfe duyarlıdır; klasör `argus` olmalı. Aynı kimliği tanımlayan daha öncelikli bir kaynak olmadığını ve ajanının `skill` izninin `deny` olmadığını kontrol et.

---

## Claude Code

**Kurulum**

```bash
mkdir -p ~/.claude/skills
cp -R argus ~/.claude/skills/
```

Tek bir repo için (git ile ekibinle paylaşılır): `.claude/skills/argus`. Tekrar kopyalamadan `git pull` ile güncelleme istersen bağlantı kur: `ln -s "$PWD/argus" ~/.claude/skills/argus`.

**Kontrol**: `/skills` çalıştır, Argus listede olmalı. Claude Code değişiklikleri yeniden başlatmadan alır; oturum açılırken `~/.claude/skills/` yoksa `/reload-skills` çalıştır.

**Kullanım**

```text
/argus https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

Ya da düz cümleyle sor; istek uyunca Claude kendisi yükler.

**Güncelleme**: çek ve yeniden kopyala (bağlantı kurduysan gerek yok). **Kaldırma**: `~/.claude/skills/argus/` sil.

**Görünmüyorsa**: kurulumunu `/doctor` kontrol eder. `SKILL.md` frontmatter'ı dosyanın ilk satırında başlamalı. Argus'u claude.ai'a da yüklediysen ve aynı hesapla giriş yaptıysan, senkronlanan kopya `claude.ai sync` altında görünür.

---

## OpenAI Codex

**Kurulum**

```bash
mkdir -p ~/.agents/skills
cp -R argus ~/.agents/skills/
```

Tek bir repo için: `.agents/skills/argus`. Codex çalışma dizininden repo köküne kadar tarar.

**Kontrol ve kullanım**: `/skills` çalıştır (ya da `$` yaz) ve `argus`'u seç, ya da an:

```text
$argus https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

Codex açıklamaya bakıp kendisi de seçer. Yeni skill'leri otomatik algılar; görünmezse Codex'i yeniden başlat.

**Güncelleme**: yeniden kopyala. **Kaldırma**: klasörü sil.

---

## Hermes

**Kurulum**

```bash
mkdir -p ~/.hermes/skills
cp -R argus ~/.hermes/skills/
```

**Kontrol**: `hermes skills list | grep argus`, ya da sohbette `/skills`. Yeni skill **yeni** oturumlarda kullanılabilir; hemen istersen `/reset` ile oturumu sıfırla.

**Kullanım**

```text
/argus https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

Yüklü her skill bir slash komutudur; Hermes'e düz cümleyle "bu skill'i kullan" da diyebilirsin.

**Güncelleme**: yeniden kopyala. **Kaldırma**: klasörü sil.

Hermes dokümanına göre URL'den de kurabilir (`hermes skills install <SKILL.md-url>`). Bunu bu repoyla denemedim, güvenilir yol yukarıdaki kopyalamadır.

---

## ChatGPT

ChatGPT'de skill'ler uygun Business, Enterprise, Healthcare ve Edu planlarında var; tek başına skill'ler ChatGPT masaüstü uygulamasında çalışıyor. **Skills** görünmüyorsa planın ya da çalışma alanın desteklemiyor olabilir, ya da yönetici yüklemeyi kapatmıştır.

**Kurulum**

1. `make zip` çalıştır.
2. ChatGPT'de kenar çubuğundan **Plugins**'i, sonra **Skills** sekmesini aç.
3. **Create**'e, sonra **Upload from your computer**'a bas ve `argus-skill.zip`'i seç.
4. ChatGPT yüklemeyi tarar. **Needs Review** derse gösterdiğini oku ve onayla. **Blocked** ise kullanılamaz.

**Kullanım**: `@` yaz ve `argus`'u seç, ya da doğrudan sor; ChatGPT açıklamaya bakıp seçebilir.

```text
@argus https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

**Güncelleme**: yeni ZIP'i yükle. **Kaldırma**: Skills sayfasından sil.

**Planında Skills yoksa**: `SKILL.md` içeriğini bir Project'in talimatlarına yapıştır, `references/` dosyalarını ekle ve "Argus talimatlarını uygula" diye başla. Skill yine çalışır ama betik çalıştırma, açık araçlarına bağlıdır.

---

## Claude.ai

Free, Pro, Max, Team ve Enterprise'ta var. **Code execution and file creation** açık olmalı (Settings > Capabilities; Team ve Enterprise'ta sahibi Organization settings > Plugins & skills'ten açar).

**Kurulum**

1. `make zip` çalıştır. ZIP'in kökü `argus/` klasörü olmalı, bu komut öyle üretir.
2. **Customize > Skills**'i aç.
3. **+**'ya, sonra **Create skill**'e, sonra **Upload a skill**'e bas ve `argus-skill.zip`'i seç.
4. Skill'i **aç** (toggle).

**Kullanım**: ilk seferde açıkça iste.

```text
Argus skill'imi kullanarak https://example.com adresini indie SaaS kurucuları için analiz et, bütçe 300 $.
```

**Güncelleme**: yeni ZIP'i yükle. **Kaldırma**: skill'i aç, kapat, sonra "..." > Delete. Aynı hesapla Claude Code kullanıyorsan, açık skill'ler oraya da senkronlanır.

**Yükleme hata verirse**: yardım merkezi şu nedenleri sayıyor: ZIP çok büyük, klasör adı skill adıyla uyuşmuyor, `SKILL.md` yok, ad veya açıklamada geçersiz karakter. Dikkat edilecek bir şey: Anthropic'in "How to create custom skills" yazısı description için hâlâ 200 karakter sınırı diyor, Agent Skills spec'i ise 1024 izin veriyor. Argus'un description'ı yaklaşık 590 karakter. Uzunluktan reddedilirse `SKILL.md` içindeki `description` satırını ~200 karaktere kısalt, Türkçe tetikleyicileri tut.

---

## İsteğe bağlı: rapor betiği

Argus bulgularını JSON olarak kaydedip markdown ya da tek dosyalık HTML rapora çevirebilir. Python 3.10+ yeter, başka bir şey gerekmez. Kabuğu olan ajanlar (OpenCode, Claude Code, Codex, Hermes; ChatGPT ve Claude.ai'da kod çalıştırma açıksa) Full modda bunu senin yerine çalıştırır. Elle:

```bash
python3 argus/scripts/render_report.py --template > bulgular.json
python3 argus/scripts/render_report.py bulgular.json --check --strict
python3 argus/scripts/render_report.py bulgular.json --lang tr -o plan.html
```

## Bilmekte fayda var

- **Argus yalnızca sen URL verirsen araştırır.** URL verirsen araştırır ve tarihli kaynak gösterir. Vermezsen, ajanının web araçları olsa bile hiç arama ya da sayfa çekme yapmaz; yalnızca hipotez içeren bir plan verir ve linki gönderirsen araştırmayı teklif eder.
- **Quick veya Full**: kısa soruya kısa cevap verir. Tam sürüm için "plan", "denetim" ya da "30 günlük" iste.
- **Senin yerine hiçbir şey gönderilmez.** Gönderi, e-posta ve DM'ler senin onayladığın taslaklardır.
- **Dil**: yazdığın dilde cevap verir.

## Kaynaklar

- OpenCode V2 skills: https://opencode.ai/v2/docs/skills/
- Claude Code skills: https://code.claude.com/docs/en/skills
- OpenAI, build skills (ChatGPT ve Codex): https://learn.chatgpt.com/docs/build-skills
- OpenAI, skills in ChatGPT: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- Hermes, working with skills: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills
- Claude help center, use skills: https://support.claude.com/en/articles/12512180-use-skills-in-claude
- Claude help center, create custom skills: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
