/* =========================================================
   TOKENIZER WORKSHOP DASHBOARD
   =========================================================
   Bu dosya compare odaklı UI davranışını yönetir.

   Temel sorumluluklar:
   - tokenizer listesini backend'den yüklemek
   - seçimleri yönetmek
   - compare isteği göndermek
   - gelen sonuçları normalize edip render etmek
   - rich metrics / highlights / pairwise verilerini göstermek
   - sonuçları kopyalamak ve indirmek
   - UI state'ini tutarlı yönetmek
========================================================= */

/* =========================================================
   DOM REFERENCES
========================================================= */
const elements = {
    textInput: document.getElementById("textInput"),
    analyzeButton: document.getElementById("analyzeButton"),
    clearButton: document.getElementById("clearButton"),
    selectAllButton: document.getElementById("selectAllButton"),
    clearSelectionButton: document.getElementById("clearSelectionButton"),
    copyResultsButton: document.getElementById("copyResultsButton"),
    downloadJsonButton: document.getElementById("downloadJsonButton"),
    downloadReportButton: document.getElementById("downloadReportButton"),
    reportFormatSelect: document.getElementById("reportFormatSelect"),
    sortModeSelect: document.getElementById("sortModeSelect"),

    tokenizerCheckboxList: document.getElementById("tokenizerCheckboxList"),
    resultsContainer: document.getElementById("resultsContainer"),
    statusBox: document.getElementById("statusBox"),
    selectionInfo: document.getElementById("selectionInfo"),
    insightBox: document.getElementById("insightBox"),

    summarySelectedCount: document.getElementById("summarySelectedCount"),
    summaryRunCount: document.getElementById("summaryRunCount"),
    summaryTextLength: document.getElementById("summaryTextLength"),

    metricsTableContainer: document.getElementById("metricsTableContainer"),
    highlightsContainer: document.getElementById("highlightsContainer"),
    pairwiseContainer: document.getElementById("pairwiseContainer"),
};

/* =========================================================
   APP STATE
========================================================= */
const state = {
    lastCompareRawResult: null,
    lastNormalizedResult: null,
    lastInputText: "",
    isLoading: false,
};

/* =========================================================
   CONFIG
========================================================= */
const API = {
    tokenizers: "/api/tokenizers",
    compare: "/api/compare",
    report: "/api/report",
};

const DEFAULT_EMPTY_MESSAGE = "Henüz bir karşılaştırma sonucu yok.";
const DEFAULT_INSIGHT_MESSAGE = "Henüz analiz içgörüsü yok.";

/* =========================================================
   GENERIC HELPERS
========================================================= */
function exists(value) {
    return value !== null && value !== undefined;
}

function safeArray(value) {
    return Array.isArray(value) ? value : [];
}

function safeNumber(value, fallback = 0) {
    return Number.isFinite(Number(value)) ? Number(value) : fallback;
}

