let recentTimer = null;
let lastRecentUsers = [];


function startRecentPolling() {

    if (recentTimer) return; // already running

    RecentChats();

    recentTimer = setInterval(RecentChats, 2000);
}

function stopRecentPolling() {
    if (recentTimer) {
        clearInterval(recentTimer);
        recentTimer = null;
    }
}

startRecentPolling();

document.getElementById('searchbox').addEventListener('input', function () {
    const query = this.value.trim();

    if (!query) {
        stopRecentPolling();     // reset polling state
        lastRecentUsers = [];    // 🔥 force rebuild
        startRecentPolling();    // rebuild + poll
        return;
    }

    stopRecentPolling();
    SearchResult(query);
})

function SearchResult(query) {

    document.getElementById("searchResults").innerHTML =
        `<div class="text-center py-12 text-slate-500 animate-pulse">Searching...</div>`;

    fetch(`/search?q=${query}`)
        .then(res => res.json())
        .then(data => {

            let html = "";

            if (data.length === 0) {
                html = `
                    <div class="text-center py-12">
                        <p class="text-slate-500">No users found matching "${query}"</p>
                    </div>
                `;
            } else {
                data.forEach(users => {
                    html += `
                        <a href="/chat/${users.username}" class="block group">
                            <div class="flex items-center gap-4 p-4 rounded-xl glass-panel hover:bg-slate-800/80 transition-all duration-300 chat-user" data-username="${users.username}">
                                <div class="relative">
                                    <img src="${users.user_profiles.profile_pic}" 
                                         class="w-14 h-14 rounded-full object-cover border-2 border-slate-700 group-hover:border-brand-500 transition-colors">
                                    <span class="status-dot absolute bottom-0 right-0 w-3.5 h-3.5 ${users.user_profiles.status ? 'bg-green-500' : 'bg-slate-500'} border-2 border-slate-900 rounded-full"></span>
                                </div>
                                
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between items-baseline mb-1">
                                        <h3 class="text-lg font-semibold text-main group-hover:text-brand-400 transition-colors chat-name">${users.username}</h3>
                                        <span class="unseen-badge hidden bg-brand-500 text-slate-900 text-xs font-bold px-2 py-0.5 rounded-full">New</span>
                                    </div>
                                    <p class="text-sm text-muted truncate">${users.user_profiles.bio || 'No bio available'}</p>
                                </div>
                                
                                <svg class="w-5 h-5 text-muted group-hover:text-brand-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </a>
                    `;
                });
            }

            document.getElementById("searchResults").innerHTML = html;
            loadUnrevealedCounts();
        });
}


function RecentChats() {

    fetch('/recent_chats')
        .then(res => res.json())
        .then(users => {

            if (JSON.stringify(users) === JSON.stringify(lastRecentUsers)) {
                loadUnrevealedCounts();
                return Promise.resolve(null);
            }

            lastRecentUsers = users;

            const requests = users.map(user =>
                fetch(`/fetch_profile?name=${user}`)
                    .then(res => res.json())
                    .then(data => `
                        <a href="/chat/${user}" class="block group">
                            <div class="flex items-center gap-4 p-4 rounded-xl glass-panel hover:bg-slate-800/80 transition-all duration-300 chat-user" data-username="${user}">
                                <div class="relative">
                                    <img src="${data.pfp}" 
                                         class="w-14 h-14 rounded-full object-cover border-2 border-slate-700 group-hover:border-brand-500 transition-colors">
                                    <span class="status-dot absolute bottom-0 right-0 w-3.5 h-3.5 ${data.status ? 'bg-green-500' : 'bg-slate-500'} border-2 border-slate-900 rounded-full"></span>
                                </div>
                                
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between items-baseline mb-1">
                                        <h3 class="text-lg font-semibold text-main group-hover:text-brand-400 transition-colors chat-name">${user}</h3>
                                        <span class="unseen-badge hidden bg-brand-500 text-slate-900 text-xs font-bold px-2 py-0.5 rounded-full">New</span>
                                    </div>
                                    <p class="text-sm text-muted truncate">Tap to chat with ${user}</p>
                                </div>
                                
                                <svg class="w-5 h-5 text-muted group-hover:text-brand-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </a>
                    `)
            );

            return Promise.all(requests);
        })
        .then(cards => {

            if (!cards) return;

            const header = `
                <div class="mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <h2 class="text-lg font-bold text-main">Recent Chats</h2>
                </div>
            `;

            document.getElementById("searchResults").innerHTML =
                header + '<div class="grid gap-3">' + cards.join("") + '</div>';

            loadUnrevealedCounts();
        })
        .catch(err => console.error("RecentChats error:", err));
}



function loadUnrevealedCounts() {

    fetch("/unrevealed_counts")
        .then(res => res.json())
        .then(counts => {

            document.querySelectorAll(".chat-user").forEach(el => {

                const name = el.dataset.username;

                const badge = el.querySelector(".unseen-badge");

                if (counts[name]) {
                    badge.innerText = counts[name];
                    badge.style.display = "inline-block";
                } else {
                    badge.style.display = "none";
                }
            });
        });
}

