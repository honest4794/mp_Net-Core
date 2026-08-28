/* NetBus WebMaster 前端 */
(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  let uiWs = null;          // /ws/ui
  let activeSlave = null;   // 目前選中的 slave_id
  let currentAudio = null;  // 目前播放的 mp3 name

  const terminal = $("#terminal");
  const deviceList = $("#deviceList");
  const connState = $("#connState");

  // ── 終端 log ──────────────────────────────────────────────
  function log(msg, level) {
    const div = document.createElement("div");
    div.className = "t-line t-" + (level || "info");
    div.textContent = "[" + new Date().toLocaleTimeString() + "] " + msg;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
    while (terminal.children.length > 500) terminal.removeChild(terminal.firstChild);
  }

  // ── WebSocket 連線 ─────────────────────────────────────────
  function connectUI() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    uiWs = new WebSocket(`${proto}://${location.host}/ws/ui`);
    uiWs.onopen = () => { connState.textContent = "已連線"; connState.className = "conn-state on"; log("UI 已連線", "ok"); };
    uiWs.onclose = () => { connState.textContent = "未連線"; connState.className = "conn-state off"; log("UI 已斷線", "warn"); setTimeout(connectUI, 2000); };
    uiWs.onerror = () => log("WS 錯誤", "err");
    uiWs.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      handleMsg(msg);
    };
  }

  function sendUI(obj) {
    if (uiWs && uiWs.readyState === WebSocket.OPEN) uiWs.send(JSON.stringify(obj));
    else log("UI 未連線, 無法送出指令", "err");
  }

  function handleMsg(msg) {
    switch (msg.type) {
      case "device_list": renderDevices(msg.data || []); break;
      case "ok": log("✅ " + (msg.action || "") + (msg.sha ? " sha=" + msg.sha.slice(0, 8) : ""), "ok"); break;
      case "error": log("❌ " + msg.err, "err"); break;
      case "pong": break;
      default: log("⬅ " + JSON.stringify(msg), "info");
    }
  }

  // ── 設備清單 ──────────────────────────────────────────────
  function renderDevices(devices) {
    deviceList.innerHTML = "";
    if (!devices.length) {
      const li = document.createElement("li");
      li.textContent = "(無在線設備)";
      li.style.cursor = "default";
      deviceList.appendChild(li);
      return;
    }
    devices.forEach((d) => {
      const li = document.createElement("li");
      if (d.slave_id === activeSlave) li.className = "active";
      const dot = document.createElement("span");
      dot.className = "dot" + (d.online ? "" : " offline");
      const name = document.createElement("span");
      name.className = "name";
      name.textContent = d.slave_id;
      li.appendChild(dot);
      li.appendChild(name);
      li.onclick = () => { activeSlave = d.slave_id; $("#activeSlave").textContent = d.slave_id; renderDevices(devices); };
      deviceList.appendChild(li);
    });
  }

  // ── 播放控制 ──────────────────────────────────────────────
  function requireSlave() {
    if (!activeSlave) { log("請先在左側選擇設備", "warn"); return false; }
    return true;
  }

  function bindControls() {
    $("#btnPrepare").onclick = () => {
      if (!requireSlave()) return;
      sendUI({ action: "stream_prepare", slave_id: activeSlave, file_name: $("#fileName").value, play_mode: parseInt($("#playMode").value, 10) });
    };
    $("#btnPlay").onclick = () => {
      if (!requireSlave()) return;
      const fps = parseInt($("#fps").value, 10) || 40;
      sendUI({ action: "stream_fps", slave_id: activeSlave, fps });
      sendUI({ action: "stream_play", slave_id: activeSlave, start_frame: 0 });
    };
    $("#btnPause").onclick = () => { if (requireSlave()) sendUI({ action: "stream_pause", slave_id: activeSlave, paused: true }); };
    $("#btnStop").onclick = () => { if (requireSlave()) sendUI({ action: "stream_stop", slave_id: activeSlave }); };
    $("#btnSeek").onclick = () => { if (requireSlave()) sendUI({ action: "stream_seek", slave_id: activeSlave, frame: 0 }); };

    // RAM 上傳
    $("#btnRamUpload").onclick = async () => {
      if (!requireSlave()) return;
      const file = $("#ramFile").files[0];
      if (!file) { log("請選擇要上傳的檔案", "warn"); return; }
      const chunk = parseInt($("#ramChunk").value, 10) || 4096;
      const remote = $("#ramPath").value || "/ram/live.bin";
      const buf = await file.arrayBuffer();
      const b64 = b64FromArrayBuffer(buf);
      log(`上傳 ${file.name} (${buf.byteLength} B) → ${remote}`, "info");
      const bar = $("#ramProgress");
      bar.style.width = "0";
      // 分次送出 (避免單一 WS message 太大)
      const SLICE = 512 * 1024;
      for (let i = 0; i < b64.length; i += SLICE) {
        sendUI({ action: "ram_upload", slave_id: activeSlave, remote_path: remote, chunk_size: chunk, data_b64: b64.slice(i, i + SLICE) });
        // 簡易進度 (最終由 server 回 ok 再收尾)
      }
      log("已送出 RAM 上傳指令", "info");
    };

    $("#delaySlider").oninput = () => { $("#delayVal").textContent = $("#delaySlider").value; };
    $("#themeToggle").onclick = () => {
      const cur = document.documentElement.getAttribute("data-theme");
      document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
    };
  }

  function b64FromArrayBuffer(buf) {
    const bytes = new Uint8Array(buf);
    let bin = "";
    for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin);
  }

  // ── MP3 播放 (瀏覽器原生 <audio>) ─────────────────────────
  async function loadMp3() {
    try {
      const r = await fetch("/api/mp3");
      const j = await r.json();
      if (!j.ok) return;
      const sel = $("#mp3Select");
      sel.innerHTML = '<option value="">(選擇 MP3)</option>';
      j.data.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.name;
        opt.textContent = m.name;
        sel.appendChild(opt);
      });
    } catch (e) { log("載入 MP3 清單失敗: " + e, "err"); }
  }

  function bindAudio() {
    const player = $("#player");
    $("#mp3Select").onchange = () => {
      const name = $("#mp3Select").value;
      if (!name) { player.pause(); currentAudio = null; return; }
      currentAudio = name;
      player.src = "/media/" + encodeURIComponent(name);
      player.play().then(() => {
        log("▶ 播放 MP3: " + name + " (延遲 " + $("#delaySlider").value + " ms)", "ok");
        // 播放同步訊號給選中設備
        if (activeSlave) {
          const delay = parseInt($("#delaySlider").value, 10) || 0;
          // delay 補償: 先準備 + 延遲後觸發播放
          setTimeout(() => {
            sendUI({ action: "stream_play", slave_id: activeSlave, start_frame: 0 });
          }, Math.max(0, delay));
        }
      }).catch((e) => log("播放失敗: " + e, "err"));
    };
  }

  // ── init ──────────────────────────────────────────────────
  function init() {
    bindControls();
    bindAudio();
    loadMp3();
    connectUI();
    log("WebMaster 已啟動", "ok");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
