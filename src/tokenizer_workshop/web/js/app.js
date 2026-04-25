/**
 * app.js
 *
 * Tokenizer Workshop Dashboard frontend logic.
 */

const state = {
    tokenizers: [],
    selectedTokenizers: new Set(),
    lastCompareResult: null,
    lastEvaluateResult: null,
    lastMode: "compare",
};

// --------------------------------------------------
// DOM References
// --------------------------------------------------
const textInput = document.getElementById("textInput");
const modeSelect = document.getElementById("modeSelect");
const sortModeSelect = document.getElementById("sortModeSelect");

const tokenizerCheckboxList = document.getElementById("tokenizerCheckboxList");
const selectionInfo = document.getElementById("selectionInfo");
const statusBox = document.getElementById("statusBox");
const insightBox = document.getElementById("insightBox");

const analyzeButton = document.getElementById("analyzeButton");
const clearButton = document.getElementById("clearButton");
const selectAllButton = document.getElementById("selectAllButton");
const clearSelectionButton = document.getElementById("clearSelectionButton");

const copyResultsButton = document.getElementById("copyResultsButton");
const downloadJsonButton = document.getElementById("downloadJsonButton");
const downloadReportButton = document.getElementById("downloadReportButton");
const downloadPdfBtn = document.getElementById("download-pdf-btn");
const reportFormatSelect = document.getElementById("reportFormatSelect");

const resultsContainer = document.getElementById("resultsContainer");
const highlightsContainer = document.getElementById("highlightsContainer");
const metricsTableContainer = document.getElementById("metricsTableContainer");
const pairwiseContainer = document.getElementById("pairwiseContainer");

const summarySelectedCount = document.getElementById("summarySelectedCount");
const summaryRunCount = document.getElementById("summaryRunCount");
const summaryTextLength = document.getElementById("summaryTextLength");
const summaryMode = document.getElementById("summaryMode");
const heroModeValue = document.getElementById("heroModeValue");
const modeDescription = document.getElementById("modeDescription");

const metricsSection = document.getElementById("metricsSection");
const pairwiseSection = document.getElementById("pairwiseSection");

// --------------------------------------------------
// Utilities
// --------------------------------------------------
function setStatus(message, type = "info") {
    statusBox.textContent = message;
    statusBox.dataset.state = type;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatNumber(value, digits = 2) {
    return typeof value === "number" && Number.isFinite(value)
        ? value.toFixed(digits)
        : "-";
}

function truncateText(value, maxLength = 220) {
    if (!value) return "";
    return value.length <= maxLength
        ? value
        : `${value.slice(0, maxLength)}...`;
}

function downloadTextFile(content, filename, mimeType = "text/plain;charset=utf-8") {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();

    URL.revokeObjectURL(url);
}

function getSelectedTokenizerNames() {
    return Array.from(state.selectedTokenizers);
}

function getRequestPayload() {
    return {
        text: textInput.value.trim(),
        tokenizer_names: getSelectedTokenizerNames(),
    };
}

function getSortedTokenizers(tokenizers) {
    const sortMode = sortModeSelect.value;
    const tokenizersCopy = [...tokenizers];

    if (sortMode === "name_asc") {
        return tokenizersCopy.sort((a, b) => a.localeCompare(b));
    }

    return tokenizersCopy;
}

function updateSelectionSummary() {
    const count = state.selectedTokenizers.size;
    selectionInfo.textContent = `${count} seçim`;
    summarySelectedCount.textContent = String(count);
}

function updateModeUI() {
    const mode = modeSelect.value;
    const isEvaluate = mode === "evaluate";

    state.lastMode = mode;
    heroModeValue.textContent = isEvaluate ? "Evaluate" : "Compare";
    summaryMode.textContent = isEvaluate ? "Evaluate" : "Compare";

    modeDescription.textContent = isEvaluate
        ? "Evaluate modu detaylı metrikler, latency verileri ve pairwise comparison sonuçları üretir."
        : "Compare modu temel tokenizer karşılaştırma çıktısı üretir ve hızlı analiz için uygundur.";

    metricsSection.style.display = "block";
    pairwiseSection.style.display = "block";

    if (!isEvaluate) {
        metricsTableContainer.innerHTML = `
            <p class="empty-state">
                Detaylı metrikler yalnızca evaluate modunda görüntülenir.
            </p>
        `;
        pairwiseContainer.innerHTML = `
            <p class="empty-state">
                Pairwise comparison verisi yalnızca evaluate modunda görüntülenir.
            </p>
        `;
    }
}

function updateTextSummary() {
    summaryTextLength.textContent = `${textInput.value.trim().length} karakter`;
}

// --------------------------------------------------
// API
// --------------------------------------------------
async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
        },
        ...options,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const detail = data?.detail || "Beklenmeyen bir hata oluştu.";
        throw new Error(detail);
    }

    return data;
}

