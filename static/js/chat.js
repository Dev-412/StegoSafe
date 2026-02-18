let revealed = new Set();

let timestamp = null
let html = "";

//runs when u send msg
function send(event) {
    if (document.getElementById("message").value.trim() === "") {
        event.preventDefault();
    }
    else {
        event.preventDefault();
        let msg = document.getElementById("message").value
        lastView = new Date().toISOString();

        fetch(`/send_message?msg=${msg}&receiver=${user_name}`)
        // .then(() => fetchMessages());
        document.getElementById("message").value = "";

    }
}

setInterval(fetchMessages, 2000);
//fetches every msg every 2 sec
function fetchMessages() {

    fetch(`/get_messages?receiver=${(user_name)}&timestamp=${timestamp}`)
        .then(res => res.json())
        .then(data => renderMessages(data));
}

function renderMessages(data) {

    if (data.length === 0) return;

    const box = document.getElementById("chatMessages");

    data.forEach(messages => {

        // 🚫 skip duplicates
        if (document.getElementById("msg-" + messages.id)) {
            return;
        }

        let wrapper = document.createElement("div");

        // Styling for Sent vs Received
        const isMe = messages.receiver == user_name; // wait, logic check
        // If receiver is the other person (user_name), then I sent it.
        // Logic from original: 
        // wrapper.className = messages.receiver == user_name ? "message sent" : "message received";
        // Yes.

        const isSent = messages.receiver == user_name;

        wrapper.className = `flex w-full ${isSent ? 'justify-end' : 'justify-start'} animate-slide-in`;
        wrapper.id = "msg-" + messages.id;

        const bubbleClass = isSent
            ? "glass-panel bg-purple-500/20 border-purple-500/30 text-white" // Sent: Purple tint
            : "glass-panel bg-slate-900/40 border-slate-700/30 text-slate-100"; // Received: Darker glass

        wrapper.innerHTML = messages.revealed
            ? `
                <div class="max-w-[80%] md:max-w-[60%] p-4 ${bubbleClass} shadow-md relative group">
                    <p class="text-sm md:text-base text-slate-200 font-medium break-words">${messages.text}</p>
                    <div class="flex items-center justify-end gap-1 mt-1 opacity-60">
                         <svg class="w-3 h-3 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                         <span class="text-[10px] text-slate-400">Decrypted</span>
                    </div>
                </div>
              `
            : `
                <div class="max-w-[80%] md:max-w-[60%] space-y-2">
                    <!-- Stego Image Box -->
                    <div class="glass-panel p-2 rounded-xl relative group transition-all hover:scale-[1.01]" id="box-${messages.id}">
                        <img src="${messages.image_url}" class="rounded-lg w-full max-h-64 object-cover border border-slate-700/50">
                        
                        <!-- Overlay Reveal Button -->
                        <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg">
                            <button onclick="revealMsg('${messages.id}')" 
                                class="px-4 py-2 bg-brand-500 text-slate-900 text-sm font-bold rounded-lg shadow-[0_0_15px_rgba(20,184,166,0.4)] hover:scale-105 transition-transform flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                Reveal Secret
                            </button>
                        </div>
                        
                        <div class="absolute bottom-2 right-2 px-2 py-1 bg-black/60 rounded text-[10px] text-white backdrop-blur-sm pointer-events-none">
                            Stego Image
                        </div>
                    </div>
                    
                    <!-- Hidden Text Container (Appears after reveal) -->
                    <div id="txt-${messages.id}" class="hidden p-4 ${bubbleClass} shadow-md animate-fade-in">
                        <!-- Content injected by revealMsg -->
                    </div>
                </div>
              `;

        box.appendChild(wrapper);

        timestamp = messages.time;
    });

    box.scrollTop = box.scrollHeight;
}



function revealMsg(id) {

    fetch(`/reveal_message?id=${id}`)
        .then(res => res.json())
        .then(data => {

            if (!data.text) {
                alert("Failed to reveal");
                return;
            }

            // remember revealed
            revealed.add(id);

            // hide image box
            document.getElementById("box-" + id).style.display = "none";

            // show text
            const txt = document.getElementById("txt-" + id);
            txt.classList.remove("hidden");
            txt.innerHTML = `
                <p class="text-sm md:text-base text-slate-200 font-medium break-words">${data.text}</p>
                <div class="flex items-center justify-end gap-1 mt-1 opacity-60">
                     <svg class="w-3 h-3 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" /></svg>
                     <span class="text-[10px] text-slate-400">Revealed</span>
                </div>
            `;
        });
}



