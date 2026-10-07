const entryFlow = document.querySelector('#entryFlow');
const entryFirst = document.querySelector('#entryFirst');
const entryPlayful = document.querySelector('#entryPlayful');
entryFlow.querySelectorAll('.entry-no').forEach(button => button.addEventListener('click', () => {
  entryFirst.hidden = true;
  entryPlayful.hidden = false;
  entryPlayful.querySelector('.entry-yes').focus();
}));
entryFlow.querySelectorAll('.entry-yes').forEach(button => button.addEventListener('click', () => {
  entryFlow.remove();
  const heading = document.querySelector('#hero-title');
  heading.setAttribute('tabindex', '-1');
  heading.focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
}));

const lightbox = document.querySelector('#lightbox');
document.querySelectorAll('.photo-card').forEach(card => card.addEventListener('click', () => {
  lightbox.querySelector('img').src = new URL(card.dataset.full, document.baseURI).href;
  lightbox.querySelector('img').alt = card.querySelector('img').alt;
  lightbox.showModal();
}));
lightbox.querySelector('.lightbox-close').addEventListener('click', () => lightbox.close());
lightbox.addEventListener('click', event => { if (event.target === lightbox) lightbox.close(); });

const letter = document.querySelector('.editable-letter');
const status = document.querySelector('.save-status');
const savedLetter = localStorage.getItem('paridhi-birthday-letter-v2');
if (savedLetter) letter.innerText = savedLetter;
let saveTimer;
letter.addEventListener('input', () => {
  status.textContent = 'Saving…';
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    localStorage.setItem('paridhi-birthday-letter-v2', letter.innerText);
    status.textContent = 'Saved on this device ✓';
  }, 350);
});

const giftButton = document.querySelector('#giftButton');
const reveal = document.querySelector('#giftReveal');
const balloons = document.querySelector('#balloonLayer');
const replay = document.querySelector('#replayButton');
let opened = false;
function openGift() {
  if (opened) return;
  opened = true;
  giftButton.classList.add('open');
  giftButton.setAttribute('aria-expanded', 'true');
  reveal.classList.add('show');
  reveal.setAttribute('aria-hidden', 'false');
  replay.hidden = false;
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    for (let i = 0; i < 24; i++) {
      const balloon = document.createElement('span');
      balloon.className = 'balloon';
      balloon.style.left = `${Math.random() * 100}%`;
      balloon.style.setProperty('--duration', `${5 + Math.random() * 3}s`);
      balloon.style.setProperty('--drift', `${Math.round(Math.random() * 140 - 70)}px`);
      balloon.style.animationDelay = `${Math.random() * 1.3}s`;
      balloon.style.transform = `scale(${0.72 + Math.random() * 0.72})`;
      balloons.append(balloon);
      setTimeout(() => balloon.remove(), 9000);
    }
  }
}
giftButton.addEventListener('click', openGift);
replay.addEventListener('click', () => {
  opened = false;
  giftButton.classList.remove('open');
  giftButton.setAttribute('aria-expanded', 'false');
  reveal.classList.remove('show');
  reveal.setAttribute('aria-hidden', 'true');
  replay.hidden = true;
  balloons.replaceChildren();
  setTimeout(openGift, 250);
});

// Keep video playback to one clip at a time.
document.querySelectorAll('video').forEach(video => video.addEventListener('play', () => {
  document.querySelectorAll('video').forEach(other => { if (other !== video) other.pause(); });
}));

const backgroundMusic = document.querySelector('#backgroundMusic');
const musicButton = document.querySelector('#musicButton');
const musicMark = musicButton.querySelector('.music-toggle-mark');
const musicStatus = document.querySelector('#musicStatus');
backgroundMusic.loop = true;
let musicContext = null;
let musicGain = null;
const musicNormalGain = 0.46;
const musicDuckedGain = 0.11;

function isAnyVideoPlaying() {
  return [...document.querySelectorAll('video')].some(video => !video.paused && !video.ended);
}

function setMusicLevel(level) {
  if (musicGain && musicContext && musicContext.state !== 'closed') {
    const gain = musicGain.gain;
    const now = musicContext.currentTime;
    gain.cancelScheduledValues(now);
    gain.setValueAtTime(gain.value, now);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) gain.setValueAtTime(level, now);
    else gain.linearRampToValueAtTime(level, now + 0.45);
  } else {
    backgroundMusic.volume = level;
  }
}

function syncMusicToVideoPlayback() {
  setMusicLevel(isAnyVideoPlaying() ? musicDuckedGain : musicNormalGain);
}

function showMusicState() {
  const isPlaying = !backgroundMusic.paused;
  musicButton.dataset.playing = String(isPlaying);
  musicButton.setAttribute('aria-pressed', String(isPlaying));
  musicButton.setAttribute('aria-label', isPlaying ? 'Pause background music' : 'Play background music');
  musicMark.textContent = isPlaying ? 'Ⅱ' : '▶';
  musicStatus.textContent = isPlaying ? 'Background music playing' : 'Background music paused';
}

async function startBackgroundMusic() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass && !musicContext) {
      musicContext = new AudioContextClass();
      const source = musicContext.createMediaElementSource(backgroundMusic);
      musicGain = musicContext.createGain();
      source.connect(musicGain);
      musicGain.connect(musicContext.destination);
      backgroundMusic.volume = 1;
    }
    if (musicContext?.state === 'suspended') await musicContext.resume();
    setMusicLevel(isAnyVideoPlaying() ? musicDuckedGain : musicNormalGain);
    await backgroundMusic.play();
  } catch (error) {
    backgroundMusic.pause();
    showMusicState();
    musicStatus.textContent = 'Background music could not be started';
    console.warn('Background music playback failed:', error);
  }
}

musicButton.addEventListener('click', () => {
  if (backgroundMusic.paused) startBackgroundMusic();
  else backgroundMusic.pause();
});
backgroundMusic.addEventListener('play', showMusicState);
backgroundMusic.addEventListener('pause', showMusicState);
backgroundMusic.addEventListener('error', () => { musicStatus.textContent = 'Background music could not be loaded'; });
document.querySelectorAll('video').forEach(video => {
  video.addEventListener('play', syncMusicToVideoPlayback);
  video.addEventListener('pause', syncMusicToVideoPlayback);
  video.addEventListener('ended', syncMusicToVideoPlayback);
});
window.addEventListener('pagehide', () => backgroundMusic.pause());
