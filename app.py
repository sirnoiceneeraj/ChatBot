from flask import Flask, request, render_template_string, jsonify
button { padding: 8px 12px; }
</style>
</head>
<body>
<h2>SimpleBot</h2>
<div id="chat"></div>
<form id="form" onsubmit="return sendMessage();">
<input id="msg" type="text" placeholder="Type a message..." autocomplete="off" />
<button type="submit">Send</button>
</form>


<script>
const chat = document.getElementById('chat');
function addMessage(text, cls) {
const d = document.createElement('div');
d.className = cls;
d.textContent = text;
chat.appendChild(d);
chat.scrollTop = chat.scrollHeight;
}


async function sendMessage() {
const input = document.getElementById('msg');
const t = input.value.trim();
if (!t) return false;
addMessage('You: ' + t, 'user');
input.value = '';
const res = await fetch('/api/chat', {
method: 'POST', headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ message: t })
});
const data = await res.json();
addMessage('Bot: ' + data.reply, 'bot');
return false; // prevent page reload
}
</script>
</body>
</html>
'''


@app.route('/')
def index():
return render_template_string(HTML)


@app.route('/api/chat', methods=['POST'])
def chat_api():
data = request.get_json(force=True)
message = data.get('message', '')
reply = get_bot_reply(message)
return jsonify({ 'reply': reply })


if __name__ == '__main__':
# debug True for development (auto-reload)
app.run(host='0.0.0.0', port=5000, debug=True)