function safeString(value, fallback = "") {
    return exists(value) ? String(value) : fallback;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatDecimal(value, digits = 2) {
    return safeNumber(value).toFixed(digits);
}

function formatLatencySeconds(value) {
    return `${safeNumber(value).toFixed(6)}s`;
}

function setText(element, value) {
    if (!element) return;
    element.textContent = value;
}

function setHtml(element, value) {
    if (!element) return;
    element.innerHTML = value;
}

/* =========================================================
   STATUS / UI STATE
========================================================= */
function setStatus(message, isError = false) {
    if (!elements.statusBox) return;

    elements.statusBox.textContent = message;

    if (isError) {
        elements.statusBox.classList.add("error");
    } else {
        elements.statusBox.classList.remove("error");
    }
}

function setLoadingState(isLoading) {
    state.isLoading = isLoading;

    const controls = [
        elements.analyzeButton,
        elements.clearButton,
        elements.selectAllButton,
        elements.clearSelectionButton,
        elements.copyResultsButton,
        elements.downloadJsonButton,
        elements.downloadReportButton,
        elements.reportFormatSelect,
        elements.sortModeSelect,
    ];

    controls.forEach((control) => {
        if (control) {
            control.disabled = isLoading;
        }
    });

    if (isLoading) {
        document.body.classList.add("loading");
        setText(elements.analyzeButton, "Çalışıyor...");
    } else {
        document.body.classList.remove("loading");
        setText(elements.analyzeButton, "Karşılaştır");
    }
}

/* =========================================================
   FILE DOWNLOAD HELPERS
========================================================= */
function downloadTextFile(filename, content, mimeType = "text/plain;charset=utf-8") {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}

/* =========================================================
   SELECTION HELPERS
========================================================= */
function getTokenizerCheckboxes() {
    return document.querySelectorAll('input[name="tokenizer"]');
}

function getSelectedTokenizers() {
    return Array.from(document.querySelectorAll('input[name="tokenizer"]:checked'))
        .map((item) => item.value);
}

function updateSelectionInfo() {
    const count = getSelectedTokenizers().length;

    setText(elements.selectionInfo, `${count} seçim`);
    setText(elements.summarySelectedCount, String(count));
}

function selectAllTokenizers() {
    getTokenizerCheckboxes().forEach((checkbox) => {
        checkbox.checked = true;
    });

    updateSelectionInfo();
    setStatus("Tüm tokenizer'lar seçildi.");
}

function clearTokenizerSelection(showStatus = true) {
    getTokenizerCheckboxes().forEach((checkbox) => {
        checkbox.checked = false;
    });

    updateSelectionInfo();

    if (showStatus) {
        setStatus("Tokenizer seçimi temizlendi.");
    }
}

/* =========================================================
   API HELPERS
========================================================= */
async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const errorMessage =
            data?.detail ||
            data?.message ||
            `Request failed with status ${response.status}`;
        throw new Error(errorMessage);
    }

    return data;
}

/* =========================================================
   TOKENIZER LIST LOAD
========================================================= */
function buildTokenizerCheckbox(name) {
    const wrapper = document.createElement("label");
    wrapper.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "tokenizer";
    checkbox.value = name;
    checkbox.addEventListener("change", updateSelectionInfo);

    const text = document.createElement("span");
    text.textContent = name;

    wrapper.appendChild(checkbox);
    wrapper.appendChild(text);

    return wrapper;
}

async function loadTokenizers() {
    try {
        setStatus("Tokenizer listesi yükleniyor...");

        const data = await fetchJson(API.tokenizers);
        const tokenizers = safeArray(data.available_tokenizers);

        if (!elements.tokenizerCheckboxList) return;

        elements.tokenizerCheckboxList.innerHTML = "";

        if (tokenizers.length === 0) {
            setHtml(
                elements.tokenizerCheckboxList,
                "<p>Kullanılabilir tokenizer bulunamadı.</p>"
            );
            updateSelectionInfo();
            setStatus("Tokenizer listesi boş geldi.", true);
            return;
        }

        tokenizers.forEach((name) => {
            elements.tokenizerCheckboxList.appendChild(buildTokenizerCheckbox(name));
        });

        updateSelectionInfo();
        setStatus("Tokenizer listesi yüklendi.");
    } catch (error) {
        console.error(error);

        setHtml(
            elements.tokenizerCheckboxList,
            "<p>Tokenizer listesi yüklenemedi.</p>"
        );

        setStatus("Tokenizer listesi yüklenirken hata oluştu.", true);
    }
}

