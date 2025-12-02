// --- CONFIGURATION ---
const API_BASE_URL = "http://127.0.0.1:5000/api";

// --- ELEMENTS ---
const fileInput = document.getElementById('file-upload');
const processBtn = document.getElementById('process-btn');
const loadingIndicator = document.getElementById('loading-indicator');
const summaryContent = document.getElementById('summary-content');
const quizContainer = document.getElementById('quiz-container');
const videoList = document.getElementById('video-list');
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const historyList = document.getElementById('history-list'); // NEW
const difficultySelector = document.getElementById('quiz-difficulty');
const generateQuizBtn = document.getElementById('generate-quiz-btn');
const loadMoreBtn = document.getElementById('load-more-btn');
const submitQuizBtn = document.getElementById('submit-quiz');

// --- STATE ---
let totalQuestionsGenerated = 0;
let rawDocumentText = ""; 
let isDocumentIndexed = false;

// --- INITIALIZATION ---
window.addEventListener('DOMContentLoaded', () => {
    fetchHistory(); // Load previous work on startup
});

// --- EVENT LISTENERS ---
// 1. File Selection
// --- EVENT LISTENERS ---

// 1. File Selection (Debug Version)
if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        
        // Debugging: Print to the Console (F12) to prove it works
        console.log("File input changed!"); 
        
        if (file) {
            console.log("File selected:", file.name);
            
            // Force update the text
            const statusText = document.getElementById('file-name');
            statusText.textContent = `✅ Selected: ${file.name}`;
            statusText.style.color = "#10B981"; // Turn text green
            statusText.style.fontWeight = "bold";
            
            // Enable the button
            processBtn.disabled = false;
            processBtn.style.opacity = "1";
            processBtn.style.cursor = "pointer";
        } else {
            console.log("No file selected (User cancelled)");
        }
    });
} else {
    console.error("❌ Error: Could not find the file input element!");
}

processBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    processBtn.disabled = true;
    loadingIndicator.classList.remove('hidden');
    document.getElementById('file-name').textContent = "Uploading & Analyzing...";
    
    // Clear previous state
    quizContainer.innerHTML = '';
    videoList.innerHTML = '';
    chatBox.innerHTML = '<div class="message bot-message">Processing new document...</div>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData });
        
        // Handle Redirects (If session expired)
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const data = await response.json();
        
        if (data.error) throw new Error(data.error);

        rawDocumentText = data.raw_text;
        isDocumentIndexed = true;
        totalQuestionsGenerated = data.quiz.length; 

        updateSummary(data.summary);
        updateQuiz(data.quiz, true);
        updateVideos(data.videos);
        fetchHistory(); // Refresh the sidebar list
        
        document.getElementById('file-name').textContent = "✅ Analysis Complete!";
        
    } catch (error) {
        alert("Error: " + error.message);
        document.getElementById('file-name').textContent = "❌ Failed";
    } finally {
        loadingIndicator.classList.add('hidden');
        processBtn.disabled = false;
    }
});

// Generate Quiz Logic
generateQuizBtn.addEventListener('click', () => { generateQuiz(true); });
loadMoreBtn.addEventListener('click', () => { generateQuiz(false); });

async function generateQuiz(reset) {
    if (!isDocumentIndexed) { alert("Please upload and analyze a document first."); return; }

    const difficulty = difficultySelector.value;
    let count = 10;
    
    if (!reset && totalQuestionsGenerated >= 50) {
        alert("Maximum limit reached.");
        return;
    }

    if (reset) {
        quizContainer.innerHTML = '';
        totalQuestionsGenerated = 0;
        loadMoreBtn.classList.add('hidden');
        submitQuizBtn.classList.add('hidden');
    }
    
    quizContainer.innerHTML += '<div class="spinner-small" style="text-align:center">Loading...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/quiz-more`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: rawDocumentText, difficulty: difficulty, count: count })
        });
        const data = await response.json();
        
        quizContainer.removeChild(quizContainer.lastChild); // Remove spinner
        
        totalQuestionsGenerated += data.quiz.length;
        updateQuiz(data.quiz, false);

    } catch (error) {
        console.error(error);
    }
}

// Chat Logic
document.getElementById('send-btn').addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessageToChat("User", text);
    userInput.value = "";

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text })
        });
        const data = await response.json();
        addMessageToChat("VAULT", data.answer);
    } catch (error) {
        addMessageToChat("System", "❌ Error.");
    }
}

// --- HELPERS ---

async function fetchHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        if (response.redirected) return; // User not logged in
        
        const data = await response.json();
        historyList.innerHTML = "";
        
        if (data.documents.length === 0) {
            historyList.innerHTML = '<li style="padding:10px; color:gray">No history yet.</li>';
            return;
        }

        data.documents.forEach(doc => {
            const li = document.createElement('li');
            li.className = 'history-item';
            li.innerHTML = `📄 ${doc.filename}`;
            // Future: Add click listener to reload this document
            historyList.appendChild(li);
        });
    } catch (e) {
        console.error("History fetch error", e);
    }
}

function updateSummary(text) {
    summaryContent.innerHTML = `<p>${text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`;
}

function updateQuiz(quizData, reset) {
    if (reset) quizContainer.innerHTML = ""; 
    quizData.forEach((q, i) => {
        let idx = totalQuestionsGenerated - quizData.length + i + 1;
        let opts = q.options.map(o => `<label><input type="radio" name="q${idx}"> ${o}</label>`).join('<br>');
        quizContainer.innerHTML += `<div class="quiz-item"><p><strong>${idx}. ${q.question}</strong></p>${opts}<p class="hidden answer">✅ ${q.answer}</p></div>`;
    });
    submitQuizBtn.classList.remove('hidden');
    submitQuizBtn.onclick = () => document.querySelectorAll('.answer').forEach(e => e.classList.remove('hidden'));
    
    if (totalQuestionsGenerated < 50) loadMoreBtn.classList.remove('hidden');
    else loadMoreBtn.classList.add('hidden');
}

function updateVideos(videos) {
    videoList.innerHTML = "";
    if(!videos) return;
    videos.forEach(v => {
        videoList.innerHTML += `
            <div class="video-card">
                <a href="${v.url}" target="_blank">
                    <img src="${v.thumbnail}">
                    <p>${v.title}</p>
                </a>
            </div>`;
    });
}

function addMessageToChat(sender, text) {
    const msg = document.createElement('div');
    msg.className = `message ${sender === "User" ? "user-message" : "bot-message"}`;
    msg.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Tab Switching (Global)
function openTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(e => e.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add("active");
}