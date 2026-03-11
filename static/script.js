/* ═══════════════════════════════════════════════════════════════════════
   Clinical RAG Assistant – Premium Chat UI Logic  (v3)
   Features: streaming, collapsible sources, clickable PDF links,
   timestamps, debug panel, knowledge base list, file upload with progress,
   PDF preview modal, message animations
   ═══════════════════════════════════════════════════════════════════════ */

(() => {
    "use strict";

    // ── State ───────────────────────────────────────────────────────────
    let debugMode = false;

    // ── DOM refs ────────────────────────────────────────────────────────
    const chatMessages = document.getElementById("chat-messages");
    const welcomeScreen = document.getElementById("welcome-screen");
    const thinkingBar = document.getElementById("thinking-indicator");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("sidebar");
    const debugToggle = document.getElementById("debug-toggle");
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file-input");
    const uploadProgress = document.getElementById("upload-progress");
    const uploadStatus = document.getElementById("upload-status");
    const pdfModal = document.getElementById("pdf-modal");
    const pdfFrame = document.getElementById("pdf-frame");
    const modalClose = document.getElementById("modal-close");
    const modalBackdrop = pdfModal ? pdfModal.querySelector(".modal-backdrop") : null;
    const modalTitle = document.getElementById("modal-title");
    const docList = document.getElementById("doc-list");

    // ── Init ──────────────────────────────────────────────────────────
    loadDocumentList();

    // ── Auto-resize textarea ────────────────────────────────────────────
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 150) + "px";
    });

    // ── Submit on Enter (Shift+Enter = newline) ─────────────────────────
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // ── Example prompt buttons ──────────────────────────────────────────
    document.querySelectorAll(".example-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            userInput.value = btn.dataset.prompt;
            userInput.dispatchEvent(new Event("input"));
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // ── Sidebar toggle (mobile) ─────────────────────────────────────────
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }

    // ── New chat ────────────────────────────────────────────────────────
    if (newChatBtn) {
        newChatBtn.addEventListener("click", async () => {
            await fetch("/reset", { method: "POST" });
            chatMessages.innerHTML = "";
            chatMessages.appendChild(welcomeScreen);
            welcomeScreen.style.display = "";
        });
    }

    // ── Debug toggle ────────────────────────────────────────────────────
    if (debugToggle) {
        debugToggle.addEventListener("click", () => {
            debugMode = !debugMode;
            debugToggle.classList.toggle("active", debugMode);
            document.querySelectorAll(".debug-panel").forEach((p) =>
                p.classList.toggle("visible", debugMode)
            );
        });
    }

    // ══════════════════ KNOWLEDGE BASE ══════════════════════════════════

    async function loadDocumentList() {
        if (!docList) return;
        try {
            const res = await fetch("/api/documents");
            const docs = await res.json();
            if (!docs.length) {
                docList.innerHTML = `<div class="doc-list-loading">No documents indexed yet.</div>`;
                return;
            }
            docList.innerHTML = docs.map((name) => `
                <div class="doc-item" title="${name}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <span class="doc-item-name">${name}</span>
                </div>
            `).join("");
        } catch {
            docList.innerHTML = `<div class="doc-list-loading">Could not load documents.</div>`;
        }
    }

    // ══════════════════ FILE UPLOAD ═════════════════════════════════════

    if (uploadZone && fileInput) {
        uploadZone.addEventListener("click", () => fileInput.click());

        uploadZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadZone.classList.add("drag-over");
        });
        uploadZone.addEventListener("dragleave", () =>
            uploadZone.classList.remove("drag-over")
        );
        uploadZone.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadZone.classList.remove("drag-over");
            if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files.length) {
                handleUpload(fileInput.files[0]);
                fileInput.value = "";
            }
        });
    }

    async function handleUpload(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showStatus("Only PDF files are accepted.", "error");
            return;
        }

        // Show progress
        showProgress(file.name);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/upload", { method: "POST", body: formData });
            const data = await res.json();
            hideProgress();

            if (data.status === "ok") {
                showStatus(
                    `✓ ${data.filename} uploaded — ${data.pages} pages, ${data.chunks} chunks indexed.`,
                    "success"
                );
                loadDocumentList(); // Refresh the knowledge base list
            } else {
                showStatus(`✗ ${data.error || data.message}`, "error");
            }
        } catch (err) {
            hideProgress();
            showStatus(`✗ Upload failed: ${err.message}`, "error");
        }
    }

    function showProgress(name) {
        if (!uploadProgress) return;
        uploadProgress.classList.remove("hidden");
        uploadProgress.querySelector(".upload-progress-text").textContent = `Uploading ${name}…`;
        const fill = uploadProgress.querySelector(".upload-progress-fill");
        fill.style.width = "0%";
        // Animate progress
        let w = 0;
        const iv = setInterval(() => {
            w += Math.random() * 15;
            if (w > 90) w = 90;
            fill.style.width = w + "%";
            if (w >= 90) clearInterval(iv);
        }, 300);
        uploadProgress._interval = iv;
    }

    function hideProgress() {
        if (!uploadProgress) return;
        clearInterval(uploadProgress._interval);
        const fill = uploadProgress.querySelector(".upload-progress-fill");
        fill.style.width = "100%";
        setTimeout(() => uploadProgress.classList.add("hidden"), 600);
    }

    function showStatus(msg, type) {
        if (!uploadStatus) return;
        uploadStatus.textContent = msg;
        uploadStatus.className = `upload-status ${type}`;
        setTimeout(() => uploadStatus.classList.add("hidden"), 7000);
    }

    // ══════════════════ PDF PREVIEW MODAL ═══════════════════════════════

    function openPreview(url, title) {
        if (!pdfModal || !pdfFrame) return;
        pdfFrame.src = url;
        if (modalTitle) modalTitle.textContent = title || "Document Preview";
        pdfModal.classList.remove("hidden");
    }

    function closePreview() {
        if (!pdfModal) return;
        pdfModal.classList.add("hidden");
        if (pdfFrame) pdfFrame.src = "";
    }

    if (modalClose) modalClose.addEventListener("click", closePreview);
    if (modalBackdrop) modalBackdrop.addEventListener("click", closePreview);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closePreview();
    });

    // ══════════════════ HELPERS ═════════════════════════════════════════

    function scrollBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideWelcome() {
        if (welcomeScreen) welcomeScreen.style.display = "none";
    }

    function timeNow() {
        return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function esc(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function md(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            .replace(/`(.+?)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
    }

    // ─── Create message row ──────────────────────────────────────────

    function addMessage(role, html) {
        const row = document.createElement("div");
        row.className = `message-row ${role}`;

        const avatar = document.createElement("div");
        avatar.className = "msg-avatar";
        avatar.innerHTML = role === "user"
            ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
            : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`;

        const content = document.createElement("div");
        content.className = "msg-content";

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.innerHTML = html;

        const time = document.createElement("span");
        time.className = "msg-time";
        time.textContent = timeNow();

        content.appendChild(bubble);
        content.appendChild(time);
        row.appendChild(avatar);
        row.appendChild(content);
        chatMessages.appendChild(row);
        scrollBottom();

        return { bubble, content };
    }

    // ─── Collapsible sources ──────────────────────────────────────────

    function buildSources(sources) {
        if (!sources || !sources.length) return null;

        const wrap = document.createElement("div");
        wrap.className = "sources-wrap";

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "sources-toggle";
        toggle.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            Sources (${sources.length})
            <svg class="sources-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
        `;

        const body = document.createElement("div");
        body.className = "sources-body";

        sources.forEach((s) => {
            const a = document.createElement("a");
            a.className = "source-link";
            const pdfUrl = `/static/pdfs/${encodeURIComponent(s.document)}#page=${s.page}`;
            a.href = pdfUrl;
            a.target = "_blank";
            a.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                ${s.document}
                <span class="source-page">p. ${s.page}</span>
            `;
            a.addEventListener("click", (e) => {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    openPreview(pdfUrl, s.document);
                }
            });
            body.appendChild(a);
        });

        toggle.addEventListener("click", () => {
            toggle.classList.toggle("open");
            body.classList.toggle("open");
        });

        wrap.appendChild(toggle);
        wrap.appendChild(body);
        return wrap;
    }

    // ─── Debug panel ─────────────────────────────────────────────────

    function buildDebugPanel(chunks) {
        if (!chunks || !chunks.length) return null;

        const panel = document.createElement("div");
        panel.className = `debug-panel${debugMode ? " visible" : ""}`;

        let html = `<div class="debug-title"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg> Retrieved Chunks</div>`;
        chunks.forEach((c, i) => {
            html += `<div class="debug-chunk">
                <div class="debug-meta">#${i + 1} — ${c.source || "?"}, p. ${c.page || "?"}${c.score != null ? `<span class="debug-score">${c.score}</span>` : ""}</div>
                <div class="debug-text">${esc(c.content || "")}</div>
            </div>`;
        });
        panel.innerHTML = html;
        return panel;
    }

    // ══════════════════ FORM SUBMISSION ═════════════════════════════════

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;

        hideWelcome();
        addMessage("user", md(question));
        userInput.value = "";
        userInput.style.height = "auto";
        sendBtn.disabled = true;

        thinkingBar.classList.remove("hidden");
        scrollBottom();

        try {
            const res = await fetch("/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question }),
            });

            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const { bubble, content } = addMessage("assistant", "");
            thinkingBar.classList.add("hidden");

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullAnswer = "";
            let sources = [];
            let debugChunks = [];

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const payload = line.slice(6).trim();
                    if (!payload) continue;

                    try {
                        const data = JSON.parse(payload);
                        if (data.token) {
                            fullAnswer += data.token;
                            bubble.innerHTML = md(fullAnswer);
                            scrollBottom();
                        }
                        if (data.done) {
                            if (data.sources) sources = data.sources;
                            if (data.debug_chunks) debugChunks = data.debug_chunks;
                        }
                    } catch (_) { /* skip */ }
                }
            }

            // Append sources card
            const srcEl = buildSources(sources);
            if (srcEl) content.appendChild(srcEl);

            // Append debug panel
            const dbgEl = buildDebugPanel(debugChunks);
            if (dbgEl) content.appendChild(dbgEl);

            scrollBottom();
        } catch (err) {
            thinkingBar.classList.add("hidden");
            addMessage(
                "assistant",
                `<span style="color:var(--danger)">⚠ ${err.message || "Something went wrong."}</span>`
            );
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
})();
