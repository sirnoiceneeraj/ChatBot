from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# --- SIMPLE BOT LOGIC ---
def get_bot_reply(message: str) -> str:
    msg = message.strip().lower()
    if msg in ["hi", "hello", "hey"]:
        return "Hello! I'm SimpleBot. 🙂"
    if "time" in msg:
        from datetime import datetime
        return datetime.now().strftime("It's %Y-%m-%d %H:%M:%S right now.")
    if "joke" in msg:
        return "Why did the programmer quit his job? Because he didn't get arrays. 😅"
    if "thanks" in msg or "thank you" in msg:
        return "You're welcome! Glad to help."
    # fallback: short echo + suggestion
    return f"I heard: \"{message}\" — ask me for 'time' or 'joke'!"

# --- HTML PAGE (INSIDE TRIPLE QUOTES) ---
HTML = '''
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>SimpleBot — Interactive</title>
<meta name="viewport" content="width=device-width,initial-scale=1" />
<style>
  :root{
    --bg:#f6f8fb; --card:#ffffff; --accent:#0b63d3;
    --user:#0b63d3; --bot:#222; --muted:#6b7280;
  }
  body { font-family: Inter, system-ui, Arial; background:var(--bg); margin:0; padding:24px; display:flex; justify-content:center; }
  .container { width:100%; max-width:720px; }
  .card { background:var(--card); border-radius:14px; box-shadow:0 6px 20px rgba(15,23,42,0.08); padding:16px; display:flex; flex-direction:column; height:76vh; min-height:480px; }
  header { display:flex; align-items:center; gap:12px; padding-bottom:8px; border-bottom:1px solid #eee; }
  .title { font-weight:600; font-size:18px; }
  #chat { flex:1; padding:12px; overflow:auto; display:flex; flex-direction:column; gap:10px; }
  .row { display:flex; gap:10px; align-items:flex-end; }
  .row.user { justify-content:flex-end; }
  .bubble { max-width:72%; padding:10px 12px; border-radius:12px; box-shadow:0 2px 6px rgba(2,6,23,0.06); animation:fadeIn .18s ease; position:relative; }
  .bubble.bot { background:#f3f4f6; color:var(--bot); border-bottom-left-radius:4px; }
  .bubble.user { background:var(--user); color:#fff; border-bottom-right-radius:4px; }
  .meta { font-size:11px; color:var(--muted); margin-top:6px; display:flex; gap:8px; align-items:center; }
  .avatar { width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; color:#fff; flex-shrink:0; }
  .avatar.bot { background:#9ca3ff; }
  .avatar.user { background:var(--user); }
  .typing { font-style:italic; color:var(--muted); padding-left:8px; }
  .controls { margin-top:12px; display:flex; gap:8px; align-items:center; }
  textarea { flex:1; resize:none; padding:10px 12px; border-radius:10px; border:1px solid #e6e9ef; min-height:48px; font-size:14px; }
  button.send { background:var(--accent); color:#fff; border:none; padding:10px 14px; border-radius:10px; cursor:pointer; font-weight:600; }
  button.send[disabled] { opacity:0.6; cursor:not-allowed; }
  .timestamp { font-size:11px; color:var(--muted); margin-left:6px; }
  .hint { font-size:12px; color:var(--muted); margin-left:6px; }
  @keyframes dots {
    0% { content:'.'; }
    33% { content:'..'; }
    66% { content:'...'; }
  }
  .dots::after {
    content:'.';
    animation: dots 1s steps(3,end) infinite;
    margin-left:6px;
  }
  @keyframes fadeIn {
    from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; }
  }
  /* small screens */
  @media (max-width:520px){
    .card{ height:78vh; padding:12px; }
    .bubble{ max-width:86%; }
  }
</style>
</head>
<body>
  <div class="container">
    <div class="card" role="region" aria-label="Chat with SimpleBot">
      <header>
        <div class="avatar bot">B</div>
        <div>
          <div class="title">SimpleBot</div>
          <div class="hint">Try: <strong>time</strong>, <strong>joke</strong>, or say <strong>hi</strong></div>
        </div>
      </header>

      <div id="chat" aria-live="polite"></div>

      <div class="controls" role="form" aria-label="Message input area">
        <textarea id="msg" placeholder="Type a message — Enter to send, Shift+Enter for newline"></textarea>
        <button id="sendBtn" class="send">Send</button>
      </div>
    </div>
  </div>

<script>
/* Client-side logic: message rendering, typing indicator, localStorage persistence,
   Enter-to-send (Shift+Enter -> newline), disabled send while sending. */

const chat = document.getElementById('chat');
const textarea = document.getElementById('msg');
const sendBtn = document.getElementById('sendBtn');

let sending = false;
let history = [];

// utility: format time like 14:32
function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// save / load from localStorage
function loadHistory() {
  try {
    const raw = localStorage.getItem('simplebot_history');
    if (raw) history = JSON.parse(raw);
    else history = [];
  } catch(e){ history = []; }
}

function saveHistory() {
  try {
    localStorage.setItem('simplebot_history', JSON.stringify(history));
  } catch(e){}
}

// render a single message object: {who: 'user'|'bot', text: '...', time: 'HH:MM'}
function renderMessage(msgObj) {
  const row = document.createElement('div');
  row.className = 'row ' + (msgObj.who === 'user' ? 'user' : 'bot');

  const avatar = document.createElement('div');
  avatar.className = 'avatar ' + (msgObj.who === 'user' ? 'user' : 'bot');
  avatar.textContent = (msgObj.who === 'user') ? 'Y' : 'B';

  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';
  wrapper.style.alignItems = (msgObj.who === 'user') ? 'flex-end' : 'flex-start';

  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (msgObj.who === 'user' ? 'user' : 'bot');
  bubble.innerHTML = msgObj.text.replace(/\\n/g, '<br>');

  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.innerHTML = `<span class="timestamp">${msgObj.time}</span>`;

  wrapper.appendChild(bubble);
  wrapper.appendChild(meta);

  if (msgObj.who === 'user') {
    row.appendChild(wrapper);
    row.appendChild(avatar);
  } else {
    row.appendChild(avatar);
    row.appendChild(wrapper);
  }

  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

// show typing indicator (bot)
let typingRow = null;
function showTyping() {
  if (typingRow) return;
  typingRow = document.createElement('div');
  typingRow.className = 'row bot';
  const avatar = document.createElement('div');
  avatar.className = 'avatar bot';
  avatar.textContent = 'B';
  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';
  wrapper.style.alignItems = 'flex-start';
  const bubble = document.createElement('div');
  bubble.className = 'bubble bot typing';
  bubble.textContent = 'Bot is typing';
  const span = document.createElement('span');
  span.className = 'dots';
  bubble.appendChild(span);
  wrapper.appendChild(bubble);
  chat.appendChild(typingRow);
  typingRow.appendChild(avatar);
  typingRow.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

function hideTyping() {
  if (typingRow) {
    chat.removeChild(typingRow);
    typingRow = null;
  }
}

// render whole history
function renderHistory() {
  chat.innerHTML = '';
  for (const m of history) renderMessage(m);
}

// add message to history + render + save
function pushMessage(who, text) {
  const obj = { who, text, time: nowTime() };
  history.push(obj);
  renderMessage(obj);
  saveHistory();
}

// handle send
async function sendMessage() {
  const text = textarea.value.trim();
  if (!text || sending) return;
  // push user message
  pushMessage('user', textarea.value);
  textarea.value = '';
  textarea.focus();

  // prepare UI
  sending = true;
  sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: text })
    });
    hideTyping();
    if (!res.ok) {
      pushMessage('bot', '(Server error — try again)');
    } else {
      const data = await res.json();
      // small delay to feel more natural
      await new Promise(r => setTimeout(r, 350));
      pushMessage('bot', data.reply);
    }
  } catch (err) {
    hideTyping();
    pushMessage('bot', '(Network error)');
    console.error(err);
  } finally {
    sending = false;
    sendBtn.disabled = false;
  }
}

// keyboard handling: Enter to send, Shift+Enter newline
textarea.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// send button
sendBtn.addEventListener('click', (e) => {
  e.preventDefault();
  sendMessage();
});

// load history on startup
loadHistory();
renderHistory();

// focus input
textarea.focus();
</script>
</body>
</html>
'''

# --- ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json(force=True)
    message = data.get('message', '')
    reply = get_bot_reply(message)
    return jsonify({ 'reply': reply })

# --- START SERVER ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
