const recommendBtn = document.getElementById("recommendBtn");

const aiStartDate = document.getElementById("aiStartDate");
const aiEndDate = document.getElementById("aiEndDate");

const requireSun = document.getElementById("requireSun");
const requireEarth = document.getElementById("requireEarth");
const requireBoth = document.getElementById("requireBoth");

const aiMessage = document.getElementById("aiMessage");
const recommendationResults =
    document.getElementById("recommendationResults");


recommendBtn.addEventListener("click", async () => {

    aiMessage.textContent = "";

    if (!aiStartDate.value || !aiEndDate.value) {
        aiMessage.textContent =
            "Please enter the mission start and end dates.";
        return;
    }

    if (aiEndDate.value < aiStartDate.value) {
        aiMessage.textContent =
            "The end date must not be before the start date.";
        return;
    }

    if (
        !requireSun.checked &&
        !requireEarth.checked &&
        !requireBoth.checked
    ) {
        aiMessage.textContent =
            "Please select at least one mission requirement.";
        return;
    }

    const requirements = {
        sun_visibility: requireSun.checked,
        earth_visibility: requireEarth.checked,
        simultaneous_visibility: requireBoth.checked
    };

    recommendBtn.disabled = true;
    recommendBtn.textContent = "Processing...";

    aiMessage.textContent =
        "Sending mission requirements...";

    try {

        const response = await fetch(
            "/api/recommendations",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    start_date: aiStartDate.value,
                    end_date: aiEndDate.value,
                    requirements: requirements
                })
            }
        );

        if (!response.ok) {
            throw new Error(
                "Recommendation service is not connected."
            );
        }

        const result = await response.json();

        if (!Array.isArray(result.recommendations)) {
            throw new Error("Invalid recommendation data.");
        }

        displayRecommendations(result.recommendations);

        aiMessage.textContent =
            "Recommendations received successfully.";

    } catch (error) {

        console.error(error);

        aiMessage.textContent =
            "The AI recommendation service is not connected yet. Connect the backend to receive real recommendations.";
    }

    finally {

        recommendBtn.disabled = false;
        recommendBtn.textContent =
            "Find Best Landing Sites";
    }
});


function displayRecommendations(recommendations) {

    recommendationResults.innerHTML = "";

    recommendations.slice(0, 3).forEach((site, index) => {

        const card = document.createElement("div");

        card.className = "recommendation-item";

        const content = document.createElement("div");

        const title = document.createElement("h4");
        title.textContent =
            `${index + 1}. ${site.site_name}`;

        const description = document.createElement("p");
        description.textContent =
            site.reason || "No explanation provided.";

        content.appendChild(title);
        content.appendChild(description);

        card.appendChild(content);

        recommendationResults.appendChild(card);
    });
}