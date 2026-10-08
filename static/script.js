async function analyzeDocument() {

    const fileInput = document.getElementById("document");
    const loading = document.getElementById("loading");

    // Check file
    if (!fileInput.files.length) {
        alert("Please select a PDF or image document.");
        return;
    }

    const file = fileInput.files[0];

    // Show loading
    loading.classList.remove("hidden");

    const formData = new FormData();
    formData.append("document", file);

    try {

        const response = await fetch("/analyze", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Document analysis failed.");
        }

        const data = result.data;

        // Show result section
        document
            .getElementById("resultSection")
            .classList.remove("hidden");


        // Summary
        document.getElementById("summary").innerText =
            data.summary || "-";


        // Important information
        const info = data.important_information || {};

        document.getElementById("name").innerText =
            info.name || "-";

        document.getElementById("department").innerText =
            info.department || "-";

        document.getElementById("date").innerText =
            info.date || "-";

        document.getElementById("deadline").innerText =
            info.deadline || "-";


        // Important points
        const points = document.getElementById("importantPoints");

        points.innerHTML = "";

        if (data.important_points &&
            data.important_points.length > 0) {

            data.important_points.forEach(function(point) {

                const li = document.createElement("li");

                li.innerText = point;

                points.appendChild(li);

            });

        } else {

            const li = document.createElement("li");

            li.innerText = "No important points found.";

            points.appendChild(li);
        }


        // Scroll to result
        document.getElementById("resultSection")
            .scrollIntoView({
                behavior: "smooth"
            });


    } catch (error) {

        alert("Error: " + error.message);

    } finally {

        // Hide loading
        loading.classList.add("hidden");
    }
}



async function askQuestion() {

    const questionInput =
        document.getElementById("question");

    const answer =
        document.getElementById("answer");

    const answerText =
        document.getElementById("answerText");


    const question =
        questionInput.value.trim();


    // Check question
    if (!question) {

        alert("Please enter a question.");

        return;
    }


    answer.classList.remove("hidden");

    answerText.innerText =
        "🤖 AI is thinking...";


    try {

        const response = await fetch("/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })
        });


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.error || "Question failed."
            );

        }


        answerText.innerText =
            result.answer || "No answer found.";


    } catch (error) {

        answerText.innerText =
            "Error: " + error.message;
    }
}