/* =========================================================
   RESPONSE NORMALIZATION
========================================================= */
/*
    UI iki response tipini destekler:

    1) Simple Compare Response
       {
         text,
         total_tokenizers,
         results: [
           {
             tokenizer_name,
             tokens,
             token_count,
             vocab_size
           }
         ]
       }

    2) Rich Compare / Report Response
       {
         source_text,
         evaluations: [
           {
             name,
             tokens,
             metrics: {...}
           }
         ],
         pairwise_comparisons: [...]
       }
*/
function normalizeMetrics(metrics = {}, tokens = []) {
    return {
        token_count: safeNumber(metrics.token_count, tokens.length),
        unique_token_count: safeNumber(
            metrics.unique_token_count,
            new Set(tokens).size
        ),
        unique_ratio: safeNumber(metrics.unique_ratio),
        average_token_length: safeNumber(metrics.average_token_length),
        min_token_length: safeNumber(metrics.min_token_length),
        max_token_length: safeNumber(metrics.max_token_length),
        avg_chars_per_token: safeNumber(metrics.avg_chars_per_token),
        unknown_count: safeNumber(metrics.unknown_count),
        unknown_rate: safeNumber(metrics.unknown_rate),
        latency_seconds: safeNumber(metrics.latency_seconds),
        efficiency_score: safeNumber(metrics.efficiency_score),
        top_tokens: safeArray(metrics.top_tokens),
        token_length_distribution: metrics.token_length_distribution || {},
        reconstructed_text: exists(metrics.reconstructed_text)
            ? metrics.reconstructed_text
            : null,
        reconstruction_match: exists(metrics.reconstruction_match)
            ? metrics.reconstruction_match
            : null,
    };
}

function normalizeRichResponse(rawData) {
    const evaluations = safeArray(rawData.evaluations).map((evaluation) => {
        const tokens = safeArray(evaluation.tokens);
        const metrics = normalizeMetrics(evaluation.metrics || {}, tokens);

        return {
            tokenizer_name: safeString(evaluation.name),
            tokens,
            token_count: metrics.token_count,
            vocab_size: metrics.unique_token_count,
            metrics,
        };
    });

    return {
        source_text: safeString(rawData.source_text),
        total_tokenizers: evaluations.length,
        results: evaluations,
        pairwise_comparisons: safeArray(rawData.pairwise_comparisons),
        isRich: true,
        raw: rawData,
    };
}

function normalizeSimpleResponse(rawData) {
    const results = safeArray(rawData.results).map((item) => {
        const tokens = safeArray(item.tokens);

        return {
            tokenizer_name: safeString(item.tokenizer_name),
            tokens,
            token_count: safeNumber(item.token_count, tokens.length),
            vocab_size: safeNumber(item.vocab_size, new Set(tokens).size),
            metrics: null,
        };
    });

    return {
        source_text: safeString(rawData.text),
        total_tokenizers: safeNumber(rawData.total_tokenizers, results.length),
        results,
        pairwise_comparisons: [],
        isRich: false,
        raw: rawData,
    };
}

function normalizeResponse(rawData) {
    if (rawData && Array.isArray(rawData.evaluations)) {
        return normalizeRichResponse(rawData);
    }

    if (rawData && Array.isArray(rawData.results)) {
        return normalizeSimpleResponse(rawData);
    }

    return {
        source_text: "",
        total_tokenizers: 0,
        results: [],
        pairwise_comparisons: [],
        isRich: false,
        raw: rawData,
    };
}

/* =========================================================
   EMPTY / RESET RENDERERS
========================================================= */
function renderEmptyState(message = DEFAULT_EMPTY_MESSAGE) {
    setHtml(
        elements.resultsContainer,
        `<p class="empty-state">${escapeHtml(message)}</p>`
    );
}

function resetOptionalBlocks() {
    setHtml(elements.metricsTableContainer, "");
    setHtml(elements.highlightsContainer, "");
    setHtml(elements.pairwiseContainer, "");
}

function resetSummary() {
    setText(elements.summarySelectedCount, "0");
    setText(elements.summaryRunCount, "0");
    setText(elements.summaryTextLength, "0 karakter");
}

function resetInsights() {
    setText(elements.insightBox, DEFAULT_INSIGHT_MESSAGE);
}

/* =========================================================
   SUMMARY / INSIGHTS
========================================================= */
function renderSummary(normalizedData, selectedCount, text) {
    setText(elements.summarySelectedCount, String(selectedCount));
    setText(elements.summaryRunCount, String(normalizedData.total_tokenizers || 0));
    setText(elements.summaryTextLength, `${text.length} karakter`);
}

function getBestTokenizerByEfficiency(normalizedData) {
    const candidates = normalizedData.results.filter((item) => item.metrics);

    if (candidates.length === 0) return null;

    return [...candidates].sort(
        (a, b) => b.metrics.efficiency_score - a.metrics.efficiency_score
    )[0];
}

