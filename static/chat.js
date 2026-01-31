let timestamp = null
let lastView = null
let html = "";

    //runs when u send msg
    function send(event){
        if(document.getElementById("message").value.trim() === ""){
            event.preventDefault();
        }
        else{
            event.preventDefault();
            let msg =document.getElementById("message").value
            lastView = new Date().toISOString();
            
            fetch(`/send_message?msg=${msg}&receiver=${user_name}&lastView=${lastView}`)
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
        let new_chat=false
        data.forEach(messages=>{
            if(messages['receiver']==user_name){ //receiver = person we are chatting to
                html+=`<div class="message sent">
                    <p>${messages['image_url']}</p>
                    </div>`
                new_chat=true
            }
            else{
                html+=`<div class="message received">
                    <p>${messages['image_url']}</p>
                    </div>`
                new_chat=true
            }
            timestamp=messages['time']
        })

    const box = document.getElementById("chatMessages");

    box.innerHTML = html;

    if(new_chat==true){
        // auto scroll bottom
        document.getElementById("chatMessages").scrollTop = document.getElementById("chatMessages").scrollHeight;
    } 
}
