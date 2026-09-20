/* SmartLearn AI Quiz Engine */

let currentQuestionIndex = 0;
let userAnswers = {};
let questionsData = [];

function initQuiz(questions) {
    questionsData = questions;
    currentQuestionIndex = 0;
    userAnswers = {};
    renderQuestion(currentQuestionIndex);
    updateProgress();
}

function renderQuestion(index) {
    const q = questionsData[index];
    if (!q) return;

    document.getElementById("current-q-num").textContent = index + 1;
    document.getElementById("total-q-num").textContent = questionsData.length;
    document.getElementById("question-text").textContent = q.question;
    
    if (document.getElementById("question-concept-badge")) {
        document.getElementById("question-concept-badge").textContent = q.concept || "General";
    }

    const optionsContainer = document.getElementById("options-container");
    optionsContainer.innerHTML = "";

    const letters = ["A", "B", "C", "D"];

    q.options.forEach((opt, idx) => {
        const letter = letters[idx] || (idx + 1);
        const btn = document.createElement("div");
        btn.className = "option-btn";
        if (userAnswers[index] === opt) {
            btn.classList.add("selected");
        }

        btn.onclick = () => selectOption(index, opt, btn);

        btn.innerHTML = `
            <div class="option-circle">${letter}</div>
            <div style="flex: 1;">${escapeHtml(opt)}</div>
        `;
        optionsContainer.appendChild(btn);
    });

    // Handle nav buttons
    const prevBtn = document.getElementById("btn-prev");
    const nextBtn = document.getElementById("btn-next");
    const submitBtn = document.getElementById("btn-submit");

    if (prevBtn) prevBtn.style.display = (index === 0) ? "none" : "inline-flex";
    
    if (index === questionsData.length - 1) {
        if (nextBtn) nextBtn.style.display = "none";
        if (submitBtn) submitBtn.style.display = "inline-flex";
    } else {
        if (nextBtn) nextBtn.style.display = "inline-flex";
        if (submitBtn) submitBtn.style.display = "none";
    }
}

function selectOption(qIdx, optionText, element) {
    userAnswers[qIdx] = optionText;
    
    // Highlight UI
    const allBtns = document.querySelectorAll(".option-btn");
    allBtns.forEach(b => b.classList.remove("selected"));
    element.classList.add("selected");
    
    updateProgress();
}

function prevQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion(currentQuestionIndex);
        updateProgress();
    }
}

function nextQuestion() {
    if (currentQuestionIndex < questionsData.length - 1) {
        currentQuestionIndex++;
        renderQuestion(currentQuestionIndex);
        updateProgress();
    }
}

function updateProgress() {
    const answeredCount = Object.keys(userAnswers).length;
    const pct = (answeredCount / questionsData.length) * 100;
    const bar = document.getElementById("quiz-progress-bar");
    if (bar) bar.style.width = pct + "%";
}

function submitQuiz() {
    if (Object.keys(userAnswers).length < questionsData.length) {
        if (!confirm("You haven't answered all questions. Submit anyway?")) {
            return;
        }
    }

    showLoading("Evaluating your quiz and updating your learning analytics...");

    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/submit_quiz";

    const inputAnswers = document.createElement("input");
    inputAnswers.type = "hidden";
    inputAnswers.name = "user_answers";
    inputAnswers.value = JSON.stringify(userAnswers);
    form.appendChild(inputAnswers);

    document.body.appendChild(form);
    form.submit();
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showLoading(msg) {
    const overlay = document.getElementById("loading-overlay");
    const label = document.getElementById("loading-label");
    if (label) label.textContent = msg || "SmartLearn AI is processing...";
    if (overlay) overlay.style.display = "flex";
}
