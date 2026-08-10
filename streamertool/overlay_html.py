from __future__ import annotations

CALL_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/call/default.css"></head><body>
<div id="overlay-container">
  <section id="call-area" class="overlay-area">
    <div id="call-message" class="overlay-message" hidden></div>
  </section>
</div>
<script>
let lastCallId=0, callTimer;
const sound=new Audio();
sound.preload='auto';
function showBox(box){
  box.hidden=false;
  box.classList.add('show');
}
function hideBox(box){
  box.classList.remove('show');
  box.hidden=true;
}
function renderCharacters(box,text){
  box.replaceChildren();
  Array.from(text).forEach((character,index)=>{
    const span=document.createElement('span');
    span.className='char';
    span.style.setProperty('--char-index',index);
    span.textContent=character;
    box.appendChild(span);
  });
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    const call=data.call || {};
    if(call.id>lastCallId){
      lastCallId=call.id;
      const box=document.getElementById('call-message');
      clearTimeout(callTimer);
      if(call.visible && call.text){
        renderCharacters(box,call.text);
        showBox(box);
      }else{
        hideBox(box);
      }
      if(call.sound_url){
        sound.pause();
        sound.src=call.sound_url+'?event='+call.id;
        sound.currentTime=0;
        sound.play().catch(()=>{});
      }
      if(call.visible && call.duration_ms>0){
        callTimer=setTimeout(()=>hideBox(box),call.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


QUEUE_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/queue/default.css"></head><body>
<div id="overlay-container">
  <section id="queue-area" class="overlay-area">
    <div id="queue-message" class="overlay-message" hidden></div>
  </section>
</div>
<script>
let lastQueueId=0, queueTimer;
function showBox(box){
  box.hidden=false;
  box.classList.add('show');
}
function hideBox(box){
  box.classList.remove('show');
  box.hidden=true;
}
function renderQueue(box,items,hasMore){
  box.replaceChildren();
  const list=document.createElement('ol');
  list.className='queue-list';
  items.forEach(name=>{
    const item=document.createElement('li');
    item.textContent=name;
    list.appendChild(item);
  });
  if(hasMore){
    const item=document.createElement('li');
    item.className='queue-more';
    item.textContent='...';
    list.appendChild(item);
  }
  box.appendChild(list);
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    const queue=data.queue || {};
    if(queue.id>lastQueueId){
      lastQueueId=queue.id;
      const box=document.getElementById('queue-message');
      clearTimeout(queueTimer);
      if(queue.visible){
        renderQueue(box,queue.items || [], !!queue.has_more);
        showBox(box);
      }else{
        hideBox(box);
      }
      if(queue.visible && queue.duration_ms>0){
        queueTimer=setTimeout(()=>hideBox(box),queue.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


CALENDAR_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link id="calendarStyle" rel="stylesheet" href="/css/calendar/default.css"></head><body>
<div class="calendar-container" id="calendarBox">
  <div class="banner-alert" id="alertText">Twitch Check-in Calendar</div>
  <div class="calendar-header" id="calendarTitle"></div>
  <div class="days-grid" id="daysGrid"></div>
</div>
<script>
let lastCalendarId=0, lastCalendarStyleVersion=0, calendarTimer, calendarRenderToken=0;
const dayCells={};
const avatarCache=new Map();
const calendarSound=new Audio();
calendarSound.preload='auto';
const weekdayLabels={
  zh:['\u65e5','\u4e00','\u4e8c','\u4e09','\u56db','\u4e94','\u516d'],
  en:['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
  ja:['\u65e5','\u6708','\u706b','\u6c34','\u6728','\u91d1','\u571f']
};
const box=document.getElementById('calendarBox');
const grid=document.getElementById('daysGrid');
const alertText=document.getElementById('alertText');
function fallbackAvatar(name){
  const initial=Array.from(String(name || '?').trim())[0] || '?';
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="18" fill="#9146ff"/><text x="60" y="75" text-anchor="middle" font-family="Arial,sans-serif" font-size="54" font-weight="700" fill="#fff">${initial.replace(/[&<>]/g,'')}</text></svg>`;
  return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
}
function avatarUrlFor(calendar){
  return String(calendar.avatar_url || '').trim();
}
function preloadImage(url){
  if(!url) return Promise.resolve('');
  if(avatarCache.has(url)) return Promise.resolve(avatarCache.get(url));
  return new Promise(resolve=>{
    const image=new Image();
    let settled=false;
    const finish=(src)=>{
      if(settled) return;
      settled=true;
      clearTimeout(timer);
      if(src) avatarCache.set(url,src);
      resolve(src);
    };
    const timer=setTimeout(()=>finish(''),2000);
    image.onload=()=>finish(url);
    image.onerror=()=>finish('');
    image.src=url;
  });
}
async function preloadCalendarAvatar(calendar){
  const url=avatarUrlFor(calendar);
  if(!url) return '';
  const loadedUrl=await preloadImage(url);
  return loadedUrl || fallbackAvatar(calendar.display_name);
}
function showBox(){
  box.classList.add('show');
}
function hideBox(){
  box.classList.remove('show');
}
function rebuildCalendar(year,month,today,weekdayLanguage){
  grid.replaceChildren();
  Object.keys(dayCells).forEach(key=>delete dayCells[key]);
  const weekdays=weekdayLabels[weekdayLanguage] || weekdayLabels.zh;
  weekdays.forEach(label=>{
    const weekday=document.createElement('div');
    weekday.className='day-name';
    weekday.textContent=label;
    grid.appendChild(weekday);
  });
  document.getElementById('calendarTitle').textContent=`${year} / ${String(month).padStart(2,'0')}`;
  const first=new Date(year,month-1,1).getDay();
  const total=new Date(year,month,0).getDate();
  for(let i=0;i<first;i++){
    const empty=document.createElement('div');
    empty.className='empty-day';
    grid.appendChild(empty);
  }
  for(let day=1;day<=total;day++){
    const cell=document.createElement('div');
    cell.className='day';
    const number=document.createElement('div');
    number.className='day-number';
    number.textContent=day;
    cell.appendChild(number);
    if(day===today){
      cell.classList.add('today-day');
    }
    grid.appendChild(cell);
    dayCells[day]=cell;
  }
}
function clearAllAvatars(){
  Object.values(dayCells).forEach(cell=>{
    cell.classList.remove('first-stamp-day');
    cell.querySelectorAll('img.user-avatar').forEach(img=>img.remove());
  });
}
function renderUserDates(calendar,avatarSrc){
  clearAllAvatars();
  const animateDate=calendar.signed_date || '';
  (calendar.dates || []).forEach(item=>{
    const parts=String(item.date || '').split('-');
    const day=Number(parts[2]);
    const cell=dayCells[day];
    if(!cell) return;
    if(item.isFirst){
      cell.classList.add('first-stamp-day');
    }
    if(avatarSrc){
      const img=document.createElement('img');
      img.className='user-avatar';
      img.src=avatarSrc;
      img.alt='';
      cell.appendChild(img);
      if(animateDate && item.date===animateDate){
        requestAnimationFrame(()=>img.classList.add('stamp-animation'));
      }
    }
  });
}
function renderCalendar(calendar,avatarSrc){
  rebuildCalendar(calendar.year,calendar.month,calendar.today || 0, calendar.weekday_language || 'zh');
  alertText.textContent=calendar.message || 'Twitch Check-in Calendar';
  renderUserDates(calendar,avatarSrc);
}
function updateCalendarStyle(version){
  version=Number(version || 0);
  if(!version || version===lastCalendarStyleVersion) return;
  lastCalendarStyleVersion=version;
  const link=document.getElementById('calendarStyle');
  if(link){
    link.href='/css/calendar/default.css?style='+version;
  }
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    updateCalendarStyle(data.calendar_style_version);
    const calendar=data.calendar || {};
    if(calendar.id>lastCalendarId){
      lastCalendarId=calendar.id;
      clearTimeout(calendarTimer);
      const renderToken=++calendarRenderToken;
      if(calendar.visible){
        const avatarSrc=await preloadCalendarAvatar(calendar);
        if(renderToken!==calendarRenderToken) return;
        renderCalendar(calendar,avatarSrc);
        showBox();
        if(calendar.sound_url){
          calendarSound.pause();
          calendarSound.currentTime=0;
          calendarSound.src=calendar.sound_url+'?event='+calendar.id;
          calendarSound.play().catch(()=>{});
        }
      }else{
        hideBox();
      }
      if(calendar.visible && calendar.duration_ms>0){
        calendarTimer=setTimeout(hideBox,calendar.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


