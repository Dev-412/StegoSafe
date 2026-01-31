document.getElementById('searchbox').addEventListener('input',function(){
    const query = this.value.trim();

    if (!query) {
        RecentChats()
        return;
    }

    SearchResult(query);
})

function SearchResult(query){
    document.getElementById("searchResults").innerHTML =`<div class="empty-state">Searching...</div>`;

    fetch(`/search?q=${query}`)
    .then(res => res.json())
    .then(data =>{
    let html=""
        data.forEach(users=>{
            html += `<a href="/chat/${ users.username }">
            <div class="search-user">
            <img src="${users.user_profiles.profile_pic}" width="50" height="50" class="rounded-circle object-fit-cover"> <h2>${ users.username }<span class="status-dot online"></span></h2>
            </div>
            </a>`;
        })
        document.getElementById("searchResults").innerHTML=html;
    })
}

function RecentChats() {
    fetch('/recent_chats')
        .then(res => res.json())
        .then(users => {

            const requests = users.map(user =>
                fetch(`/fetch_profile?name=${user}`)
                    .then(res => res.json())
                    .then(pic => {

                        return `
                            <a href="/chat/${user}">
                                <div class="search-user">
                                    <img src="${pic}"
                                         width="50"
                                         height="50"
                                         class="rounded-circle object-fit-cover">
                                    <h2>${user}
                                        <span class="status-dot online"></span>
                                    </h2>
                                </div>
                            </a>
                        `;
                    })
            );

            return Promise.all(requests);
        })
        .then(cards => {

            const header = `
                <div id="emptyState" class="empty-state">
                    🔍 Recent Chats
                </div>
                `;

            document.getElementById("searchResults").innerHTML =
            header + cards.join("");
        });
}
