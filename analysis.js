// Environmental Analysis Module for Lunar Explorer

let currentSiteId = "Site01";
let currentSiteName = "Connecting Ridge";

// Track site selection from 3D Moon
window.addEventListener("lunar:site-selected", event => {
    if (event.detail) {
        currentSiteId = event.detail.site_id || currentSiteId;
        currentSiteName = event.detail.site_name || currentSiteId;
    }
    const dialogSiteName = document.getElementById("dialogSiteName");
    if (dialogSiteName) {
        dialogSiteName.textContent = currentSiteName;
    }
});

// Helper to create stepped binary visibility line charts
function createVisibilityChart(canvasId, label, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas element not found: #${canvasId}`);
        return null;
    }

    return new Chart(canvas, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                stepped: true,
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: {
                    labels: {
                        color: "#E9DFC9",
                        font: { family: "Space Grotesk, sans-serif" }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#AAB5C4",
                        maxTicksLimit: 8,
                        font: { family: "Space Grotesk, sans-serif" }
                    },
                    grid: { color: "#24354A" },
                    title: {
                        display: true,
                        text: "Observation Date & Time (UTC)",
                        color: "#C7AD87"
                    }
                },
                y: {
                    min: 0,
                    max: 1,
                    ticks: {
                        stepSize: 1,
                        color: "#AAB5C4",
                        callback: function(value) {
                            return value === 1 ? "Visible" : "Blocked";
                        }
                    },
                    grid: { color: "#24354A" }
                }
            }
        }
    });
}

// Initialize Charts matching canvas IDs in index.html
const sunChart = createVisibilityChart("sunChart", "Sun Illumination", "#C7AD87");
const earthChart = createVisibilityChart("earthChart", "Earth Line of Sight", "#9CB5C7");
const combinedChart = createVisibilityChart("combinedChart", "Sun + Earth Simultaneous Visibility", "#B8A5C9");

function updateChart(chart, records, field) {
    if (!chart) return;
    chart.data.labels = records.map(item => item.time);
    chart.data.datasets[0].data = records.map(item => item[field] ? 1 : 0);
    chart.update();
}

// Elements
const runAnalysisBtn = document.getElementById("runAnalysis") || document.getElementById("analyzeBtn");
const analysisDialog = document.getElementById("analysisDialog");
const dialogStatus = document.getElementById("dialogStatus") || document.getElementById("formMessage");
const analysisPlaceholder = document.getElementById("analysisPlaceholder");
const chartsArea = document.getElementById("chartsArea");

const startInput = document.getElementById("analysisStart") || document.getElementById("startDate");
const endInput = document.getElementById("analysisEnd") || document.getElementById("endDate");

if (runAnalysisBtn) {
    runAnalysisBtn.addEventListener("click", async () => {
        const startDate = (startInput && startInput.value) || "2026-11-10";
        const endDate = (endInput && endInput.value) || "2026-11-25";

        if (dialogStatus) {
            dialogStatus.textContent = "";
        }

        if (endDate <= startDate) {
            if (dialogStatus) dialogStatus.textContent = "End date must be after start date.";
            return;
        }

        runAnalysisBtn.disabled = true;
        const originalText = runAnalysisBtn.innerHTML;
        runAnalysisBtn.textContent = "Computing visibility...";

        try {
            const response = await fetch("/api/analysis", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    site_id: currentSiteId,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || errData.details || "Analysis calculation failed.");
            }

            const result = await response.json();
            const records = result.hourly_results;

            if (!Array.isArray(records) || records.length === 0) {
                throw new Error("No data returned for the selected time range.");
            }

            // Update charts
            updateChart(sunChart, records, "sun_visibility");
            updateChart(earthChart, records, "earth_visibility");
            updateChart(combinedChart, records, "simultaneous_visibility");

            // Reveal charts
            if (analysisPlaceholder) analysisPlaceholder.style.display = "none";
            if (chartsArea) chartsArea.classList.remove("hidden");

            // Close modal
            if (analysisDialog && typeof analysisDialog.close === "function") {
                analysisDialog.close();
            }

            // Smooth scroll to charts
            chartsArea?.scrollIntoView({ behavior: "smooth", block: "start" });

        } catch (error) {
            console.error("Analysis error:", error);
            if (dialogStatus) {
                dialogStatus.textContent = error.message || "Failed to load analysis.";
            }
        } finally {
            runAnalysisBtn.disabled = false;
            runAnalysisBtn.innerHTML = originalText;
        }
    });
}