function getFastestTokenizer(normalizedData) {
    const candidates = normalizedData.results.filter((item) => item.metrics);

    if (candidates.length === 0) return null;

    return [...candidates].sort(
        (a, b) => a.metrics.latency_seconds - b.metrics.latency_seconds
    )[0];
}

function buildInsights(normalizedData) {
    if (!elements.insightBox) return;

    if (!normalizedData.results.length) {
        resetInsights();
        return;
    }

    const byTokenAsc = [...normalizedData.results].sort(
        (a, b) => a.token_count - b.token_count
    );
    const byTokenDesc = [...normalizedData.results].sort(
        (a, b) => b.token_count - a.token_count
    );
    const byVocabDesc = [...normalizedData.results].sort(
        (a, b) => b.vocab_size - a.vocab_size
    );

    const lowestToken = byTokenAsc[0];
    const highestToken = byTokenDesc[0];
    const highestVocab = byVocabDesc[0];
    const bestEfficiency = getBestTokenizerByEfficiency(normalizedData);
    const fastest = getFastestTokenizer(normalizedData);

    let richHtml = "";

    if (bestEfficiency) {
        richHtml += `
            En yüksek efficiency score değerine sahip tokenizer
            <strong>${escapeHtml(bestEfficiency.tokenizer_name)}</strong>
            (${formatDecimal(bestEfficiency.metrics.efficiency_score)}).
        `;
    }

    if (fastest) {
        richHtml += `
            En hızlı tokenizer
            <strong>${escapeHtml(fastest.tokenizer_name)}</strong>
            (${formatLatencySeconds(fastest.metrics.latency_seconds)}).
        `;
    }

    setHtml(
        elements.insightBox,
        `
        <strong>Özet içgörü:</strong>
        En az token üreten tokenizer <strong>${escapeHtml(lowestToken.tokenizer_name)}</strong>
        (${lowestToken.token_count} token).
        En fazla token üreten tokenizer <strong>${escapeHtml(highestToken.tokenizer_name)}</strong>
        (${highestToken.token_count} token).
        En yüksek vocab size değerine sahip tokenizer
        <strong>${escapeHtml(highestVocab.tokenizer_name)}</strong>
        (${highestVocab.vocab_size} unique token).
        ${richHtml}
        `
    );
}

/* =========================================================
   SORTING
========================================================= */
function sortResults(results, mode) {
    const cloned = [...results];

    switch (mode) {
        case "token_asc":
            return cloned.sort((a, b) => a.token_count - b.token_count);

        case "token_desc":
            return cloned.sort((a, b) => b.token_count - a.token_count);

        case "vocab_desc":
            return cloned.sort((a, b) => b.vocab_size - a.vocab_size);

        case "name_asc":
            return cloned.sort((a, b) =>
                a.tokenizer_name.localeCompare(b.tokenizer_name)
            );

        default:
            return cloned;
    }
}

/* =========================================================
   RESULT CARDS
========================================================= */
function createTokenBadge(token) {
    return `<span class="token-badge">${escapeHtml(token)}</span>`;
}

function renderTokenBadges(tokens) {
    if (!tokens || tokens.length === 0) {
        return `<span class="token-badge token-badge--empty">Token üretilmedi</span>`;
    }

    return tokens.map(createTokenBadge).join("");
}

function getBestTokenizerName(results) {
    if (!results.length) return null;

    const best = [...results].sort((a, b) => {
        if (a.token_count !== b.token_count) {
            return a.token_count - b.token_count;
        }

        return b.vocab_size - a.vocab_size;
    })[0];

    return best.tokenizer_name;
}

