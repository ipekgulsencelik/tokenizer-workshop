# Guide

Bu doküman, `tokenizer-workshop` projesine katkı verecek öğrenciler için hazırlanmıştır. Amaç; projeyi locale almak, `uv` ile çalıştırmak, kendi branch'inde geliştirme yapmak, değişiklikleri push etmek ve Pull Request (PR) açmak için ortak bir çalışma standardı oluşturmaktır.

Bu repo için önerilen çalışma modeli şudur:

- Ana repo, merkezi çalışma alanıdır.
- Katkı verecek kişi repo'yu kendi hesabına **fork** eder.
- Geliştirmeyi kendi fork'u üzerinde, kendi **feature branch**'inde yapar.
- İşini tamamladıktan sonra ana repo'nun `main` branch'ine **PR** açar.

Bu yaklaşım, hem profesyonel Git/GitHub akışını öğretir hem de ana repo'nun kontrollü kalmasını sağlar.

---

## 1. Projeye katkı yaklaşımı

Bu projede doğrudan `main` branch üzerinde geliştirme yapılmaz.
Her öğrenci kendi branch'inde çalışır ve işini tamamladıktan sonra `main` branch'e Pull Request açar.

Temel akış şöyledir:

1. Repo'yu fork et
2. Kendi fork'unu locale al
3. Projeyi ayağa kaldır
4. Ana repo'yu `upstream` olarak tanımla
5. Kendi branch'ini oluştur
6. Geliştirmeyi yap
7. Testleri çalıştır
8. Commit al
9. Kendi fork'una push et
10. Ana repo'ya Pull Request aç

---

## 2. Gereksinimler

Bu projede temel araçlar şunlardır:

- Git
- Python 3.10+
- `uv`

### `uv` kontrolü

PowerShell'de:

```powershell
uv --version
```

Eğer sürüm dönüyorsa hazırdır.

---

## 3. Repo'yu locale alma

### Önerilen yöntem — Fork ile çalışma

Önce GitHub üzerinden ana repo'yu kendi hesabına **fork** et.
Ardından kendi fork'unu clone et:

```powershell
git clone <YOUR_FORK_URL>
cd tokenizer-workshop
```

Örnek yapı:

- Ana repo: `https://github.com/Burakkylmz/tokenizer-workshop.git`
- Senin fork'un: `https://github.com/<your-username>/tokenizer-workshop.git`

### Alternatif yöntem — Doğrudan erişimin varsa

Eğer repo'ya doğrudan yazma yetkin varsa, teorik olarak ana repo'yu doğrudan clone edebilirsin:

```powershell
git clone <REPO_URL>
cd tokenizer-workshop
```

Ancak eğitim ve PR disiplini açısından önerilen yöntem yine de **fork + branch + PR** akışıdır.

---

## 4. Ana repo'yu `upstream` olarak ekleme

Fork ile çalışıyorsan clone sonrası `origin`, kendi fork'un olur.
Bu durumda ana repo'yu ayrıca `upstream` olarak eklemelisin:

```powershell
git remote add upstream https://github.com/Burakkylmz/tokenizer-workshop.git
```

Kontrol etmek için:

```powershell
git remote -v
```

Beklenen mantık:

- `origin` -> senin fork'un
- `upstream` -> ana repo

Bu ayar önemlidir çünkü ana repo güncellendikçe kendi fork'unu senkronize etmeni sağlar.

---

## 5. Projeyi locale ayağa kaldırma

Repo klasörüne girdikten sonra önce bağımlılıkları senkronize et:

```powershell
uv sync
```

Bu komut:
- `.venv` oluşturur (yoksa)
- `pyproject.toml` ve `uv.lock` dosyasına göre bağımlılıkları kurar
- proje ortamını hazır hale getirir

Ardından proje girişini çalıştır:

```powershell
uv run tokenizer-workshop
```

Bu komut başarılı çalışıyorsa proje temel seviyede ayağa kalkmış demektir.

