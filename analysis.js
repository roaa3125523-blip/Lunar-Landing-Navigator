const analyzeBtn = document.getElementById("analyzeBtn");

const startDate = document.getElementById("startDate");
const endDate = document.getElementById("endDate");
const siteSelect = document.getElementById("siteSelect");

const formMessage = document.getElementById("formMessage");
const analysisMessage = document.getElementById("analysisMessage");


// EMPTY CHARTS

function createVisibilityChart(canvasId, label, color) {

    const canvas = document.getElementById(canvasId);

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
                        color: "#E9DFC9"
                    }
                }
            },

            scales: {
                x: {
                    ticks: {
                        color: "#AAB5C4",
                        maxTicksLimit: 8
                    },
                    grid: {
                        color: "#24354A"
                    },
                    title: {
                        display: true,
                        text: "Date and Time",
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
                            return value === 1
                                ? "Visible"
                                : "Not Visible";
                        }
                    },

                    grid: {
                        color: "#24354A"
                    }
                }
            }
        }
    });
}


const sunChart = createVisibilityChart(
    "sunChart",
    "Sun Visibility",
    "#C7AD87"
);

const earthChart = createVisibilityChart(
    "earthChart",
    "Earth Visibility",
    "#9CB5C7"
);

const simultaneousChart = createVisibilityChart(
    "simultaneousChart",
    "Simultaneous Visibility",
    "#B8A5C9"
);


// UPDATE CHARTS USING BACKEND DATA

function updateChart(chart, records, field) {

    chart.data.labels = records.map(
        item => item.time
    );

    chart.data.datasets[0].data = records.map(
        item => item[field] ? 1 : 0
    );

    chart.update();
}


// ANALYZE BUTTON

analyzeBtn.addEventListener("click", async () => {

    formMessage.textContent = "";

    if (!siteSelect.value) {
        formMessage.textContent =
            "Please select a landing site.";
        return;
    }

    if (!startDate.value || !endDate.value) {
        formMessage.textContent =
            "Please select the mission start and end dates.";
        return;
    }

    if (endDate.value < startDate.value) {
        formMessage.textContent =
            "The end date must not be before the start date.";
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";

    try {

        const response = await fetch("/api/analysis", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                site_id: siteSelect.value,
                start_date: startDate.value,
                end_date: endDate.value
            })
        });

        if (!response.ok) {
            throw new Error(
                "The analysis service is not available."
            );
        }

        const result = await response.json();

        if (!Array.isArray(result.hourly_results)) {
            throw new Error("Invalid analysis data.");
        }

        const records = result.hourly_results;

        updateChart(
            sunChart,
            records,
            "sun_visibility"
        );

        updateChart(
            earthChart,
            records,
            "earth_visibility"
        );

        updateChart(
            simultaneousChart,
            records,
            "simultaneous_visibility"
        );

        analysisMessage.textContent =
            "Analysis data loaded successfully.";

    } catch (error) {

        console.error(error);

        analysisMessage.textContent =
            "Analysis service is not connected yet. The charts will appear after the backend is connected.";

    } finally {

        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Mission";
    }
});