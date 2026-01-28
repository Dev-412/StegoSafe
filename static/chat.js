let timestamp = null


    //runs when u send msg
    function send(event){
        if(document.getElementById("message").value.trim() === ""){
            event.preventDefault();
        }
        else{
            event.preventDefault();
            let msg =document.getElementById("message").value
            console.log(msg)
            
            fetch(`/send_message?msg=${msg}&receiver=${user_name}`)
            .then(() => fetchMessages());
            document.getElementById("message").value = "";
            // auto scroll bottom
            document.getElementById("chatMessages").scrollTop = document.getElementById("chatMessages").scrollHeight;
        }
    }

    setInterval(fetchMessages, 2000);
    //fetches every msg every 2 sec
    function fetchMessages() {

    fetch(`/get_messages?receiver=${(user_name)}`)
        .then(res => res.json())
        .then(data => renderMessages(data));
    }

    function renderMessages(data) {

    let html = "";

    data.forEach(messages=>{
        if(messages['receiver']==user_name){
            html+=`<div class="message sent">
                    <p>${messages['image_url']}</p>
                    </div>`
            }
        else{
                html+=`<div class="message received">
                    <p>${messages['image_url']}</p>
                </div>`
        }
    })

    const box = document.getElementById("chatMessages");

    box.innerHTML = html;

    
}
