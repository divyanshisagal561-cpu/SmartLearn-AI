/* SmartLearn AI Study Plan Interactive Script */

function toggleTask(taskId) {
    const card = document.getElementById(`task-card-${taskId}`);
    const checkbox = document.getElementById(`task-check-${taskId}`);

    fetch(`/api/toggle_task/${taskId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (data.is_completed) {
                card.classList.add("completed");
                if (checkbox) checkbox.checked = true;
                if (data.xp_awarded > 0) {
                    showToast(`+${data.xp_awarded} XP! Great job completing this study task! 🔥`);
                }
            } else {
                card.classList.remove("completed");
                if (checkbox) checkbox.checked = false;
            }
        }
    })
    .catch(err => console.error("Error toggling task:", err));
}

function showToast(msg) {
    let toast = document.getElementById("toast-container");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast-container";
        toast.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #10b981;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-weight: 700;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
            z-index: 3000;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.display = "block";
    toast.style.opacity = "1";
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.style.display = "none", 300);
    }, 3000);
}