### Testleri çalıştırma

Tüm testleri çalıştırmak için:

```powershell
uv run pytest -v
```

Belirli bir test dosyasını çalıştırmak için:

```powershell
uv run pytest tests/test_char_tokenizer.py -v
```

---

## 6. Güncel kodu alma

Çalışmaya başlamadan önce local `main` branch'ini güncelle.

### Fork ile çalışıyorsan

Önce ana repo'dan güncel kodu al:

```powershell
git fetch upstream
git checkout main
git merge upstream/main
```

Sonra istersen kendi fork'una da gönder:

```powershell
git push origin main
```

### Doğrudan ana repo ile çalışıyorsan

```powershell
git checkout main
git pull origin main
```

---

## 7. Kendi branch'ini açma

Her geliştirme ayrı branch'te yapılmalıdır.
Branch isimleri açık ve kısa olmalıdır.

Örnek branch isimleri:

- `feature/word-tokenizer`
- `feature/regex-tokenizer`
- `feature/regex-bpe-tokenizer`
- `feature/byte-bpe-tokenizer`
- `test/metrics-improvements`
- `docs/contribution-guide`

Branch oluşturmak ve geçmek için:

```powershell
git checkout -b feature/<your-work-name>
```

Örnek:

```powershell
git checkout -b feature/word-tokenizer
```

---

## 8. Geliştirme sırasında çalışma standardı

Katkı verirken şu prensiplere uy:

- Küçük ve kontrollü değişiklik yap
- Gereksiz dosya ekleme
- Kod ile birlikte test ekle
- Yorum satırları eğitim değerini artırıyorsa ekle
- Mevcut klasör yapısını bozma
- `main` branch'e doğrudan push atma

### Beklenen temel kontrol listesi

Kodunu push etmeden önce şunları kontrol et:

1. Proje çalışıyor mu?
2. İlgili testler geçiyor mu?
3. Yeni eklediğin dosyalar doğru klasörde mi?
4. Gerekliyse `__init__.py` güncellendi mi?
5. Değişiklik açıklanabilir ve küçük parçalara ayrılmış mı?

---

## 9. Dosya değişikliklerini kontrol etme

Durumu görmek için:

```powershell
git status
```

Yapılan değişiklikleri satır bazlı görmek için:

```powershell
git diff
```

---

## 10. Commit alma

Önce dosyaları stage et:

```powershell
git add .
```

Daha kontrollü gitmek istersen belirli dosyaları ekle:

```powershell
git add src/tokenizer_workshop/tokenizers/word_tokenizer.py
git add tests/test_word_tokenizer.py
```

Sonra commit al:

```powershell
git commit -m "Add word tokenizer and tests"
```

### Commit mesajı önerileri

- `Add word tokenizer and tests`
- `Add regex tokenizer implementation`
- `Add byte BPE tokenizer draft`
- `Improve tokenizer metrics tests`
- `Update contribution guide`

Commit mesajı kısa, net ve fiil ile başlamalıdır.

---

## 11. Kendi fork'una push etme

İlk kez push ederken branch'i kendi fork'una gönder:

```powershell
git push -u origin feature/<your-work-name>
```

Örnek:

```powershell
git push -u origin feature/word-tokenizer
```

Sonraki push'larda daha kısa yazabilirsin:

```powershell
git push
```

Buradaki önemli nokta şudur:

- `origin` -> senin fork'un
- push işlemi önce senin fork'una gider
- ana repo'ya doğrudan push atılmaz

---

## 12. Pull Request açma

Push işleminden sonra GitHub'a git ve kendi fork'undaki ilgili branch için PR aç.

PR yönü şu şekilde olmalıdır:

- **base repository:** ana repo (`Burakkylmz/tokenizer-workshop`)
- **base branch:** `main`
- **compare branch:** senin fork'undaki feature branch

Yani PR, senin fork'undan ana repo'ya doğru açılır.

### PR açarken dikkat edilmesi gerekenler

