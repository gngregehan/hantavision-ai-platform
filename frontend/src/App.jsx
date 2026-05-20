import { useEffect, useMemo, useState } from 'react';
import { getOverview, getPerformance, listAnalyses, loadSession, login, register, saveSession, uploadAnalysis } from './lib/api';

const initialAuth = { fullName: '', email: 'admin@hantavision.local', password: 'ChangeMe!2026' };

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function App() {
  const [session, setSession] = useState(() => loadSession());
  const [auth, setAuth] = useState(initialAuth);
  const [mode, setMode] = useState('login');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [overview, setOverview] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const isAdmin = session?.user?.role === 'admin';
  const latest = useMemo(() => result || history[0], [result, history]);

  useEffect(() => {
    if (!session?.accessToken) return;
    refreshData(session.accessToken, isAdmin);
  }, [session?.accessToken, isAdmin]);

  async function refreshData(token, includeAll = false) {
    try {
      const analyses = await listAnalyses(token, includeAll);
      setHistory(analyses);
      if (includeAll) {
        setOverview(await getOverview(token));
        setPerformance(await getPerformance(token));
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleAuth(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const payload = mode === 'register'
        ? { full_name: auth.fullName || 'HantaVision User', email: auth.email, password: auth.password }
        : { email: auth.email, password: auth.password };
      const nextSession = mode === 'register' ? await register(payload) : await login(payload);
      saveSession(nextSession);
      setSession(nextSession);
      setMessage('Oturum açıldı.');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!file || !session?.accessToken) return;
    setLoading(true);
    setMessage('');
    try {
      const analysis = await uploadAnalysis(file, session.accessToken);
      setResult(analysis);
      await refreshData(session.accessToken, isAdmin);
      setMessage('Analiz tamamlandı.');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    saveSession(null);
    setSession(null);
    setResult(null);
    setHistory([]);
    setOverview(null);
    setPerformance(null);
  }

  if (!session) {
    return (
      <main className='auth-page'>
        <section className='auth-panel'>
          <p className='eyebrow'>HantaVision AI</p>
          <h1>Klinik görüntü analiz paneli</h1>
          <form onSubmit={handleAuth} className='stack'>
            <div className='segmented'>
              <button type='button' className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Giriş</button>
              <button type='button' className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Kayıt</button>
            </div>
            {mode === 'register' && (
              <label>Ad Soyad<input value={auth.fullName} onChange={(event) => setAuth({ ...auth, fullName: event.target.value })} /></label>
            )}
            <label>E-posta<input type='email' value={auth.email} onChange={(event) => setAuth({ ...auth, email: event.target.value })} /></label>
            <label>Parola<input type='password' value={auth.password} onChange={(event) => setAuth({ ...auth, password: event.target.value })} /></label>
            <button className='primary' disabled={loading}>{loading ? 'Bekleyin' : 'Devam et'}</button>
          </form>
          {message && <p className='message'>{message}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className='shell'>
      <aside className='sidebar'>
        <p className='eyebrow'>HantaVision AI</p>
        <h1>Analiz konsolu</h1>
        <div className='identity'>
          <strong>{session.user.fullName}</strong>
          <span>{session.user.email}</span>
          <small>{session.user.role}</small>
        </div>
        <button className='ghost' onClick={logout}>Çıkış</button>
      </aside>

      <section className='workspace'>
        <form className='upload' onSubmit={handleUpload}>
          <div>
            <p className='eyebrow'>Yeni analiz</p>
            <h2>Görüntü yükle</h2>
          </div>
          <input type='file' accept='image/*' onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <button className='primary' disabled={!file || loading}>{loading ? 'Analiz ediliyor' : 'Analiz et'}</button>
        </form>

        {message && <p className='message'>{message}</p>}

        <section className='grid'>
          <article className='panel result-panel'>
            <p className='eyebrow'>Son sonuç</p>
            {latest ? (
              <>
                <h2>{latest.hantavirusResult}</h2>
                <div className='metrics'>
                  <span>Güven <strong>{formatPercent(latest.confidence)}</strong></span>
                  <span>Kalite <strong>{formatPercent(latest.qualityScore)}</strong></span>
                  <span>Güvenilirlik <strong>{formatPercent(latest.reliabilityScore)}</strong></span>
                  <span>Risk <strong>{latest.riskLevel}</strong></span>
                </div>
                <p>{latest.explanation}</p>
                <p className='notice'>{latest.medicalNotice}</p>
                {latest.warnings?.length > 0 && <ul>{latest.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
              </>
            ) : (
              <p>Henüz analiz yapılmadı.</p>
            )}
          </article>

          <article className='panel'>
            <p className='eyebrow'>Geçmiş</p>
            <div className='history'>
              {history.length === 0 && <p>Kayıt yok.</p>}
              {history.map((item) => (
                <button type='button' key={item.id} onClick={() => setResult(item)}>
                  <strong>{item.fileName}</strong>
                  <span>{item.hantavirusResult}</span>
                  <small>{new Date(item.createdAt).toLocaleString('tr-TR')}</small>
                </button>
              ))}
            </div>
          </article>
        </section>

        {isAdmin && (
          <section className='grid admin-grid'>
            <article className='panel'>
              <p className='eyebrow'>Admin özet</p>
              <div className='metrics'>
                <span>Analiz <strong>{overview?.totalAnalyses ?? 0}</strong></span>
                <span>Yüksek risk <strong>{overview?.highRisk ?? 0}</strong></span>
                <span>Uzman inceleme <strong>{overview?.expertReview ?? 0}</strong></span>
                <span>Kullanıcı <strong>{overview?.users ?? 0}</strong></span>
              </div>
            </article>
            <article className='panel'>
              <p className='eyebrow'>Model performansı</p>
              <div className='metrics'>
                <span>Accuracy <strong>{formatPercent(performance?.metrics?.accuracy)}</strong></span>
                <span>Precision <strong>{formatPercent(performance?.metrics?.precision)}</strong></span>
                <span>Recall <strong>{formatPercent(performance?.metrics?.recall)}</strong></span>
                <span>AUROC <strong>{formatPercent(performance?.metrics?.auroc)}</strong></span>
              </div>
            </article>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;
