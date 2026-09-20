/* SmartLearn AI General Client Script */

document.addEventListener("DOMContentLoaded", function () {
    console.log("SmartLearn AI Ready.");
});

function openExplainModal(questionId) {
    const modal = document.getElementById("explain-modal");
    const container = document.getElementById("explain-modal-body");
    
    if (!modal || !container) return;

    modal.classList.add("active");
    container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem;">
            <div class="loading-spinner" style="margin: 0 auto 1rem;"></div>
            <p style="font-weight: 700; color: var(--primary);">🤖 SmartLearn AI is crafting a detailed step-by-step explanation for your mistake...</p>
        </div>
    `;

    fetch(`/api/explain_mistake/${questionId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: var(--danger); font-weight:700;">Error: ${data.error}</p>`;
                return;
            }
            renderExplainContent(container, data);
        })
        .catch(err => {
            console.error(err);
            container.innerHTML = `<p style="color: var(--danger); font-weight:700;">Could not load explanation right now.</p>`;
        });
}

function closeExplainModal() {
    const modal = document.getElementById("explain-modal");
    if (modal) modal.classList.remove("active");
}

function renderExplainContent(container, data) {
    const pq = data.practice_question || {};
    
    let reasoningHtml = "";
    if (data.step_by_step_reasoning && data.step_by_step_reasoning.length > 0) {
        reasoningHtml = `
            <div style="margin: 1.25rem 0;">
                <h4 style="font-family: var(--font-heading); font-weight: 700; margin-bottom: 0.5rem;">🧠 Step-by-Step Reasoning:</h4>
                <ul style="padding-left: 1.5rem; color: var(--text-secondary);">
                    ${data.step_by_step_reasoning.map(step => `<li style="margin-bottom: 0.4rem;">${step}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    container.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <span style="background: var(--primary-light); color: var(--primary); padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">
                Concept: ${data.concept_name || 'School Learning'}
            </span>
            <h3 style="font-family: var(--font-heading); font-weight: 800; font-size: 1.6rem; margin-top: 0.5rem;">
                Explain My Mistake 💡
            </h3>
        </div>

        <div class="mistake-box">
            <h4 style="color: #991b1b; font-weight: 700; margin-bottom: 0.3rem;">❌ Why Your Answer Was Incorrect:</h4>
            <p style="color: #7f1d1d;"><strong>Your Answer:</strong> ${data.your_choice} | <strong>Correct Answer:</strong> ${data.correct_answer}</p>
            <p style="margin-top: 0.5rem; color: #450a0a;">${data.why_incorrect}</p>
        </div>

        <div class="concept-box">
            <h4 style="color: #1e40af; font-weight: 700; margin-bottom: 0.3rem;">📚 Simple Concept Explanation:</h4>
            <p style="color: #1e3a8a;">${data.simple_explanation}</p>
        </div>

        ${reasoningHtml}

        ${data.real_life_example ? `
        <div style="background: #fdf4ff; border-left: 5px solid var(--accent-pink); padding: 1.25rem; border-radius: var(--radius-sm); margin: 1rem 0;">
            <h4 style="color: #86198f; font-weight: 700; margin-bottom: 0.3rem;">🌟 Real-Life Example:</h4>
            <p style="color: #701a75;">${data.real_life_example}</p>
        </div>` : ''}

        ${data.common_mistake ? `
        <div style="background: #fff7ed; border-left: 5px solid #f97316; padding: 1.25rem; border-radius: var(--radius-sm); margin: 1rem 0;">
            <h4 style="color: #9a3412; font-weight: 700; margin-bottom: 0.3rem;">⚠️ Common Mistake to Avoid:</h4>
            <p style="color: #7c2d12;">${data.common_mistake}</p>
        </div>` : ''}

        <div class="tip-box">
            <h4 style="color: #92400e; font-weight: 700; margin-bottom: 0.3rem;">💡 Memory Tip:</h4>
            <p style="color: #78350f;">${data.memory_tip || 'Keep practicing steps cleanly!'}</p>
        </div>

        ${pq.question ? `
        <div style="background: white; border: 2px solid var(--primary-light); border-radius: var(--radius-md); padding: 1.5rem; margin-top: 1.5rem;">
            <h4 style="font-family: var(--font-heading); font-weight: 800; color: var(--primary); margin-bottom: 0.75rem;">
                🎯 Quick Micro-Practice Check:
            </h4>
            <p style="font-weight: 700; margin-bottom: 1rem;">${pq.question}</p>
            <div style="display: grid; gap: 0.5rem;">
                ${pq.options.map(opt => `
                    <button class="btn btn-secondary" style="justify-content: flex-start; text-align: left; font-size: 0.95rem;" onclick="checkQuickAnswer(this, '${opt === pq.correct_answer}', '${pq.explanation}')">
                        ${opt}
                    </button>
                `).join('')}
            </div>
            <div id="quick-check-result" style="margin-top: 1rem; font-weight: 700;"></div>
        </div>
        ` : ''}
    `;
}

function checkQuickAnswer(btn, isCorrect, explanation) {
    const parent = btn.parentElement;
    const resDiv = document.getElementById("quick-check-result");
    
    if (isCorrect === "true") {
        btn.style.background = "#d1fae5";
        btn.style.borderColor = "#10b981";
        btn.style.color = "#065f46";
        resDiv.innerHTML = `<span style="color: #10b981;">🎉 Spot on! Correct answer! ${explanation}</span>`;
    } else {
        btn.style.background = "#fee2e2";
        btn.style.borderColor = "#ef4444";
        btn.style.color = "#991b1b";
        resDiv.innerHTML = `<span style="color: #ef4444;">Not quite. Try another option or read the explanation above!</span>`;
    }
}

/* Chatbot Functions */
function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const container = document.getElementById("chat-messages");
    if (!input || !container) return;

    const query = input.value.trim();
    if (!query) return;

    // Render User Message
    const userDiv = document.createElement("div");
    userDiv.className = "chat-bubble user";
    userDiv.textContent = query;
    container.appendChild(userDiv);

    input.value = "";
    container.scrollTop = container.scrollHeight;

    // Render Loading AI Message
    const aiLoadingDiv = document.createElement("div");
    aiLoadingDiv.className = "chat-bubble ai";
    aiLoadingDiv.innerHTML = "🤖 <em>SmartLearn AI Tutor is thinking...</em>";
    container.appendChild(aiLoadingDiv);
    container.scrollTop = container.scrollHeight;

    fetch("/api/ask_tutor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query })
    })
    .then(res => res.json())
    .then(data => {
        aiLoadingDiv.innerHTML = data.reply ? data.reply.replace(/\n/g, '<br>') : "Sorry, I couldn't process that response.";
        container.scrollTop = container.scrollHeight;
    })
    .catch(err => {
        console.error(err);
        aiLoadingDiv.innerHTML = "Sorry, I ran into a network error. Please try asking again!";
    });
}

function renderScoreChart(scores, dates) {
    const svg = document.getElementById("score-chart-svg");
    if (!svg || !scores || scores.length === 0) return;

    const width = 600;
    const height = 220;
    const padding = 40;

    const maxScore = 100;
    const minScore = 0;

    const points = scores.map((score, i) => {
        const x = padding + (i / Math.max(1, scores.length - 1)) * (width - 2 * padding);
        const y = height - padding - (score / maxScore) * (height - 2 * padding);
        return { x, y, score, date: dates[i] || `Quiz ${i+1}` };
    });

    let polylinePoints = points.map(p => `${p.x},${p.y}`).join(' ');

    let dotsSvg = points.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="6" fill="#6366f1" stroke="#ffffff" stroke-width="3" />
        <text x="${p.x}" y="${p.y - 12}" font-size="12" font-weight="bold" fill="#4f46e5" text-anchor="middle">${p.score}%</text>
    `).join('');

    svg.innerHTML = `
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#e2e8f0" stroke-width="2"/>
        <polyline fill="none" stroke="url(#chartGrad)" stroke-width="4" points="${polylinePoints}" stroke-linecap="round" />
        <defs>
            <linearGradient id="chartGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#6366f1" />
                <stop offset="100%" stop-color="#ec4899" />
            </linearGradient>
        </defs>
        ${dotsSvg}
    `;
}