async function loadTokenizers() {
    setStatus("Tokenizer listesi yükleniyor...");

    try {
        const data = await fetchJson("/api/tokenizers", {
            method: "GET",
        });

        state.tokenizers = Array.isArray(data.available_tokenizers)
            ? data.available_tokenizers
            : [];

        renderTokenizerList();
        setStatus("Tokenizer listesi başarıyla yüklendi.", "success");
    } catch (error) {
        tokenizerCheckboxList.innerHTML = `
            <p class="empty-state">Tokenizer listesi yüklenemedi.</p>
        `;
        setStatus(`Tokenizer listesi yüklenemedi: ${error.message}`, "error");
    }
}

async function runAnalysis() {
    const payload = getRequestPayload();
    const mode = modeSelect.value;

    if (!payload.text) {
        setStatus("Lütfen önce bir metin gir.", "error");
        textInput.focus();
        return;
    }

    if (payload.tokenizer_names.length === 0) {
        setStatus("Lütfen en az bir tokenizer seç.", "error");
        return;
    }

    updateTextSummary();
    setStatus(`${mode === "evaluate" ? "Evaluate" : "Compare"} isteği gönderiliyor...`);

    analyzeButton.disabled = true;

    try {
        if (mode === "evaluate") {
            const result = await fetchJson("/api/evaluate", {
                method: "POST",
                body: JSON.stringify(payload),
            });

            state.lastEvaluateResult = result;
            state.lastCompareResult = {
                text: result.source_text,
                total_tokenizers: Array.isArray(result.evaluations)
                    ? result.evaluations.length
                    : 0,
                results: (result.evaluations || []).map((item) => ({
                    tokenizer_name: item.tokenizer_name,
                    tokens: item.tokens || [],
                    token_count: item.metrics?.token_count ?? (item.tokens?.length || 0),
                    vocab_size: item.metrics?.unique_token_count ?? 0,
                    metrics: item.metrics || null,
                })),
                pairwise_comparisons: result.pairwise_comparisons || [],
            };

            renderEvaluateResult(result);
            setStatus("Evaluate sonucu başarıyla üretildi.", "success");
        } else {
            const result = await fetchJson("/api/compare", {
                method: "POST",
                body: JSON.stringify(payload),
            });

            state.lastCompareResult = result;
            state.lastEvaluateResult = null;

            renderCompareResult(result);
            setStatus("Compare sonucu başarıyla üretildi.", "success");
        }
    } catch (error) {
        setStatus(`Analiz başarısız: ${error.message}`, "error");
    } finally {
        analyzeButton.disabled = false;
    }
}

async function downloadReport() {
    if (!state.lastCompareResult) {
        setStatus("Önce compare veya evaluate sonucu üretmelisin.", "error");
        return;
    }

    const format = reportFormatSelect.value;

    try {
        setStatus("Rapor hazırlanıyor...");

        const payload = {
            text: textInput.value.trim(),
            tokenizer_names: getSelectedTokenizerNames(),
            format,
        };

        const result = await fetchJson("/api/report", {
            method: "POST",
            body: JSON.stringify(payload),
        });

        const mimeType =
            result.format === "md"
                ? "text/markdown;charset=utf-8"
                : "text/plain;charset=utf-8";

        downloadTextFile(result.report, result.filename, mimeType);
        setStatus(`Rapor indirildi: ${result.filename}`, "success");
    } catch (error) {
        setStatus(`Rapor indirilemedi: ${error.message}`, "error");
    }
}

