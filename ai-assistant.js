// AI Site Recommendation Module for Lunar Explorer

const recommendButton =
    document.getElementById("recommendButton") ||
    document.getElementById("recommendBtn");

const aiStartInput =
    document.getElementById("aiStart") ||
    document.getElementById("aiStartDate");

const aiEndInput =
    document.getElementById("aiEnd") ||
    document.getElementById("aiEndDate");

const prioritySelect =
    document.getElementById("priority");

const statusElement =
    document.getElementById("recommendationStatus") ||
    document.getElementById("aiMessage");

const resultsContainer =
    document.getElementById("recommendations") ||
    document.getElementById("recommendationResults");

if (recommendButton) {
    recommendButton.addEventListener("click", async () => {
        const startDate = (aiStartInput && aiStartInput.value) || "2026-11-10";
        const endDate = (aiEndInput && aiEndInput.value) || "2026-11-25";
        const priority = (prioritySelect && prioritySelect.value) || "both";

        if (statusElement) {
            statusElement.textContent = "";
        }

        if (endDate <= startDate) {
            if (statusElement) {
                statusElement.textContent = "End date must be after start date.";
            }
            return;
        }

        recommendButton.disabled = true;
        const originalText = recommendButton.innerHTML;
        recommendButton.textContent = "Evaluating candidate sites...";

        if (statusElement) {
            statusElement.textContent = "AI engine analyzing terrain illumination & line-of-sight...";
        }

        try {
            const response = await fetch("/api/recommendations", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate,
                    priority: priority
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || errData.details || "Recommendation calculation failed.");
            }

            const data = await response.json();
            const recommendations = data.recommendations;

            if (!Array.isArray(recommendations) || recommendations.length === 0) {
                throw new Error("No sites met the specified criteria.");
            }

            displayRecommendations(recommendations.slice(0, 3));

            if (statusElement) {
                statusElement.textContent = `Identified top 3 candidate sites for ${priority.toUpperCase()} priority. Click any site to view.`;
            }

        } catch (error) {
            console.error("Recommendation error:", error);
            if (statusElement) {
                statusElement.textContent = error.message || "Failed to calculate recommendations.";
            }
        } finally {
            recommendButton.disabled = false;
            recommendButton.innerHTML = originalText;
        }
    });
}

function displayRecommendations(sites) {
    if (!resultsContainer) return;

    resultsContainer.innerHTML = "";

    sites.forEach((site, index) => {
        const card = document.createElement("div");
        card.className = "recommendation-item";
        card.dataset.siteId = site.site_id;
        card.title = "Click to focus on 3D Moon";

        const textGroup = document.createElement("div");

        const nameEl = document.createElement("strong");
        nameEl.textContent = `${site.site_name || site.site_id}`;

        const reasonEl = document.createElement("small");
        reasonEl.textContent = site.reason || `${site.visible_hours} hrs visibility`;

        textGroup.appendChild(nameEl);
        textGroup.appendChild(reasonEl);

        const rankBadge = document.createElement("span");
        rankBadge.className = "rank";
        rankBadge.textContent = `#${index + 1}`;

        card.appendChild(textGroup);
        card.appendChild(rankBadge);

        // Click to focus site on 3D Moon!
        card.addEventListener("click", () => {
            document.dispatchEvent(
                new CustomEvent("lunar:focus-site", {
                    detail: { site_id: site.site_id }
                })
            );
        });

        resultsContainer.appendChild(card);
    });
}