function renderMetricGrid(item) {
    if (!item.metrics) return "";

    const m = item.metrics;

    return `
        <div class="result-card__metrics">
            <div class="result-card__metric"><strong>Unique Count:</strong> ${m.unique_token_count}</div>
            <div class="result-card__metric"><strong>Unique Ratio:</strong> ${formatDecimal(m.unique_ratio)}</div>
            <div class="result-card__metric"><strong>Avg Token Length:</strong> ${formatDecimal(m.average_token_length)}</div>
            <div class="result-card__metric"><strong>Min Token Length:</strong> ${m.min_token_length}</div>
            <div class="result-card__metric"><strong>Max Token Length:</strong> ${m.max_token_length}</div>
            <div class="result-card__metric"><strong>Chars / Token:</strong> ${formatDecimal(m.avg_chars_per_token)}</div>
            <div class="result-card__metric"><strong>Unknown Count:</strong> ${m.unknown_count}</div>
            <div class="result-card__metric"><strong>Unknown Rate:</strong> ${formatDecimal(m.unknown_rate)}</div>
            <div class="result-card__metric"><strong>Latency:</strong> ${formatLatencySeconds(m.latency_seconds)}</div>
            <div class="result-card__metric"><strong>Efficiency:</strong> ${formatDecimal(m.efficiency_score)}</div>
        </div>
    `;
}

function createResultCard(item, bestTokenizerName) {
    const isBest = item.tokenizer_name === bestTokenizerName;

    const card = document.createElement("article");
    card.className = isBest
        ? "result-card result-card--best"
        : "result-card";

    card.innerHTML = `
        <div class="result-card__header">
            <div class="result-card__title-group">
                <h3 class="result-card__title">${escapeHtml(item.tokenizer_name)}</h3>
                ${isBest ? '<span class="result-card__best-label">Öne Çıkan</span>' : ""}
            </div>

            <div class="result-card__meta">
                <span class="result-card__badge">Token Count: ${item.token_count}</span>
                <span class="result-card__badge">Vocab Size: ${item.vocab_size}</span>
            </div>
        </div>

        <div class="result-card__body">
            ${renderMetricGrid(item)}
            <div class="token-badge-list">
                ${renderTokenBadges(item.tokens)}
            </div>
        </div>
    `;

    return card;
}

/* =========================================================
   RICH BLOCKS
========================================================= */
function renderHighlights(normalizedData) {
    if (!elements.highlightsContainer) return;

    if (!normalizedData.results.length) {
        setHtml(elements.highlightsContainer, "");
        return;
    }

    const byTokenAsc = [...normalizedData.results].sort(
        (a, b) => a.token_count - b.token_count
    );
    const byTokenDesc = [...normalizedData.results].sort(
        (a, b) => b.token_count - a.token_count
    );
    const byVocabDesc = [...normalizedData.results].sort(
        (a, b) => b.vocab_size - a.vocab_size
    );

    const lowest = byTokenAsc[0];
    const highest = byTokenDesc[0];
    const highestVocab = byVocabDesc[0];
    const bestEfficiency = getBestTokenizerByEfficiency(normalizedData);
    const fastest = getFastestTokenizer(normalizedData);

    setHtml(
        elements.highlightsContainer,
        `
        <ul class="rich-list">
            <li><strong>Lowest Token Count:</strong> ${escapeHtml(lowest.tokenizer_name)} (${lowest.token_count})</li>
            <li><strong>Highest Token Count:</strong> ${escapeHtml(highest.tokenizer_name)} (${highest.token_count})</li>
            <li><strong>Highest Unique Count:</strong> ${escapeHtml(highestVocab.tokenizer_name)} (${highestVocab.vocab_size})</li>
            ${bestEfficiency ? `<li><strong>Best Efficiency:</strong> ${escapeHtml(bestEfficiency.tokenizer_name)} (${formatDecimal(bestEfficiency.metrics.efficiency_score)})</li>` : ""}
            ${fastest ? `<li><strong>Fastest:</strong> ${escapeHtml(fastest.tokenizer_name)} (${formatLatencySeconds(fastest.metrics.latency_seconds)})</li>` : ""}
        </ul>
        `
    );
}

