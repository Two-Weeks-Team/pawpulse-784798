from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from routes import api_router
from models import Base, get_engine

load_dotenv()

app = FastAPI(title="PawPulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    from models import get_session, User, Pet

    db = get_session()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(id=1, email="demo@pawpulse.ai", hashed_password="demo"))
            db.flush()
            db.add(
                Pet(
                    id=1,
                    name="Buddy",
                    breed="Golden Retriever",
                    age_years=3,
                    weight_kg=30,
                    owner_id=1,
                )
            )
            db.add(
                Pet(
                    id=2,
                    name="Luna",
                    breed="Persian Cat",
                    age_years=2,
                    weight_kg=4,
                    owner_id=1,
                )
            )
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.get("/api/pets")
def list_pets():
    from models import get_session, Pet

    db = get_session()
    try:
        pets = db.query(Pet).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "breed": p.breed,
                "age_years": p.age_years,
                "weight_kg": p.weight_kg,
            }
            for p in pets
        ]
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def landing():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PawPulse - AI Pet Health Tracker</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: { pink: '#ec4899', purple: '#8b5cf6' },
        surface: { DEFAULT: '#171717', alt: '#0a0a0a', border: '#262626', hover: '#1f1f1f' }
      }
    }
  }
}
</script>
<style>
@keyframes spin { to { transform: rotate(360deg) } }
.spinner { width: 20px; height: 20px; border: 2px solid #525252; border-top-color: #ec4899; border-radius: 50%; animation: spin .6s linear infinite; display: inline-block; }
</style>
</head>
<body class="bg-[#0a0a0a] text-[#e5e5e5] min-h-screen antialiased">

<div class="max-w-3xl mx-auto px-4 py-12 sm:py-16">

  <!-- Hero -->
  <header class="text-center mb-12">
    <h1 class="text-5xl sm:text-6xl font-extrabold bg-gradient-to-r from-[#ec4899] to-[#8b5cf6] bg-clip-text text-transparent mb-3">PawPulse</h1>
    <p class="text-lg text-neutral-400 mb-4">Track, diagnose, and care for your pet's health in one place.</p>
    <div class="flex justify-center gap-2 flex-wrap">
      <span class="px-3 py-1 rounded-full text-xs font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/25">AI-Powered</span>
      <span class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/25">DigitalOcean</span>
      <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/25">Live</span>
    </div>
  </header>

  <!-- AI Symptom Check -->
  <section class="bg-[#171717] border border-[#262626] rounded-xl p-6 mb-4">
    <h2 class="text-lg font-bold text-neutral-100 mb-1">AI Symptom Check</h2>
    <p class="text-sm text-neutral-500 mb-4">Describe your pet's symptoms and get AI-powered analysis.</p>
    <form id="symptomForm" onsubmit="return handleSymptomCheck(event)" class="space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-neutral-300 mb-1" for="sc-pet-id">Select Your Pet</label>
          <select id="sc-pet-id" required class="w-full bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-[#ec4899] focus:ring-1 focus:ring-[#ec4899]/50 transition">
            <option value="1">Buddy (Golden Retriever, 3y)</option>
            <option value="2">Luna (Persian Cat, 2y)</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-300 mb-1" for="sc-photo">Photo URL <span class="text-neutral-600">(optional)</span></label>
          <input id="sc-photo" type="text" placeholder="https://..." class="w-full bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-[#ec4899] focus:ring-1 focus:ring-[#ec4899]/50 transition" />
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-neutral-300 mb-1" for="sc-symptoms">Symptoms</label>
        <textarea id="sc-symptoms" rows="3" required placeholder="e.g. My dog has been vomiting for 2 days and seems lethargic..." class="w-full bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-[#ec4899] focus:ring-1 focus:ring-[#ec4899]/50 transition resize-y"></textarea>
      </div>
      <button type="submit" id="sc-btn" class="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-[#ec4899] to-[#8b5cf6] text-white font-semibold rounded-lg text-sm hover:opacity-90 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
        <span id="sc-btn-text">Analyze Symptoms</span>
        <span id="sc-spinner" class="spinner hidden"></span>
      </button>
    </form>
    <div id="sc-error" class="mt-4 text-sm text-red-400 hidden"></div>
    <div id="sc-result" class="mt-4 hidden"></div>
  </section>

  <!-- AI Health Report -->
  <section class="bg-[#171717] border border-[#262626] rounded-xl p-6 mb-4">
    <h2 class="text-lg font-bold text-neutral-100 mb-1">AI Health Report</h2>
    <p class="text-sm text-neutral-500 mb-4">Generate a comprehensive health report for a date range.</p>
    <form id="reportForm" onsubmit="return handleReport(event)" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-neutral-300 mb-1" for="rp-pet-id">Select Your Pet</label>
        <select id="rp-pet-id" required class="w-full sm:w-48 bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-[#8b5cf6] focus:ring-1 focus:ring-[#8b5cf6]/50 transition">
          <option value="1">Buddy (Golden Retriever, 3y)</option>
          <option value="2">Luna (Persian Cat, 2y)</option>
        </select>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-neutral-300 mb-1" for="rp-start">Start Date</label>
          <input id="rp-start" type="datetime-local" required class="w-full bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-[#8b5cf6] focus:ring-1 focus:ring-[#8b5cf6]/50 transition [color-scheme:dark]" />
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-300 mb-1" for="rp-end">End Date</label>
          <input id="rp-end" type="datetime-local" required class="w-full bg-[#0a0a0a] border border-[#262626] rounded-lg px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-[#8b5cf6] focus:ring-1 focus:ring-[#8b5cf6]/50 transition [color-scheme:dark]" />
        </div>
      </div>
      <button type="submit" id="rp-btn" class="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-[#8b5cf6] to-[#6d28d9] text-white font-semibold rounded-lg text-sm hover:opacity-90 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
        <span id="rp-btn-text">Generate Report</span>
        <span id="rp-spinner" class="spinner hidden"></span>
      </button>
    </form>
    <div id="rp-error" class="mt-4 text-sm text-red-400 hidden"></div>
    <div id="rp-result" class="mt-4 hidden"></div>
  </section>

  <!-- How It Works -->
  <section class="bg-[#171717] border border-[#262626] rounded-xl p-6 mb-4">
    <h2 class="text-lg font-bold text-neutral-100 mb-4">How It Works</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="flex gap-3">
        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[#ec4899]/15 text-[#ec4899] flex items-center justify-center text-sm font-bold">1</div>
        <div><p class="text-sm font-medium text-neutral-200">Describe Symptoms</p><p class="text-xs text-neutral-500 mt-0.5">Tell us what your pet is experiencing in plain language.</p></div>
      </div>
      <div class="flex gap-3">
        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[#a855f7]/15 text-[#a855f7] flex items-center justify-center text-sm font-bold">2</div>
        <div><p class="text-sm font-medium text-neutral-200">AI Analysis</p><p class="text-xs text-neutral-500 mt-0.5">DigitalOcean Gradient AI analyzes symptoms against known conditions.</p></div>
      </div>
      <div class="flex gap-3">
        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[#8b5cf6]/15 text-[#8b5cf6] flex items-center justify-center text-sm font-bold">3</div>
        <div><p class="text-sm font-medium text-neutral-200">Confidence Scores</p><p class="text-xs text-neutral-500 mt-0.5">Get potential conditions ranked by confidence and urgency level.</p></div>
      </div>
      <div class="flex gap-3">
        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[#6d28d9]/15 text-[#6d28d9] flex items-center justify-center text-sm font-bold">4</div>
        <div><p class="text-sm font-medium text-neutral-200">Share with Vet</p><p class="text-xs text-neutral-500 mt-0.5">Use the generated report to have an informed conversation with your vet.</p></div>
      </div>
    </div>
  </section>

  <!-- Disclaimer -->
  <p class="text-center text-xs text-neutral-600 mb-6 px-4">This is an AI-powered tool and should not replace professional veterinary advice.</p>

  <!-- Footer -->
  <footer class="text-center text-xs text-neutral-600">
    Generated by <a href="https://github.com/Two-Weeks-Team/vibeDeploy" class="text-[#ec4899] hover:underline">vibeDeploy</a>
    &bull; Powered by <a href="https://www.digitalocean.com/products/gradient-ai" class="text-[#ec4899] hover:underline">DigitalOcean Gradient AI</a>
    &bull; <a href="/docs" class="text-neutral-600 hover:text-neutral-500">API Docs</a>
  </footer>

</div>

<script>
function urgencyColor(u) {
  const l = (u || '').toLowerCase();
  if (l === 'critical') return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', label: 'font-bold' };
  if (l === 'high') return { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/25', label: '' };
  if (l === 'medium') return { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/25', label: '' };
  return { bg: 'bg-green-500/15', text: 'text-green-400', border: 'border-green-500/25', label: '' };
}

function barColor(confidence) {
  if (confidence >= 0.7) return 'from-red-500 to-red-400';
  if (confidence >= 0.4) return 'from-amber-500 to-amber-400';
  return 'from-green-500 to-green-400';
}

function setLoading(prefix, loading) {
  const btn = document.getElementById(prefix + '-btn');
  const text = document.getElementById(prefix + '-btn-text');
  const spinner = document.getElementById(prefix + '-spinner');
  btn.disabled = loading;
  text.textContent = loading ? (prefix === 'sc' ? 'Analyzing...' : 'Generating...') : (prefix === 'sc' ? 'Analyze Symptoms' : 'Generate Report');
  spinner.classList.toggle('hidden', !loading);
}

function showError(prefix, msg) {
  const el = document.getElementById(prefix + '-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideError(prefix) {
  document.getElementById(prefix + '-error').classList.add('hidden');
}

function hideResult(prefix) {
  const el = document.getElementById(prefix + '-result');
  el.classList.add('hidden');
  el.innerHTML = '';
}

async function handleSymptomCheck(e) {
  e.preventDefault();
  hideError('sc'); hideResult('sc'); setLoading('sc', true);
  const petId = parseInt(document.getElementById('sc-pet-id').value);
  const symptoms = document.getElementById('sc-symptoms').value.trim();
  const photoRaw = document.getElementById('sc-photo').value.trim();
  const photo = photoRaw.length > 0 ? photoRaw : null;
  try {
    const res = await fetch('/api/ai/symptom_check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pet_id: petId, symptom_text: symptoms, photo_url: photo })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || err.message || `Error ${res.status}`);
    }
    const data = await res.json();
    const container = document.getElementById('sc-result');
    const conditions = data.conditions || [];
    if (conditions.length === 0) {
      container.innerHTML = '<p class="text-sm text-neutral-400">No conditions identified. Try providing more detail about the symptoms.</p>';
    } else {
      container.innerHTML = '<h3 class="text-sm font-semibold text-neutral-300 mb-3">Potential Conditions</h3>' +
        conditions.map(c => {
          const pct = Math.round((c.confidence || 0) * 100);
          const uc = urgencyColor(c.urgency);
          const bc = barColor(c.confidence || 0);
          return '<div class="bg-[#0a0a0a] border border-[#262626] rounded-lg p-4 mb-2">' +
            '<div class="flex items-center justify-between mb-2">' +
              '<span class="text-sm font-medium text-neutral-200">' + escHtml(c.name || 'Unknown') + '</span>' +
              '<span class="px-2 py-0.5 rounded-full text-xs font-semibold border ' + uc.bg + ' ' + uc.text + ' ' + uc.border + ' ' + uc.label + '">' + escHtml((c.urgency || 'low').toUpperCase()) + '</span>' +
            '</div>' +
            '<div class="flex items-center gap-3">' +
              '<div class="flex-1 h-2 bg-[#262626] rounded-full overflow-hidden">' +
                '<div class="h-full bg-gradient-to-r ' + bc + ' rounded-full transition-all" style="width:' + pct + '%"></div>' +
              '</div>' +
              '<span class="text-xs font-mono text-neutral-400 w-10 text-right">' + pct + '%</span>' +
            '</div>' +
          '</div>';
        }).join('');
    }
    container.classList.remove('hidden');
  } catch (err) {
    showError('sc', err.message);
  } finally {
    setLoading('sc', false);
  }
  return false;
}

async function handleReport(e) {
  e.preventDefault();
  hideError('rp'); hideResult('rp'); setLoading('rp', true);
  const petId = parseInt(document.getElementById('rp-pet-id').value);
  const start = document.getElementById('rp-start').value;
  const end = document.getElementById('rp-end').value;
  try {
    const res = await fetch('/api/ai/generate_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pet_id: petId, start_date: start, end_date: end })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || err.message || `Error ${res.status}`);
    }
    const data = await res.json();
    const container = document.getElementById('rp-result');
    const text = data.report_text || 'No report generated.';
    container.innerHTML = '<div class="bg-[#0a0a0a] border border-[#262626] rounded-lg p-5">' +
      '<h3 class="text-sm font-semibold text-neutral-300 mb-3">Health Report</h3>' +
      '<div class="text-sm text-neutral-300 leading-relaxed whitespace-pre-wrap">' + escHtml(text) + '</div>' +
    '</div>';
    container.classList.remove('hidden');
  } catch (err) {
    showError('rp', err.message);
  } finally {
    setLoading('rp', false);
  }
  return false;
}

function escHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}

// Pre-fill dates: start = 30 days ago, end = now
(function() {
  const now = new Date();
  const ago = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  const fmt = d => d.toISOString().slice(0, 16);
  document.getElementById('rp-start').value = fmt(ago);
  document.getElementById('rp-end').value = fmt(now);
})();
</script>

</body>
</html>"""


app.include_router(api_router, prefix="/api")