async function downloadPdfReport() {
    const text = textInput.value.trim();
    const tokenizerNames = getSelectedTokenizerNames();

    if (!text) {
        setStatus("PDF için önce metin girmelisin.", "error");
        textInput.focus();
        return;
    }

    if (tokenizerNames.length === 0) {
        setStatus("PDF için en az bir tokenizer seçmelisin.", "error");
        return;
    }

    try {
        setStatus("PDF hazırlanıyor...");

        const response = await fetch("/api/report/pdf", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text,
                tokenizer_names: tokenizerNames,
                format: "md",
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const detail = errorData?.detail || "PDF üretilemedi.";
            throw new Error(detail);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "tokenizer_report.pdf";
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();

        URL.revokeObjectURL(url);

        setStatus("PDF indirildi.", "success");
    } catch (error) {
        setStatus(`PDF indirilemedi: ${error.message}`, "error");
    }
}

// --------------------------------------------------
// Render Functions
// --------------------------------------------------
function renderTokenizerList() {
    const sortedTokenizers = getSortedTokenizers(state.tokenizers);

    if (sortedTokenizers.length === 0) {
        tokenizerCheckboxList.innerHTML = `<p class="empty-state">Tokenizer bulunamadı.</p>`;
        return;
    }

    tokenizerCheckboxList.innerHTML = sortedTokenizers
        .map((tokenizerName) => {
            const checked = state.selectedTokenizers.has(tokenizerName) ? "checked" : "";

            return `
                <label class="checkbox-card">
                    <input
                        type="checkbox"
                        value="${escapeHtml(tokenizerName)}"
                        ${checked}
                        data-tokenizer-checkbox
                    />
                    <span>${escapeHtml(tokenizerName)}</span>
                </label>
            `;
        })
        .join("");

    document.querySelectorAll("[data-tokenizer-checkbox]").forEach((checkbox) => {
        checkbox.addEventListener("change", (event) => {
            const value = event.target.value;

            if (event.target.checked) {
                state.selectedTokenizers.add(value);
            } else {
                state.selectedTokenizers.delete(value);
            }

            updateSelectionSummary();
        });
    });

    updateSelectionSummary();
}

function renderCompareCards(results) {
    if (!Array.isArray(results) || results.length === 0) {
        resultsContainer.innerHTML = `
            <p class="empty-state">Henüz analiz sonucu yok.</p>
        `;
        return;
    }

    resultsContainer.innerHTML = results
        .map((item) => {
            const tokenizerName = escapeHtml(item.tokenizer_name || "-");
            const tokenCount = item.token_count ?? 0;
            const vocabSize = item.vocab_size ?? 0;
            const tokens = Array.isArray(item.tokens) ? item.tokens : [];

            return `
                <article class="result-card">
                    <div class="result-card__header">
                        <h3>${tokenizerName}</h3>
                        <div class="result-card__meta">
                            <span>Token: ${tokenCount}</span>
                            <span>Vocab: ${vocabSize}</span>
                        </div>
                    </div>

                    <div class="result-card__body">
                        <p class="result-card__tokens">${escapeHtml(truncateText(tokens.join(" | "), 500))}</p>
                    </div>
                </article>
            `;
        })
        .join("");
}

function renderHighlightsFromCompare(compareResult) {
    const results = compareResult?.results || [];

    if (!Array.isArray(results) || results.length === 0) {
        highlightsContainer.innerHTML = `<p class="empty-state">Henüz highlight verisi yok.</p>`;
        insightBox.textContent = "Henüz analiz içgörüsü yok.";
        summaryRunCount.textContent = "0";
        return;
    }

    const lowestToken = results.reduce((min, item) =>
        (item.token_count ?? 0) < (min.token_count ?? 0) ? item : min
    );
    const highestToken = results.reduce((max, item) =>
        (item.token_count ?? 0) > (max.token_count ?? 0) ? item : max
    );
    const highestVocab = results.reduce((max, item) =>
        (item.vocab_size ?? 0) > (max.vocab_size ?? 0) ? item : max
    );

    highlightsContainer.innerHTML = `
        <div class="highlight-grid">
            <div class="highlight-card">
                <span class="highlight-card__label">En Az Token</span>
                <strong>${escapeHtml(lowestToken.tokenizer_name || "-")}</strong>
                <p>${lowestToken.token_count ?? 0} token</p>
            </div>

            <div class="highlight-card">
                <span class="highlight-card__label">En Çok Token</span>
                <strong>${escapeHtml(highestToken.tokenizer_name || "-")}</strong>
                <p>${highestToken.token_count ?? 0} token</p>
            </div>

            <div class="highlight-card">
                <span class="highlight-card__label">En Yüksek Vocab</span>
                <strong>${escapeHtml(highestVocab.tokenizer_name || "-")}</strong>
                <p>${highestVocab.vocab_size ?? 0} unique token</p>
            </div>
        </div>
    `;

    insightBox.textContent =
        `En az token üreten tokenizer: ${lowestToken.tokenizer_name}. ` +
        `En yüksek vocab değerine sahip tokenizer: ${highestVocab.tokenizer_name}.`;

    summaryRunCount.textContent = String(compareResult.total_tokenizers ?? results.length);
}

function renderMetricsTable(evaluations) {
    if (!Array.isArray(evaluations) || evaluations.length === 0) {
        metricsTableContainer.innerHTML = `
            <p class="empty-state">Henüz metrik verisi yok.</p>
        `;
        return;
    }

    const rows = evaluations
        .map((item) => {
            const metrics = item.metrics || {};

            return `
                <tr>
                    <td>${escapeHtml(item.tokenizer_name || "-")}</td>
                    <td>${metrics.token_count ?? "-"}</td>
                    <td>${metrics.unique_token_count ?? "-"}</td>
                    <td>${formatNumber(metrics.unique_ratio, 2)}</td>
                    <td>${formatNumber(metrics.average_token_length, 2)}</td>
                    <td>${formatNumber(metrics.avg_chars_per_token, 2)}</td>
                    <td>${formatNumber(metrics.latency_seconds, 6)}</td>
                    <td>${formatNumber(metrics.latency_per_token, 6)}</td>
                    <td>${formatNumber(metrics.efficiency_score, 2)}</td>
                    <td>${formatNumber(metrics.compression_ratio, 2)}</td>
                </tr>
            `;
        })
        .join("");

    metricsTableContainer.innerHTML = `
        <div class="table-wrapper">
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Tokenizer</th>
                        <th>Token Count</th>
                        <th>Unique</th>
                        <th>Unique Ratio</th>
                        <th>Avg Token Length</th>
                        <th>Chars / Token</th>
                        <th>Latency</th>
                        <th>Latency / Token</th>
                        <th>Efficiency</th>
                        <th>Compression</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

function renderPairwiseComparisons(pairwiseComparisons) {
    if (!Array.isArray(pairwiseComparisons) || pairwiseComparisons.length === 0) {
        pairwiseContainer.innerHTML = `
            <p class="empty-state">Henüz pairwise comparison verisi yok.</p>
        `;
        return;
    }

    pairwiseContainer.innerHTML = pairwiseComparisons
        .map((item) => {
            return `
                <article class="pairwise-card">
                    <h4>${escapeHtml(item.left_name || "-")} ↔ ${escapeHtml(item.right_name || "-")}</h4>
                    <p><strong>Overlap Ratio:</strong> ${formatNumber(item.overlap_ratio, 2)}</p>
                    <p><strong>Common Tokens:</strong> ${escapeHtml(truncateText((item.common_tokens || []).join(", "), 220))}</p>
                    <p><strong>Only Left:</strong> ${escapeHtml(truncateText((item.unique_to_left || []).join(", "), 180))}</p>
                    <p><strong>Only Right:</strong> ${escapeHtml(truncateText((item.unique_to_right || []).join(", "), 180))}</p>
                </article>
            `;
        })
        .join("");
}

function renderCompareResult(compareResult) {
    renderCompareCards(compareResult.results || []);
    renderHighlightsFromCompare(compareResult);

    metricsTableContainer.innerHTML = `
        <p class="empty-state">
            Detaylı metrikler yalnızca evaluate modunda görüntülenir.
        </p>
    `;

    pairwiseContainer.innerHTML = `
        <p class="empty-state">
            Pairwise comparison verisi yalnızca evaluate modunda görüntülenir.
        </p>
    `;
}

function renderEvaluateResult(evaluateResult) {
    const compareProjection = {
        text: evaluateResult.source_text,
        total_tokenizers: Array.isArray(evaluateResult.evaluations)
            ? evaluateResult.evaluations.length
            : 0,
        results: (evaluateResult.evaluations || []).map((item) => ({
            tokenizer_name: item.tokenizer_name,
            tokens: item.tokens || [],
            token_count: item.metrics?.token_count ?? 0,
            vocab_size: item.metrics?.unique_token_count ?? 0,
            metrics: item.metrics || {},
        })),
    };

    renderCompareCards(compareProjection.results);
    renderHighlightsFromCompare(compareProjection);
    renderMetricsTable(evaluateResult.evaluations || []);
    renderPairwiseComparisons(evaluateResult.pairwise_comparisons || []);

    const evaluations = evaluateResult.evaluations || [];
    if (evaluations.length > 0) {
        const fastest = evaluations.reduce((min, item) =>
            (item.metrics?.latency_seconds ?? Number.POSITIVE_INFINITY) <
            (min.metrics?.latency_seconds ?? Number.POSITIVE_INFINITY)
                ? item
                : min
        );

        insightBox.textContent =
            `En hızlı tokenizer: ${fastest.tokenizer_name}. ` +
            `Evaluate modu detaylı metrikler ve pairwise karşılaştırma verileri üretti.`;
    }

    summaryRunCount.textContent = String(evaluations.length);
}

// --------------------------------------------------
// User Actions
// --------------------------------------------------
function clearAll() {
    textInput.value = "";
    state.selectedTokenizers.clear();
    state.lastCompareResult = null;
    state.lastEvaluateResult = null;

    renderTokenizerList();
    updateTextSummary();

    resultsContainer.innerHTML = `<p class="empty-state">Henüz bir analiz sonucu yok.</p>`;
    highlightsContainer.innerHTML = `<p class="empty-state">Henüz highlight verisi yok.</p>`;
    metricsTableContainer.innerHTML = `
        <p class="empty-state">
            Detaylı metrikler yalnızca evaluate modunda görüntülenir.
        </p>
    `;
    pairwiseContainer.innerHTML = `
        <p class="empty-state">
            Pairwise comparison verisi yalnızca evaluate modunda görüntülenir.
        </p>
    `;

    insightBox.textContent = "Henüz analiz içgörüsü yok.";
    summaryRunCount.textContent = "0";

    updateSelectionSummary();
    setStatus("Form temizlendi.", "success");
}

async function copyResultsToClipboard() {
    const source = state.lastMode === "evaluate"
        ? state.lastEvaluateResult
        : state.lastCompareResult;

    if (!source) {
        setStatus("Kopyalanacak sonuç bulunamadı.", "error");
        return;
    }

    try {
        await navigator.clipboard.writeText(JSON.stringify(source, null, 2));
        setStatus("Sonuçlar panoya kopyalandı.", "success");
    } catch (error) {
        setStatus("Sonuçlar panoya kopyalanamadı.", "error");
    }
}

function downloadJson() {
    const source = state.lastMode === "evaluate"
        ? state.lastEvaluateResult
        : state.lastCompareResult;

    if (!source) {
        setStatus("İndirilecek JSON sonucu bulunamadı.", "error");
        return;
    }

    const filename = state.lastMode === "evaluate"
        ? "tokenizer_evaluation.json"
        : "tokenizer_compare.json";

    downloadTextFile(
        JSON.stringify(source, null, 2),
        filename,
        "application/json;charset=utf-8"
    );

    setStatus(`JSON indirildi: ${filename}`, "success");
}

// --------------------------------------------------
// Event Bindings
// --------------------------------------------------
analyzeButton.addEventListener("click", runAnalysis);
clearButton.addEventListener("click", clearAll);

selectAllButton.addEventListener("click", () => {
    state.tokenizers.forEach((name) => state.selectedTokenizers.add(name));
    renderTokenizerList();
    updateSelectionSummary();
});

clearSelectionButton.addEventListener("click", () => {
    state.selectedTokenizers.clear();
    renderTokenizerList();
    updateSelectionSummary();
});

sortModeSelect.addEventListener("change", renderTokenizerList);

modeSelect.addEventListener("change", () => {
    updateModeUI();
    setStatus(`Mod değiştirildi: ${modeSelect.value}`, "success");
});

textInput.addEventListener("input", updateTextSummary);

copyResultsButton.addEventListener("click", copyResultsToClipboard);
downloadJsonButton.addEventListener("click", downloadJson);
downloadReportButton.addEventListener("click", downloadReport);

if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener("click", downloadPdfReport);
}

// --------------------------------------------------
// Init
// --------------------------------------------------
function init() {
    updateModeUI();
    updateTextSummary();
    updateSelectionSummary();
    loadTokenizers();
}

init();