function renderMetricsTable(normalizedData) {
    if (!elements.metricsTableContainer) return;

    if (!normalizedData.isRich || !normalizedData.results.length) {
        setHtml(elements.metricsTableContainer, "");
        return;
    }

    const rows = normalizedData.results
        .filter((item) => item.metrics)
        .map((item) => {
            const m = item.metrics;

            return `
                <tr>
                    <td>${escapeHtml(item.tokenizer_name)}</td>
                    <td>${m.token_count}</td>
                    <td>${m.unique_token_count}</td>
                    <td>${formatDecimal(m.unique_ratio)}</td>
                    <td>${formatDecimal(m.average_token_length)}</td>
                    <td>${m.min_token_length}</td>
                    <td>${m.max_token_length}</td>
                    <td>${formatDecimal(m.avg_chars_per_token)}</td>
                    <td>${m.unknown_count}</td>
                    <td>${formatDecimal(m.unknown_rate)}</td>
                    <td>${formatLatencySeconds(m.latency_seconds)}</td>
                    <td>${formatDecimal(m.efficiency_score)}</td>
                </tr>
            `;
        })
        .join("");

    setHtml(
        elements.metricsTableContainer,
        `
        <div class="table-wrapper">
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Tokenizer</th>
                        <th>Token</th>
                        <th>Uniq</th>
                        <th>Uniq Ratio</th>
                        <th>Avg Len</th>
                        <th>Min Len</th>
                        <th>Max Len</th>
                        <th>Chars/Token</th>
                        <th>Unknown</th>
                        <th>Unknown Rate</th>
                        <th>Latency</th>
                        <th>Efficiency</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
        `
    );
}

function renderPairwiseComparisons(normalizedData) {
    if (!elements.pairwiseContainer) return;

    if (!normalizedData.pairwise_comparisons.length) {
        setHtml(elements.pairwiseContainer, "");
        return;
    }

    const html = normalizedData.pairwise_comparisons
        .map((pair) => {
            return `
                <article class="pairwise-card">
                    <h4>${escapeHtml(pair.left_name)} ↔ ${escapeHtml(pair.right_name)}</h4>
                    <p><strong>Overlap Ratio:</strong> ${formatDecimal(pair.overlap_ratio)}</p>
                    <p><strong>Common Tokens:</strong> ${escapeHtml(JSON.stringify(pair.common_tokens || []))}</p>
                    <p><strong>Only In ${escapeHtml(pair.left_name)}:</strong> ${escapeHtml(JSON.stringify(pair.unique_to_left || []))}</p>
                    <p><strong>Only In ${escapeHtml(pair.right_name)}:</strong> ${escapeHtml(JSON.stringify(pair.unique_to_right || []))}</p>
                </article>
            `;
        })
        .join("");

    setHtml(elements.pairwiseContainer, html);
}

/* =========================================================
   MAIN RENDER FLOW
========================================================= */
function renderCompareResults(rawData, selectedCount, text) {
    const normalizedData = normalizeResponse(rawData);

    state.lastCompareRawResult = rawData;
    state.lastNormalizedResult = normalizedData;
    state.lastInputText = text;

    if (!elements.resultsContainer) return;

    elements.resultsContainer.innerHTML = "";

    renderSummary(normalizedData, selectedCount, text);
    buildInsights(normalizedData);

    if (!normalizedData.results.length) {
        renderEmptyState("Sonuç bulunamadı.");
        resetOptionalBlocks();
        return;
    }

    const sortMode = elements.sortModeSelect?.value || "default";
    const sortedResults = sortResults(normalizedData.results, sortMode);
    const bestTokenizerName = getBestTokenizerName(normalizedData.results);

    sortedResults.forEach((item) => {
        elements.resultsContainer.appendChild(
            createResultCard(item, bestTokenizerName)
        );
    });

    renderHighlights(normalizedData);
    renderMetricsTable(normalizedData);
    renderPairwiseComparisons(normalizedData);
}

/* =========================================================
   API ACTIONS
========================================================= */
async function compareTokenizers() {
    const text = elements.textInput?.value.trim() || "";
    const selectedTokenizers = getSelectedTokenizers();

    if (!text) {
        setStatus("Lütfen bir metin gir.", true);
        return;
    }

    if (selectedTokenizers.length === 0) {
        setStatus("En az bir tokenizer seçmelisin.", true);
        return;
    }

    try {
        setLoadingState(true);
        setStatus("Karşılaştırma işlemi yapılıyor...");

        const data = await fetchJson(API.compare, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text,
                tokenizer_names: selectedTokenizers,
            }),
        });

        renderCompareResults(data, selectedTokenizers.length, text);
        setStatus("Karşılaştırma tamamlandı.");
    } catch (error) {
        console.error(error);
        setStatus(error.message || "Karşılaştırma hatası.", true);
    } finally {
        setLoadingState(false);
    }
}

