import os
import sys
import time
import threading
import webbrowser
import logging
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(message)s')

app = Flask(__name__)
CORS(app)

class Manager:
    def __init__(self):
        self.status = 'running'
        self.start_time = time.time()
        self.sessions = {}
        self.logs = []

    def log(self, msg, level='info'):
        self.logs.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': msg
        })
        if len(self.logs) > 200:
            self.logs = self.logs[-200:]
        print('[' + level.upper() + '] ' + msg)

    def uptime_text(self):
        if self.status != 'running':
            return '0 ثانية'
        s = int(time.time() - self.start_time)
        if s < 60:
            return str(s) + ' ثانية'
        if s < 3600:
            return str(s // 60) + ' دقيقة و' + str(s % 60) + ' ثانية'
        return str(s // 3600) + ' ساعة و' + str((s % 3600) // 60) + ' دقيقة'

    def info(self):
        return {
            'status': self.status,
            'uptime_text': self.uptime_text(),
            'sessions': len(self.sessions),
            'python_version': sys.version.split()[0],
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

manager = Manager()
manager.log('السيرفر بدأ العمل', 'success')

INDEX_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>كاميرا المراقبة</title>
<script src="https://unpkg.com/peerjs@1.5.2/dist/peerjs.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,'Segoe UI',Tahoma,sans-serif;background:#0a0e1a;color:#fff;min-height:100vh;overflow-x:hidden}
.screen{display:none;padding:20px;min-height:100vh}
.screen.active{display:block}
h1{font-size:22px;text-align:center;margin-bottom:20px;color:#4fc3f7}
h2{font-size:16px;margin-bottom:12px;color:#b0bec5}
.btn{display:block;width:100%;padding:16px;background:linear-gradient(135deg,#1976d2,#4fc3f7);color:#fff;border:none;border-radius:12px;font-size:17px;font-weight:600;cursor:pointer;margin-bottom:12px}
.btn.sec{background:linear-gradient(135deg,#37474f,#546e7a)}
.btn.red{background:linear-gradient(135deg,#c62828,#ef5350)}
.btn.grn{background:linear-gradient(135deg,#2e7d32,#66bb6a)}
.card{background:#151b2e;border-radius:14px;padding:18px;margin-bottom:14px;border:1px solid #22304d}
video{width:100%;border-radius:12px;background:#000;max-height:55vh;object-fit:contain}
.info{font-size:13px;color:#90a4ae;text-align:center;line-height:1.6}
.row{display:flex;gap:8px}
.row .btn{flex:1;font-size:14px;padding:12px}
.hidden{display:none!important}
.status{text-align:center;padding:10px;color:#81c784;font-size:14px}
.status.err{color:#ef5350}
.status.warn{color:#ffb74d}
.id-box{background:#0a0e1a;border:2px dashed #4fc3f7;border-radius:14px;padding:22px;text-align:center;margin:12px 0}
.id-val{font-family:'Courier New',monospace;font-size:26px;font-weight:bold;color:#4fc3f7;letter-spacing:2px;word-break:break-all;user-select:all;cursor:pointer}
.copy{display:inline-block;margin-top:12px;padding:8px 18px;background:#1976d2;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer}
.inp{width:100%;padding:16px;background:#0a0e1a;border:2px solid #22304d;border-radius:12px;color:#4fc3f7;font-family:'Courier New',monospace;font-size:20px;font-weight:bold;text-align:center;letter-spacing:2px;outline:none;margin-bottom:12px}
.inp:focus{border-color:#4fc3f7}
#timer{text-align:center;font-size:28px;font-weight:bold;color:#4fc3f7;margin:8px 0;font-variant-numeric:tabular-nums}
.banner{display:flex;align-items:center;justify-content:space-between;background:#151b2e;padding:12px 16px;border-radius:12px;margin-bottom:16px;border:1px solid #22304d;font-size:13px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-left:8px;background:#81c784}
.dot.off{background:#ef5350}
.dot.warn{background:#ffb74d}
.lnk{color:#4fc3f7;text-decoration:none;padding:6px 12px;border:1px solid #22304d;border-radius:8px;font-size:13px}
.badge{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.6);padding:5px 10px;border-radius:20px;font-size:12px}
.video-wrap{position:relative;margin-bottom:12px}
.live-dot{display:inline-block;width:8px;height:8px;background:#f44336;border-radius:50%;margin-left:5px;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.waiting-anim{display:inline-block;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.code-hint{font-size:12px;color:#78909c;text-align:center;margin-top:6px}
.switch-badge{text-align:center;margin-bottom:8px;font-size:13px;color:#4fc3f7}
</style>
</head>
<body>

<div id="home" class="screen active">
  <div class="banner">
    <div><span class="dot" id="srvDot"></span><span id="srvTxt">جاري الفحص...</span></div>
    <a href="/admin" class="lnk">التحكم</a>
  </div>
  <h1>كاميرا المراقبة</h1>
  <div class="card">
    <h2>اختر نوع الجهاز</h2>
    <button class="btn" onclick="goCam()">هذا الجهاز = كاميرا</button>
    <button class="btn sec" onclick="goView()">هذا الجهاز = شاشة مشاهدة</button>
  </div>
  <p class="info">جهاز الكاميرا يعرض معرّف<br>جهاز المشاهدة يكتبه ويدخل</p>
</div>

<div id="cam" class="screen">
  <h1>جهاز الكاميرا</h1>
  <div class="card">
    <h2>1) اختر الكاميرا</h2>
    <div class="row">
      <button id="bR" class="btn" onclick="setFace('environment')">خلفية</button>
      <button id="bF" class="btn sec" onclick="setFace('user')">أمامية</button>
    </div>
    <p class="info" style="margin-top:10px">لن تُشغّل إلا عند اتصال المشاهد</p>
  </div>
  <div class="card">
    <h2>2) شارك المعرّف</h2>
    <div class="id-box">
      <div style="font-size:12px;color:#90a4ae;margin-bottom:10px">معرّف الجلسة</div>
      <div class="id-val" id="sid" onclick="cpy()">----</div>
      <button class="copy" onclick="cpy()">نسخ المعرّف</button>
    </div>
    <div id="timer">05:00</div>
    <div class="status" id="camStat">جاري التحضير...</div>
  </div>
  <div class="card" id="waitCard">
    <p class="info"><span class="waiting-anim">في انتظار المشاهد...</span></p>
  </div>
  <div class="card hidden" id="bcast">
    <h2>جاري البث</h2>
    <div class="video-wrap">
      <video id="lv" autoplay muted playsinline></video>
      <span class="badge">محلي</span>
    </div>
  </div>
  <button class="btn red" onclick="stopCam()">إيقاف والعودة</button>
</div>

<div id="vin" class="screen">
  <h1>مشاهدة الكاميرا</h1>
  <div class="card">
    <h2>اكتب المعرّف</h2>
    <input type="text" id="inp" class="inp" placeholder="cam-XXXXXX" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
    <p class="code-hint">اطلب المعرّف من جهاز الكاميرا</p>
  </div>
  <button class="btn grn" onclick="connect()">اتصال</button>
  <button class="btn sec" onclick="back()">رجوع</button>
  <div class="status" id="vStat"></div>
</div>

<div id="vw" class="screen">
  <h1>مشاهدة مباشرة <span class="live-dot"></span></h1>
  <div class="video-wrap">
    <video id="rv" autoplay playsinline controls></video>
    <span class="badge">متصل</span>
  </div>
  <div class="switch-badge" id="camLbl">الكاميرا: خلفية</div>
  <button class="btn sec" onclick="swCam('environment')">تبديل للخلفية</button>
  <button class="btn sec" onclick="swCam('user')">تبديل للأمامية</button>
  <button class="btn red" onclick="disc()">قطع الاتصال</button>
</div>

<script>
var PEER_CFG = {
  debug: 2,
  host: '0.peerjs.com',
  port: 443,
  path: '/',
  secure: true,
  config: {
    iceServers: [
      {urls: 'stun:stun.l.google.com:19302'},
      {urls: 'stun:stun1.l.google.com:19302'}
    ]
  }
};

var peer = null;
var face = 'environment';
var stream = null;
var timer = null;
var countdown = 300;
var call = null;
var conn = null;
var connected = false;

function show(id) {
  var s = document.querySelectorAll('.screen');
  for (var i = 0; i < s.length; i++) s[i].classList.remove('active');
  document.getElementById(id).classList.add('active');
}

function back() { show('home'); }

function checkSrv() {
  fetch('/api/status')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var dot = document.getElementById('srvDot');
      var txt = document.getElementById('srvTxt');
      if (d.status === 'running') {
        dot.className = 'dot';
        txt.textContent = 'السيرفر يعمل';
      } else {
        dot.className = 'dot off';
        txt.textContent = 'السيرفر متوقف';
      }
    })
    .catch(function() {
      document.getElementById('srvDot').className = 'dot off';
      document.getElementById('srvTxt').textContent = 'خطأ';
    });
}

function genId() {
  var c = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  var s = '';
  for (var i = 0; i < 6; i++) s += c.charAt(Math.floor(Math.random() * c.length));
  return 'cam-' + s;
}

function goCam() {
  show('cam');
  initCam();
}

function initCam() {
  document.getElementById('camStat').textContent = 'جاري التحضير...';
  document.getElementById('camStat').className = 'status';
  document.getElementById('bcast').classList.add('hidden');
  document.getElementById('waitCard').classList.remove('hidden');
  var id = genId();
  document.getElementById('sid').textContent = id;
  createCamPeer(id);
}

function createCamPeer(id) {
  if (peer) { try { peer.destroy(); } catch(e){} }
  peer = new Peer(id, PEER_CFG);
  var opened = false;

  var t = setTimeout(function() {
    if (opened) return;
    document.getElementById('camStat').textContent = 'تأخر - إعادة...';
    var newId = genId();
    document.getElementById('sid').textContent = newId;
    createCamPeer(newId);
  }, 15000);

  peer.on('open', function(openId) {
    opened = true;
    clearTimeout(t);
    document.getElementById('camStat').textContent = 'المعرّف جاهز - بانتظار المشاهد';
    document.getElementById('camStat').className = 'status';
    document.getElementById('sid').textContent = openId;
    fetch('/api/session/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id: openId})
    }).catch(function(){});
    startTimer();
  });

  peer.on('error', function(err) {
    if (err.type === 'unavailable-id') {
      clearTimeout(t);
      var newId = genId();
      document.getElementById('sid').textContent = newId;
      createCamPeer(newId);
    } else if (err.type === 'network' || err.type === 'server-error' || err.type === 'socket-error') {
      clearTimeout(t);
      document.getElementById('camStat').textContent = 'خطأ اتصال - إعادة...';
      document.getElementById('camStat').className = 'status err';
      setTimeout(function() {
        var newId = genId();
        document.getElementById('sid').textContent = newId;
        createCamPeer(newId);
      }, 3000);
    } else {
      clearTimeout(t);
      document.getElementById('camStat').textContent = 'خطأ: ' + err.type;
      document.getElementById('camStat').className = 'status err';
    }
  });

  peer.on('disconnected', function() {
    setTimeout(function() {
      try { if (peer && !peer.destroyed) peer.reconnect(); } catch(e){}
    }, 2000);
  });

  peer.on('call', function(c) {
    document.getElementById('camStat').textContent = 'المشاهد متصل - تشغيل...';
    startStream().then(function(s) {
      c.answer(s);
      call = c;
      document.getElementById('waitCard').classList.add('hidden');
      document.getElementById('bcast').classList.remove('hidden');
      document.getElementById('camStat').textContent = 'جاري البث';
      c.on('close', function() {
        call = null;
        document.getElementById('bcast').classList.add('hidden');
        document.getElementById('waitCard').classList.remove('hidden');
        document.getElementById('camStat').textContent = 'المعرّف جاهز';
        if (stream) {
          stream.getTracks().forEach(function(tk){ tk.stop(); });
          stream = null;
        }
      });
    }).catch(function(e) {
      document.getElementById('camStat').textContent = 'فشل الكاميرا: ' + e.message;
      document.getElementById('camStat').className = 'status err';
    });
  });

  peer.on('connection', function(c) {
    c.on('data', function(data) {
      if (data && data.type === 'switch') {
        setFace(data.facing, true);
      }
    });
  });
}

function startStream() {
  return new Promise(function(resolve, reject) {
    if (stream && stream.active) return resolve(stream);
    navigator.mediaDevices.getUserMedia({
      video: { facingMode: face, width: {ideal: 1280}, height: {ideal: 720} },
      audio: false
    }).then(function(s) {
      stream = s;
      var v = document.getElementById('lv');
      v.srcObject = s;
      v.play().catch(function(){});
      resolve(s);
    }).catch(reject);
  });
}

function setFace(f, silent) {
  face = f;
  document.getElementById('bR').className = 'btn' + (f === 'environment' ? '' : ' sec');
  document.getElementById('bF').className = 'btn' + (f === 'user' ? '' : ' sec');
  if (stream) {
    stream.getTracks().forEach(function(t){ t.stop(); });
    stream = null;
    if (call) {
      startStream().then(function(s) {
        if (call.peerConnection) {
          var senders = call.peerConnection.getSenders();
          for (var i = 0; i < senders.length; i++) {
            if (senders[i].track && senders[i].track.kind === 'video') {
              senders[i].replaceTrack(s.getVideoTracks()[0]);
            }
          }
        }
      });
    }
  }
}

function cpy() {
  var id = document.getElementById('sid').textContent;
  if (!id || id === '----') return;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(id).then(function(){ alert('تم النسخ: ' + id); });
  } else {
    alert('المعرّف: ' + id);
  }
}

function startTimer() {
  countdown = 300;
  if (timer) clearInterval(timer);
  updateTimer();
  timer = setInterval(function() {
    countdown--;
    updateTimer();
    if (countdown <= 0) {
      if (!call) {
        var id = genId();
        document.getElementById('sid').textContent = id;
        createCamPeer(id);
        countdown = 300;
      } else {
        countdown = 300;
      }
    }
  }, 1000);
}

function updateTimer() {
  var m = String(Math.floor(countdown / 60)).padStart(2, '0');
  var s = String(countdown % 60).padStart(2, '0');
  document.getElementById('timer').textContent = m + ':' + s;
}

function stopCam() {
  if (timer) clearInterval(timer);
  if (stream) stream.getTracks().forEach(function(t){ t.stop(); });
  if (call) { try { call.close(); } catch(e){} }
  if (peer) { try { peer.destroy(); } catch(e){} }
  peer = null; stream = null; call = null; timer = null;
  show('home');
}

function goView() {
  show('vin');
  document.getElementById('inp').value = '';
  document.getElementById('vStat').textContent = '';
  setTimeout(function() { document.getElementById('inp').focus(); }, 300);
}

function connect() {
  var input = document.getElementById('inp').value.trim().toLowerCase();
  var st = document.getElementById('vStat');
  if (!input) { st.textContent = 'اكتب المعرّف أولاً'; st.className = 'status err'; return; }
  st.textContent = 'جاري الاتصال...';
  st.className = 'status';

  if (peer) { try { peer.destroy(); } catch(e){} }
  peer = new Peer(PEER_CFG);
  connected = false;

  peer.on('open', function() {
    st.textContent = 'جاري الطلب...';
    conn = peer.connect(input, {reliable: true});
    var c = peer.call(input, new MediaStream());
    call = c;

    c.on('stream', function(remoteStream) {
      connected = true;
      show('vw');
      var v = document.getElementById('rv');
      v.srcObject = remoteStream;
      v.play().catch(function(){});
    });

    c.on('close', function() {
      if (connected) {
        alert('انقطع الاتصال');
        disc();
      }
    });

    setTimeout(function() {
      if (!connected) {
        st.textContent = 'لم يستجب - تحقق من المعرّف';
        st.className = 'status err';
      }
    }, 20000);
  });

  peer.on('error', function(err) {
    if (err.type === 'peer-unavailable') st.textContent = 'المعرّف غير موجود';
    else if (err.type === 'network' || err.type === 'server-error') st.textContent = 'مشكلة اتصال';
    else st.textContent = 'خطأ: ' + err.type;
    st.className = 'status err';
  });

  peer.on('disconnected', function() {
    setTimeout(function() {
      try { if (peer && !peer.destroyed) peer.reconnect(); } catch(e){}
    }, 2000);
  });
}

function swCam(f) {
  if (conn && conn.open) {
    conn.send({type: 'switch', facing: f});
    document.getElementById('camLbl').textContent = 'الكاميرا: ' + (f === 'user' ? 'أمامية' : 'خلفية');
  } else {
    alert('القناة غير جاهزة');
  }
}

function disc() {
  if (call) { try { call.close(); } catch(e){} }
  if (conn) { try { conn.close(); } catch(e){} }
  if (peer) { try { peer.destroy(); } catch(e){} }
  peer = null; call = null; conn = null; connected = false;
  document.getElementById('rv').srcObject = null;
  show('home');
}

window.addEventListener('load', function() {
  checkSrv();
  setInterval(checkSrv, 5000);
});
</script>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>لوحة التحكم</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#0a0e1a;color:#fff;min-height:100vh;padding:20px}
.c{max-width:900px;margin:0 auto}
h1{text-align:center;font-size:26px;color:#4fc3f7;margin-bottom:20px}
.top{display:flex;justify-content:space-between;margin-bottom:20px}
.top a{color:#4fc3f7;text-decoration:none;padding:8px 16px;border:1px solid #22304d;border-radius:8px;font-size:14px}
.card{background:#151b2e;border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #22304d}
.stat{text-align:center;background:linear-gradient(135deg,#151b2e,#1a2340)}
.si{font-size:64px;margin-bottom:12px}
.st{font-size:22px;font-weight:bold;margin-bottom:8px}
.st.r{color:#66bb6a}.st.s{color:#ef5350}.st.e{color:#ef5350}
.sd{color:#90a4ae;font-size:13px;margin-top:8px}
.ctrl{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px}
@media(max-width:600px){.ctrl{grid-template-columns:1fr}}
.cb{padding:20px;border:none;border-radius:14px;font-size:16px;font-weight:bold;cursor:pointer;color:#fff;display:flex;flex-direction:column;align-items:center;gap:8px}
.cb:disabled{opacity:0.4;cursor:not-allowed}
.cs{background:linear-gradient(135deg,#2e7d32,#66bb6a)}
.cp{background:linear-gradient(135deg,#c62828,#ef5350)}
.cr{background:linear-gradient(135deg,#ef6c00,#ffa726)}
.ic{font-size:28px}
.log{background:#0a0e1a;border-radius:12px;padding:16px;max-height:300px;overflow-y:auto;font-family:monospace;font-size:13px;line-height:1.7}
.le{display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #1a2340}
.lt{color:#546e7a;flex-shrink:0}
.ll{font-weight:bold;width:70px;flex-shrink:0}
.ll.info{color:#4fc3f7}.ll.success{color:#66bb6a}.ll.warn{color:#ffb74d}.ll.error{color:#ef5350}
.lm{color:#b0bec5;word-break:break-word}
.ig{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.ii{background:#0a0e1a;padding:14px;border-radius:10px;text-align:center}
.ii .lb{color:#78909c;font-size:12px;margin-bottom:6px}
.ii .vv{color:#4fc3f7;font-size:18px;font-weight:bold}
h2{font-size:16px;color:#b0bec5;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.rb{margin-right:auto;background:#1976d2;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer}
</style>
</head>
<body>
<div class="c">
  <div class="top">
    <a href="/">الموقع الرئيسي</a>
    <span style="color:#4fc3f7;font-weight:bold">لوحة التحكم</span>
  </div>
  <h1>لوحة تحكم السيرفر</h1>
  <div class="card stat">
    <div class="si" id="ic">...</div>
    <div class="st" id="tx">جاري الفحص...</div>
    <div class="sd" id="dt">-</div>
  </div>
  <div class="ctrl">
    <button class="cb cs" id="bs" onclick="doStart()"><span class="ic">&#9654;</span><span>تشغيل</span></button>
    <button class="cb cp" id="bp" onclick="doStop()"><span class="ic">&#9632;</span><span>إيقاف</span></button>
    <button class="cb cr" id="br" onclick="doRestart()"><span class="ic">&#8635;</span><span>إعادة تشغيل</span></button>
  </div>
  <div class="card">
    <h2>معلومات النظام</h2>
    <div class="ig">
      <div class="ii"><div class="lb">مدة التشغيل</div><div class="vv" id="iu">-</div></div>
      <div class="ii"><div class="lb">الجلسات</div><div class="vv" id="is">0</div></div>
      <div class="ii"><div class="lb">Python</div><div class="vv" id="ip">-</div></div>
      <div class="ii"><div class="lb">الوقت</div><div class="vv" id="it">-</div></div>
    </div>
  </div>
  <div class="card">
    <h2>سجل الأحداث <button class="rb" onclick="loadLogs()">تحديث</button></h2>
    <div class="log" id="lg">جاري التحميل...</div>
  </div>
</div>
<script>
function loadStatus() {
  fetch('/api/status').then(function(r){return r.json()}).then(function(d){
    var ic = document.getElementById('ic');
    var tx = document.getElementById('tx');
    var dt = document.getElementById('dt');
    tx.className = 'st';
    if (d.status === 'running') {
      ic.textContent = 'OK';
      tx.textContent = 'السيرفر يعمل';
      tx.classList.add('r');
      dt.textContent = 'يعمل منذ ' + d.uptime_text;
    } else if (d.status === 'stopped') {
      ic.textContent = 'X';
      tx.textContent = 'السيرفر متوقف';
      tx.classList.add('s');
      dt.textContent = 'اضغط تشغيل لبدء الخدمة';
    } else {
      ic.textContent = '!';
      tx.textContent = 'خطأ';
      tx.classList.add('e');
    }
    document.getElementById('iu').textContent = d.uptime_text || '-';
    document.getElementById('is').textContent = d.sessions || 0;
    document.getElementById('ip').textContent = d.python_version || '-';
    document.getElementById('it').textContent = (d.server_time || '').split(' ')[1] || '-';
    document.getElementById('bs').disabled = (d.status === 'running');
    document.getElementById('bp').disabled = (d.status === 'stopped');
  }).catch(function(){});
}
function doStart(){ act('/api/start'); }
function doStop(){ act('/api/stop'); }
function doRestart(){ act('/api/restart'); }
function act(url) {
  fetch(url, {method: 'POST'}).then(function(r){return r.json()}).then(function(d){
    alert(d.message || 'تم');
    setTimeout(function(){ loadStatus(); loadLogs(); }, 500);
  }).catch(function(){ alert('فشل الطلب'); });
}
function loadLogs() {
  fetch('/api/logs?count=50').then(function(r){return r.json()}).then(function(d){
    var logs = d.logs || [];
    var box = document.getElementById('lg');
    if (logs.length === 0) { box.innerHTML = 'لا توجد أحداث'; return; }
    var html = '';
    var rev = logs.slice().reverse();
    for (var i = 0; i < rev.length; i++) {
      var l = rev[i];
      html += '<div class="le"><span class="lt">' + l.time + '</span><span class="ll ' + l.level + '">' + l.level.toUpperCase() + '</span><span class="lm">' + l.message + '</span></div>';
    }
    box.innerHTML = html;
  }).catch(function(){});
}
window.addEventListener('load', function(){
  loadStatus();
  loadLogs();
  setInterval(function(){ loadStatus(); loadLogs(); }, 3000);
});
</script>
</body>
</html>"""

@app.route('/')
def index():
    return Response(INDEX_HTML, mimetype='text/html')

@app.route('/admin')
def admin():
    return Response(ADMIN_HTML, mimetype='text/html')

@app.route('/api/status')
def api_status():
    return jsonify(manager.info())

@app.route('/api/start', methods=['POST'])
def api_start():
    if manager.status == 'running':
        return jsonify({'success': False, 'message': 'السيرفر يعمل بالفعل'})
    manager.status = 'running'
    manager.start_time = time.time()
    manager.log('تم تشغيل السيرفر', 'success')
    return jsonify({'success': True, 'message': 'تم التشغيل'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    if manager.status == 'stopped':
        return jsonify({'success': False, 'message': 'السيرفر متوقف بالفعل'})
    manager.status = 'stopped'
    manager.log('تم إيقاف السيرفر', 'warn')
    return jsonify({'success': True, 'message': 'تم الإيقاف'})

@app.route('/api/restart', methods=['POST'])
def api_restart():
    manager.status = 'running'
    manager.start_time = time.time()
    manager.sessions.clear()
    manager.log('تم إعادة التشغيل', 'info')
    return jsonify({'success': True, 'message': 'تم إعادة التشغيل'})

@app.route('/api/logs')
def api_logs():
    count = int(request.args.get('count', 50))
    return jsonify({'logs': manager.logs[-count:]})

@app.route('/api/session/register', methods=['POST'])
def api_reg():
    data = request.get_json() or {}
    sid = data.get('session_id')
    if sid:
        manager.sessions[sid] = {'created': time.time()}
        manager.log('جلسة جديدة: ' + sid, 'info')
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/session/unregister', methods=['POST'])
def api_unreg():
    data = request.get_json() or {}
    sid = data.get('session_id')
    if sid and sid in manager.sessions:
        del manager.sessions[sid]
        manager.log('أُغلقت الجلسة: ' + sid, 'warn')
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

def open_browser(port):
    time.sleep(1.5)
    try:
        webbrowser.open('http://localhost:' + str(port))
    except:
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print('')
    print('========================================')
    print('  كاميرا المراقبة')
    print('========================================')
    print('  الموقع:  http://localhost:' + str(port))
    print('  التحكم: http://localhost:' + str(port) + '/admin')
    print('========================================')
    print('')
    print('جاري فتح المتصفح تلقائياً...')
    print('لإيقاف السيرفر: اضغط Ctrl+C')
    print('')
    
    if os.environ.get('PORT') is None:
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    app.run(host='127.0.0.0', port=port, debug=False, threaded=True)