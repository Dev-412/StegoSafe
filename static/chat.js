let revealed = new Set();

let timestamp = null
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

    if(data.length === 0) return;

    const box = document.getElementById("chatMessages");

    data.forEach(messages => {

        let wrapper = document.createElement("div");
        wrapper.className = messages.receiver == user_name
            ? "message sent"
            : "message received";
            
        wrapper.id = "msg-" + messages.id;

        wrapper.innerHTML = `
            <div class="stego-box" id="box-${messages.id}">
                <img src="${messages.image_url}" class="chat-image">
                <button class="reveal-btn"
                    onclick="revealMsg('${messages.id}')">Reveal</button>
            </div>
            <div class="revealed-text" id="txt-${messages.id}" style="display:none;"></div>
        `;

        box.appendChild(wrapper);

        timestamp = messages.time;
    });

    box.scrollTop = box.scrollHeight;
}

    
function revealMsg(id){

    fetch(`/reveal_message?id=${id}`)
      .then(res => res.json())
      .then(data => {

          if(!data.text){
              alert("Failed to reveal");
              return;
          }

          // remember revealed
          revealed.add(id);

          // hide image box
          document.getElementById("box-"+id).style.display = "none";

          // show text
          const txt = document.getElementById("txt-"+id);
          txt.style.display = "block";
          txt.innerText = data.text;
      });
}