async function downloadReport() {
    const text = elements.textInput?.value.trim() || "";
    const selectedTokenizers = getSelectedTokenizers();
    const reportFormat = elements.reportFormatSelect?.value || "txt";

    if (!text) {
        setStatus("Lütfen bir metin gir.", true);
        return;
    }

    if (selectedTokenizers.length === 0) {
        setStatus("En az bir tokenizer seçmelisin.", true);
        return;
    }

    try {
        setStatus("Rapor hazırlanıyor...");

        const data = await fetchJson(API.report, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text,
                tokenizer_names: selectedTokenizers,
                format: reportFormat,
            }),
        });

        const filename = data.filename || `tokenizer_report.${reportFormat}`;
        const mimeType =
            reportFormat === "md"
                ? "text/markdown;charset=utf-8"
                : "text/plain;charset=utf-8";

        downloadTextFile(filename, safeString(data.report), mimeType);
        setStatus(`${reportFormat.toUpperCase()} raporu indirildi.`);
    } catch (error) {
        console.error(error);
        setStatus(error.message || "Rapor indirme hatası.", true);
    }
}


/* =========================================================
   COPY / DOWNLOAD ACTIONS
========================================================= */
async function copyResults() {
    if (!state.lastCompareRawResult) {
        setStatus("Kopyalanacak sonuç yok.", true);
        return;
    }

    try {
        await navigator.clipboard.writeText(
            JSON.stringify(state.lastCompareRawResult, null, 2)
        );
        setStatus("Sonuçlar panoya kopyalandı.");
    } catch (error) {
        console.error(error);
        setStatus("Kopyalama işlemi başarısız oldu.", true);
    }
}

function downloadJsonResults() {
    if (!state.lastCompareRawResult) {
        setStatus("İndirilecek sonuç yok.", true);
        return;
    }

    downloadTextFile(
        "tokenizer_compare_result.json",
        JSON.stringify(state.lastCompareRawResult, null, 2),
        "application/json;charset=utf-8"
    );

    setStatus("JSON dosyası indirildi.");
}

/* =========================================================
   CLEAR / RESET
========================================================= */
function clearUI() {
    if (elements.textInput) {
        elements.textInput.value = "";
    }

    clearTokenizerSelection(false);
    resetSummary();
    resetInsights();
    renderEmptyState();
    resetOptionalBlocks();

    state.lastCompareRawResult = null;
    state.lastNormalizedResult = null;
    state.lastInputText = "";

    setStatus("Arayüz temizlendi.");
}

/* =========================================================
   RE-RENDER ON SORT CHANGE
========================================================= */
function rerenderLastResults() {
    if (!state.lastCompareRawResult) return;

    const selectedCount =
        getSelectedTokenizers().length ||
        state.lastNormalizedResult?.total_tokenizers ||
        0;

    renderCompareResults(
        state.lastCompareRawResult,
        selectedCount,
        state.lastInputText
    );
}

/* =========================================================
   EVENT BINDINGS
========================================================= */
function bindEvents() {
    elements.analyzeButton?.addEventListener("click", compareTokenizers);
    elements.clearButton?.addEventListener("click", clearUI);
    elements.selectAllButton?.addEventListener("click", selectAllTokenizers);
    elements.clearSelectionButton?.addEventListener("click", () => clearTokenizerSelection(true));
    elements.copyResultsButton?.addEventListener("click", copyResults);
    elements.downloadJsonButton?.addEventListener("click", downloadJsonResults);
    elements.downloadReportButton?.addEventListener("click", downloadReport);
    elements.sortModeSelect?.addEventListener("change", rerenderLastResults);
}

/* =========================================================
   INIT
========================================================= */
function init() {
    renderEmptyState();
    resetOptionalBlocks();
    resetInsights();
    updateSelectionInfo();
    bindEvents();
    loadTokenizers();
}

window.addEventListener("DOMContentLoaded", init);