PR açıklaması şu 4 soruya cevap vermelidir:

1. Ne eklendi veya değişti?
2. Neden bu değişiklik yapıldı?
3. Hangi dosyalar etkilendi?
4. Hangi testler çalıştırıldı?

### PR açıklaması için örnek şablon

```md
## Summary
This PR adds the first implementation of the tokenizer.

## Changes
- Added tokenizer implementation
- Added tests
- Updated package exports if needed

## Validation
- Ran `uv run pytest -v`
- Verified local run with `uv run tokenizer-workshop`

## Notes
- This PR focuses only on the current scope
- Follow-up improvements can be added separately
```

### PR başlığı örnekleri

- `Add WordTokenizer implementation`
- `Add RegexTokenizer with tests`
- `Add ByteBPETokenizer baseline`
- `Improve tokenizer evaluation metrics`

---

## 13. PR sonrası revizyon süreci

PR açıldıktan sonra yorum gelebilir. Bu durumda:

1. İstenen değişikliği localde yap
2. Testleri tekrar çalıştır
3. Yeni commit al
4. Aynı branch'e tekrar push et

Örnek:

```powershell
git add .
git commit -m "Address PR review comments"
git push
```

Aynı PR otomatik güncellenir. Yeni PR açman gerekmez.

---

## 14. Contributors görünürlüğü hakkında kısa not

Bir katkının GitHub üzerinde ana repo'nun katkıları içinde görünmesi için en kritik nokta şudur:

- katkıların ana repo'nun `main` gibi default branch'ine merge edilmiş olması gerekir

Sadece fork açmak veya sadece kendi fork'unda commit atmak yeterli değildir.

Ayrıca commit author bilgisinin doğru görünmesi için local Git ayarlarında kullanılan `user.name` ve `user.email` değerleri de doğru olmalıdır.

Kontrol için:

```powershell
git config user.name
git config user.email
```

Gerekirse düzeltmek için:

```powershell
git config user.name "YourGitHubUsername"
git config user.email "your-email@example.com"
```

Bu bölümde görünürlük bazen anlık olmayabilir; merge sonrası GitHub arayüzünde kısa bir gecikme olabilir.

---

## 15. Sık kullanılan komutlar

### Projeyi çalıştır

```powershell
uv run tokenizer-workshop
```

### Tüm testleri çalıştır

```powershell
uv run pytest -v
```

### Tek test dosyası çalıştır

```powershell
uv run pytest tests/test_simple_bpe_tokenizer.py -v
```

### Yeni branch aç

```powershell
git checkout -b feature/<your-work-name>
```

### Durumu kontrol et

```powershell
git status
```

### Commit al

```powershell
git add .
git commit -m "Your commit message"
```

### Push et

```powershell
git push -u origin feature/<your-work-name>
```

---

## 16. Katkı verirken kaçınılması gereken hatalar

- `main` branch üzerinde çalışmak
- Test çalıştırmadan push etmek
- Çok büyük ve dağınık PR açmak
- Tek PR içinde birden fazla bağımsız konu çözmek
- Gereksiz refactor yapmak
- İsimlendirme ve klasör yapısını bozmak
- Çalışmayan kodu “taslak” diye main'e taşımaya çalışmak
- Yalnızca fork'a push edip PR açmayı unutmak

---

## 17. Beklenen minimum katkı kalitesi

Bir katkının kabul edilebilir olması için minimum beklenti:

- Kod localde çalışmalı
- İlgili testler yazılmış olmalı
- Mevcut yapıyla uyumlu olmalı
- PR açıklaması net olmalı
- Değişikliğin kapsamı anlaşılır olmalı

---

## 18. Son öneri

Bu projede amaç sadece kod yazmak değil, yazılan şeyi açıklayabilmek.
Bu yüzden katkı verirken şu soruya net cevap verebilmelisin:

**"Ben ne yaptım, neden yaptım ve nasıl doğruladım?"**

PR değerlendirmesinde en önemli nokta budur.
