import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Chrome,
  Clock,
  Cpu,
  Database,
  Download,
  Eye,
  FileSearch,
  FileText,
  FlaskConical,
  Gauge,
  History,
  Layers3,
  LineChart,
  LockKeyhole,
  LogIn,
  MessageCircle,
  Microscope,
  Play,
  ScanLine,
  ShieldCheck,
  Stethoscope,
  UploadCloud,
  UserPlus,
  X,
  Zap,
} from 'lucide-react';
import {
  downloadReport,
  getModelStatus,
  getOverview,
  getPerformance,
  listAnalyses,
  loadSession,
  login,
  register,
  saveSession,
  uploadAnalysis,
} from './lib/api';

const initialAuth = { fullName: '', email: 'admin@hantavision.local', password: 'ChangeMe!2026' };

const analysisSteps = [
  'Görüntü alındı',
  'Görüntü ön işleniyor',
  'Gürültü azaltılıyor',
  'Yapay zeka modeli çalıştırılıyor',
  'Risk skoru hesaplanıyor',
  'Rapor oluşturuluyor',
];

const techStack = ['Python', 'OpenCV', 'TensorFlow / PyTorch', 'CNN', 'ResNet', 'EfficientNet', 'Grad-CAM', 'React', 'FastAPI'];

const riskLevels = [
  ['Düşük Risk', 'Belirgin bulgu yok'],
  ['Orta Risk', 'Şüpheli örüntüler var'],
  ['Yüksek Risk', 'Güçlü anomali tespiti var'],
  ['Kritik', 'Acil uzman incelemesi önerilir'],
];

const faqItems = [
  ['Hantavirüs nedir?', 'Kemirgenlerle ilişkili olabilen, solunum ve sistemik bulgularla takip edilen ciddi bir viral enfeksiyon grubudur.'],
  ['Sistem kesin tanı koyar mı?', 'Hayır. HantaVision AI yalnızca ön değerlendirme ve eğitim amaçlı karar destek çıktısı üretir.'],
  ['Hangi görüntüler desteklenir?', 'Akciğer röntgeni, kemirgen fotoğrafı, mikroskobik görüntü, laboratuvar görüntüsü ve DICOM dosyaları desteklenir.'],
  ['Sonuçlar nasıl yorumlanır?', 'Risk düzeyi, güven skoru, görüntü kalitesi ve açıklanabilir AI alanı birlikte değerlendirilmelidir.'],
  ['Veriler saklanıyor mu?', 'Giriş yapan kullanıcıların analiz geçmişi güvenli veri deposunda saklanır ve kullanıcı panelinden izlenebilir.'],
];

const modeOptions = ['Clinical Mode', 'Research Mode', 'Educational Mode'];

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function formatDate(value) {
  if (!value) return 'Yeni analiz';
  return new Date(value).toLocaleString('tr-TR', { dateStyle: 'medium', timeStyle: 'short' });
}

function safeFileName(value) {
  return (value || 'hantavision-report').replace(/[^a-z0-9._-]+/gi, '-').replace(/^-+|-+$/g, '') || 'hantavision-report';
}

function normalizeImageType(value = '') {
  const text = value.toLocaleLowerCase('tr-TR');
  if (text.includes('akciğer') || text.includes('x-ray') || text.includes('röntgen') || text.includes('rontgen')) return 'Akciğer Röntgeni';
  if (text.includes('kemirgen') || text.includes('fare') || text.includes('rodent')) return 'Kemirgen Fotoğrafı';
  if (text.includes('mikroskop') || text.includes('doku')) return 'Mikroskop Görüntüsü';
  if (text.includes('laboratuvar') || text.includes('lab')) return 'Laboratuvar Görüntüsü';
  if (text.includes('belirsiz') || text.includes('uygun olmayan')) return 'Bilinmeyen Görüntü';
  return value || 'Bilinmeyen Görüntü';
}

function inferImageType(file) {
  if (!file) return { label: 'Bilinmeyen Görüntü', model: 'Expert Review Router', route: 'unknown' };
  const name = file.name.toLocaleLowerCase('tr-TR');
  if (name.endsWith('.dcm') || name.endsWith('.dicom')) return { label: 'Akciğer Röntgeni', model: 'Medical CNN Model', route: 'xray' };
  if (/(xray|x-ray|röntgen|rontgen|chest|lung|akci)/.test(name)) return { label: 'Akciğer Röntgeni', model: 'Medical CNN Model', route: 'xray' };
  if (/(rodent|mouse|rat|fare|kemirgen)/.test(name)) return { label: 'Kemirgen Fotoğrafı', model: 'Rodent Detection Model', route: 'rodent' };
  if (/(micro|mikroskop|cell|tissue|doku)/.test(name)) return { label: 'Mikroskop Görüntüsü', model: 'Microscopy Model', route: 'micro' };
  if (/(lab|assay|culture|serum|plate)/.test(name)) return { label: 'Laboratuvar Görüntüsü', model: 'Laboratory Vision Model', route: 'lab' };
  return { label: 'Bilinmeyen Görüntü', model: 'Expert Review Router', route: 'unknown' };
}

function modelForType(value) {
  const label = normalizeImageType(value);
  if (label === 'Akciğer Röntgeni') return 'Medical CNN Model';
  if (label === 'Kemirgen Fotoğrafı') return 'Rodent Detection Model';
  if (label === 'Mikroskop Görüntüsü') return 'Microscopy Model';
  if (label === 'Laboratuvar Görüntüsü') return 'Laboratory Vision Model';
  return 'Expert Review Router';
}

function architectureForType(value) {
  const label = normalizeImageType(value);
  if (label === 'Akciğer Röntgeni') return 'EfficientNet / ResNet / CNN';
  if (label === 'Kemirgen Fotoğrafı') return 'ResNet-50 Detector';
  if (label === 'Mikroskop Görüntüsü') return 'Vision Transformer + CNN';
  if (label === 'Laboratuvar Görüntüsü') return 'CNN Ensemble';
  return 'Expert Review Ensemble';
}

function isValidatedAnalysis(item) {
  return Boolean(item?.metrics?.runtime?.architecture || item?.modelStack?.some((stage) => stage.runtime === 'validated'));
}

function riskLabel(item) {
  if (!item) return 'Beklemede';
  if (!isValidatedAnalysis(item)) return 'Legacy demo';
  const risk = String(item.riskLevel || '').toLocaleLowerCase('tr-TR');
  if (risk.includes('yüksek') && Number(item.confidence) > 0.84) return 'Kritik';
  if (risk.includes('yüksek')) return 'Yüksek';
  if (risk.includes('orta')) return 'Orta';
  if (risk.includes('düşük') || risk.includes('dusuk')) return 'Düşük';
  return item.riskLevel || 'Belirsiz';
}

function riskClass(item) {
  if (item && !isValidatedAnalysis(item)) return 'unknown';
  const label = riskLabel(item).toLocaleLowerCase('tr-TR');
  if (label.includes('kritik')) return 'critical';
  if (label.includes('yüksek')) return 'high';
  if (label.includes('orta')) return 'medium';
  if (label.includes('düşük')) return 'low';
  return 'unknown';
}

function syntheticRegions(route) {
  if (route === 'xray') {
    return [
      { x: 22, y: 24, w: 24, h: 50, label: 'Sol pulmoner alan', score: 0.77 },
      { x: 55, y: 24, w: 24, h: 50, label: 'Sağ pulmoner alan', score: 0.74 },
    ];
  }
  if (route === 'rodent') return [{ x: 22, y: 18, w: 56, h: 62, label: 'Taşıyıcı canlı adayı', score: 0.72 }];
  if (route === 'micro' || route === 'lab') {
    return [
      { x: 16, y: 18, w: 25, h: 25, label: 'Hücresel yoğunluk', score: 0.68 },
      { x: 54, y: 34, w: 28, h: 25, label: 'Tekstür değişimi', score: 0.64 },
    ];
  }
  return [{ x: 34, y: 28, w: 32, h: 34, label: 'Uzman inceleme alanı', score: 0.52 }];
}

function App() {
  const [session, setSession] = useState(() => loadSession());
  const [auth, setAuth] = useState(initialAuth);
  const [authMode, setAuthMode] = useState('login');
  const [analysisMode, setAnalysisMode] = useState('Clinical Mode');
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [overview, setOverview] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [booting, setBooting] = useState(true);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantQuestion, setAssistantQuestion] = useState('Bu sonuç ne anlama geliyor?');
  const [assistantAnswer, setAssistantAnswer] = useState('Sonuç seçildiğinde risk düzeyi, güven skoru ve model açıklamasını burada sadeleştiririm.');
  const fileInputRef = useRef(null);

  const isAdmin = session?.user?.role === 'admin';
  const latest = useMemo(() => result || history[0], [result, history]);
  const inferred = useMemo(() => inferImageType(file), [file]);
  const displayedImageType = normalizeImageType(latest?.imageType || inferred.label);
  const installedArchitecture = modelStatus?.runtime?.manifest?.architecture;
  const selectedModel = installedArchitecture ? `Validated ${installedArchitecture}` : modelForType(displayedImageType);
  const modelArchitecture = installedArchitecture || architectureForType(displayedImageType);
  const totalAnalyses = overview?.totalAnalyses ?? history.length;
  const avgConfidence = history.length
    ? history.reduce((sum, item) => sum + (Number(item.confidence) || 0), 0) / history.length
    : Number(latest?.confidence) || 0;

  useEffect(() => {
    const timer = window.setTimeout(() => setBooting(false), 2200);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!file || !file.type.startsWith('image/')) {
      setPreviewUrl('');
      return undefined;
    }
    const nextPreview = URL.createObjectURL(file);
    setPreviewUrl(nextPreview);
    return () => URL.revokeObjectURL(nextPreview);
  }, [file]);

  useEffect(() => {
    if (!session?.accessToken) return;
    refreshData(session.accessToken, isAdmin);
  }, [session?.accessToken, isAdmin]);

  useEffect(() => {
    getModelStatus().then(setModelStatus).catch(() => setModelStatus(null));
  }, []);

  useEffect(() => {
    if (!loading) return undefined;
    setActiveStep(0);
    setProgress(8);
    const timer = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, analysisSteps.length - 1));
      setProgress((value) => Math.min(value + 14, 94));
    }, 560);
    return () => window.clearInterval(timer);
  }, [loading]);

  async function refreshData(token, includeAll = false) {
    try {
      const analyses = await listAnalyses(token, includeAll);
      setHistory(analyses);
      if (includeAll) {
        setOverview(await getOverview(token));
        setPerformance(await getPerformance(token));
      }
      setModelStatus(await getModelStatus());
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleAuth(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      if (authMode === 'forgot') {
        setMessage('Şifre sıfırlama akışı demo ortamında e-posta sağlayıcısı bağlanınca aktif edilir.');
        return;
      }
      const payload = authMode === 'register'
        ? { full_name: auth.fullName || 'HantaVision User', email: auth.email, password: auth.password }
        : { email: auth.email, password: auth.password };
      const nextSession = authMode === 'register' ? await register(payload) : await login(payload);
      saveSession(nextSession);
      setSession(nextSession);
      setMessage('Oturum açıldı. Analiz paneli hazır.');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function handleFileSelect(nextFile) {
    if (!nextFile) return;
    setFile(nextFile);
    setResult(null);
    setMessage(`Dosya hazır: ${nextFile.name}`);
  }

  function handleDrop(event) {
    event.preventDefault();
    handleFileSelect(event.dataTransfer.files?.[0]);
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!session?.accessToken) {
      setMessage('Analiz için önce giriş yapmalısın. Demo admin bilgileri formda hazır.');
      document.querySelector('#auth')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (!file) {
      setMessage('Analiz için bir görüntü seç.');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const analysis = await uploadAnalysis(file, session.accessToken);
      setResult(analysis);
      setProgress(100);
      setActiveStep(analysisSteps.length - 1);
      await refreshData(session.accessToken, isAdmin);
      setMessage('Analiz tamamlandı. AI Diagnostic Report oluşturuldu.');
    } catch (error) {
      setProgress(0);
      setActiveStep(-1);
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!latest || !session?.accessToken) return;
    setMessage('PDF rapor hazırlanıyor.');
    try {
      const blob = await downloadReport(latest.id, session.accessToken);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${safeFileName(latest.fileName)}-ai-medical-report.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1200);
      setMessage('PDF rapor indirildi.');
    } catch (error) {
      setMessage(error.message);
    }
  }

  function logout() {
    saveSession(null);
    setSession(null);
    setResult(null);
    setHistory([]);
    setOverview(null);
    setPerformance(null);
    setMessage('Oturum kapatıldı.');
  }

  function handleAssistantSubmit(event) {
    event.preventDefault();
    const question = assistantQuestion.toLocaleLowerCase('tr-TR');
    if (question.includes('risk')) {
      setAssistantAnswer(isValidatedAnalysis(latest)
        ? `Bu analizde risk durumu ${riskLabel(latest)}. Güven skoru ${formatPercent(latest?.confidence || avgConfidence)} ve sonuç uzman değerlendirmesiyle doğrulanmalı.`
        : 'Bu kayıt eski demo döneminden kalmış olabilir. Profesyonel modda validasyonlu model artefact olmadan yeni risk sonucu üretilmez.');
    } else if (question.includes('model') || question.includes('nasıl')) {
      setAssistantAnswer(modelStatus?.acceptsUploads
        ? `${selectedModel}, yüklü validasyonlu artefact üzerinden çalışır. Ön işleme, sınıflandırma ve artefact destekliyorsa Grad-CAM birlikte raporlanır.`
        : 'Profesyonel mod aktif: validasyonlu model artefact yüklenmeden sistem kullanıcı görseline risk sonucu üretmez. Önce etiketli hantavirüs verisiyle eğitim ve test metrikleri gerekiyor.');
    } else if (question.includes('tanı')) {
      setAssistantAnswer('Bu sistem kesin tıbbi tanı koymaz. Çıktı yalnızca ön değerlendirme ve eğitim amaçlıdır; kesin tanı için uzman hekime başvurulmalıdır.');
    } else {
      setAssistantAnswer('Sonuç; risk seviyesi, güven skoru, görüntü kalitesi ve açıklanabilir AI bulguları birlikte okunarak yorumlanır.');
    }
  }

  const dashboardCards = [
    { label: 'Toplam Analiz', value: totalAnalyses, icon: FileSearch },
    { label: 'Aktif AI Modeli', value: selectedModel, icon: BrainCircuit },
    { label: 'Ortalama Güven Skoru', value: formatPercent(avgConfidence), icon: Gauge },
    { label: 'Desteklenen Görsel Türü', value: '5 sınıf', icon: Layers3 },
    { label: 'Sistem Durumu', value: modelStatus?.acceptsUploads ? 'Validated' : 'Model gerekli', icon: Activity },
  ];

  return (
    <main className='app-shell'>
      {booting && <CinematicBoot />}
      <Header session={session} logout={logout} />

      <section className='hero-section' id='top'>
        <div className='hero-copy'>
          <p className='eyebrow'>Modern Medical AI Research Platform</p>
          <h1>HantaVision AI</h1>
          <p className='hero-lead'>AI destekli hantavirüs görüntü analiz platformu</p>
          <p className='hero-subtitle'>Next-Generation Medical Image Intelligence</p>
          <p className='hero-description'>
            Bu sistem akciğer röntgeni, kemirgen görüntüsü ve mikroskobik görüntüleri analiz ederek hantavirüs ile ilişkili riskleri yapay zeka destekli olarak değerlendirir.
          </p>
          <div className='hero-actions'>
            <a className='primary-action' href='#analysis'><UploadCloud />Görüntü Analiz Et</a>
            <a className='secondary-action' href='#workflow'><FileText />Sistem Nasıl Çalışır?</a>
          </div>
          <div className='mode-selector' aria-label='Analiz modu'>
            {modeOptions.map((option) => (
              <button type='button' key={option} className={analysisMode === option ? 'active' : ''} onClick={() => setAnalysisMode(option)}>
                {option}
              </button>
            ))}
          </div>
        </div>
        <HeroVisual />
      </section>

      <section className='dashboard-strip' aria-label='Sistem istatistikleri'>
        {dashboardCards.map(({ label, value, icon: Icon }) => (
          <article className='stat-card' key={label}>
            <Icon />
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className='analysis-section' id='analysis'>
        <div className='section-heading'>
          <p className='eyebrow'>Biological Image Upload Zone</p>
          <h2>Akıllı görüntü analizi</h2>
          <p>Görüntü türü otomatik algılanır, uygun model seçilir ve açıklanabilir AI raporu oluşturulur.</p>
        </div>

        <div className='analysis-grid'>
          <form className={`upload-zone ${file ? 'has-file' : ''}`} onSubmit={handleUpload} onDragOver={(event) => event.preventDefault()} onDrop={handleDrop}>
            <input
              ref={fileInputRef}
              type='file'
              accept='image/png,image/jpeg,image/jpg,image/webp,image/bmp,image/tiff,.dcm,.dicom,application/dicom'
              onChange={(event) => handleFileSelect(event.target.files?.[0])}
            />
            <button type='button' className='upload-target' onClick={() => fileInputRef.current?.click()}>
              <UploadCloud />
              <strong>Görüntüyü buraya sürükle veya yükle</strong>
              <span>{file ? file.name : 'PNG, JPG, JPEG, DICOM desteği'}</span>
            </button>
            <div className='upload-meta'>
              <span>PNG</span>
              <span>JPG</span>
              <span>JPEG</span>
              <span>DICOM desteği</span>
              <span>Maksimum dosya boyutu: 12 MB</span>
            </div>
            <div className='detected-box'>
              <div>
                <span>Algılanan Görüntü Türü</span>
                <strong>{displayedImageType}</strong>
              </div>
              <div>
                <span>Seçilen Model</span>
                <strong>{selectedModel}</strong>
              </div>
            </div>
            <button className='primary-action submit-analysis' disabled={loading || !file} type='submit'>
              <Play />{loading ? 'Analiz çalışıyor' : 'AI Analizi Başlat'}
            </button>
          </form>

          <AnalysisProgress loading={loading} progress={progress} activeStep={activeStep} />

          <HeatmapPreview file={file} previewUrl={previewUrl} result={latest} inferred={inferred} loading={loading} />
        </div>

        {message && <p className='message'>{message}</p>}
      </section>

      <section className='report-layout'>
        <ReportPanel latest={latest} displayedImageType={displayedImageType} selectedModel={selectedModel} modelArchitecture={modelArchitecture} onDownloadPdf={handleDownloadPdf} />
        <AuthPanel
          session={session}
          auth={auth}
          setAuth={setAuth}
          authMode={authMode}
          setAuthMode={setAuthMode}
          loading={loading}
          onSubmit={handleAuth}
          onGoogle={() => setMessage('Google ile giriş için Firebase/Auth sağlayıcısı bağlandığında OAuth aktif edilir.')}
          logout={logout}
        />
      </section>

      {session && <HistoryPanel history={history} setResult={setResult} onDownloadPdf={handleDownloadPdf} />}

      <section className='knowledge-grid' id='workflow'>
        <article className='info-panel how-panel'>
          <p className='eyebrow'>Nasıl çalışır?</p>
          <h2>3 adımlı analiz hattı</h2>
          <div className='steps-row'>
            {[
              ['Görsel yükle', UploadCloud],
              ['AI modeli analiz eder', BrainCircuit],
              ['Risk raporu oluşturulur', FileText],
            ].map(([label, Icon], index) => (
              <div className='workflow-step' key={label}>
                <Icon />
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{label}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className='info-panel model-panel'>
          <p className='eyebrow'>Model bilgisi</p>
          <h2>Görüntü sınıflandırma ve açıklanabilir AI</h2>
          <p>Bu sistem görüntü sınıflandırma, ön işleme, segmentasyon ve açıklanabilir yapay zeka tekniklerini kullanır.</p>
          <div className='model-comparison'>
            {['ResNet', 'EfficientNet', 'Vision Transformer', 'CNN Ensemble'].map((model) => <span key={model}>{model}</span>)}
          </div>
        </article>
      </section>

      <section className='knowledge-grid'>
        <article className='info-panel'>
          <p className='eyebrow'>Risk seviyeleri</p>
          <h2>Sonuç yorumlama</h2>
          <div className='risk-list'>
            {riskLevels.map(([title, text]) => (
              <div key={title}>
                <strong>{title}</strong>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </article>

        <article className='info-panel'>
          <p className='eyebrow'>Kullanılan teknolojiler</p>
          <h2>AI araştırma altyapısı</h2>
          <div className='tech-cloud'>
            {techStack.map((tech) => <span key={tech}>{tech}</span>)}
          </div>
        </article>
      </section>

      <section className='dataset-section'>
        <div>
          <p className='eyebrow'>Dataset Explorer</p>
          <h2>Örnek veri dağılımı</h2>
        </div>
        <div className='dataset-bars'>
          {[
            ['X-Ray', 42],
            ['Rodent', 24],
            ['Microscopy', 19],
            ['Laboratory', 10],
            ['Unknown', 5],
          ].map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <div><i style={{ width: `${value}%` }} /></div>
              <strong>{value}%</strong>
            </div>
          ))}
        </div>
      </section>

      <section className='safety-section'>
        <article className='warning-panel'>
          <AlertTriangle />
          <div>
            <strong>Medical Disclaimer</strong>
            <p>Bu sistem kesin tıbbi tanı koymaz. Sonuçlar yalnızca ön değerlendirme ve eğitim amaçlıdır. Kesin tanı için uzman hekime başvurulmalıdır.</p>
          </div>
        </article>
        <article className='privacy-panel'>
          <LockKeyhole />
          <div>
            <strong>Gizlilik ve veri güvenliği</strong>
            <p>Kullanıcı görüntüleri güvenli şekilde işlenir. Analiz geçmişi yalnızca oturum sahibi kullanıcı panelinde görüntülenir.</p>
          </div>
        </article>
      </section>

      <section className='faq-section'>
        <div className='section-heading'>
          <p className='eyebrow'>SSS</p>
          <h2>Sık sorulan sorular</h2>
        </div>
        <div className='faq-grid'>
          {faqItems.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>

      <AssistantWidget
        open={assistantOpen}
        setOpen={setAssistantOpen}
        question={assistantQuestion}
        setQuestion={setAssistantQuestion}
        answer={assistantAnswer}
        onSubmit={handleAssistantSubmit}
      />

      <footer className='footer'>
        <strong>HantaVision AI</strong>
        <span>Research/Education Purpose</span>
        <a href='mailto:contact@hantavision.ai'>Contact</a>
        <a href='#top'>Privacy Policy</a>
        <a href='#top'>Medical Disclaimer</a>
      </footer>
    </main>
  );
}

function Header({ session, logout }) {
  return (
    <header className='topbar'>
      <a className='brand' href='#top'>
        <Stethoscope />
        <span>HantaVision AI</span>
      </a>
      <nav>
        <a href='#analysis'>Analiz</a>
        <a href='#workflow'>Nasıl çalışır</a>
        <a href='#auth'>Giriş</a>
      </nav>
      {session ? (
        <button type='button' className='small-action' onClick={logout}><X />Çıkış</button>
      ) : (
        <a className='small-action' href='#auth'><LogIn />Giriş yap</a>
      )}
    </header>
  );
}

function CinematicBoot() {
  return (
    <div className='boot-screen' aria-hidden='true'>
      <div className='boot-frame'>
        <ScanLine />
        <span>Initializing HantaVision AI</span>
        <strong>GNGREGEHAN SUNAR</strong>
        <i />
      </div>
    </div>
  );
}

function HeroVisual() {
  return (
    <div className='hero-visual' aria-label='Holografik medikal görüntü motoru'>
      <div className='holo-stage'>
        <div className='holo-lung left' />
        <div className='holo-lung right' />
        <div className='holo-spine' />
        <div className='virus-core'><Zap /></div>
        <div className='scan-ring ring-one' />
        <div className='scan-ring ring-two' />
      </div>
      <div className='system-status'>
        <span><CheckCircle2 />AI Core: Active</span>
        <span><CheckCircle2 />Medical Vision Engine: Online</span>
        <span><CheckCircle2 />Validated Model Gate: Strict</span>
      </div>
    </div>
  );
}

function AnalysisProgress({ loading, progress, activeStep }) {
  return (
    <article className='analysis-log'>
      <div className='panel-title'>
        <Cpu />
        <div>
          <span>Analiz logları</span>
          <strong>{loading ? 'Medical Vision Engine çalışıyor' : 'Hazır'}</strong>
        </div>
      </div>
      <div className='progress-track'><i style={{ width: `${progress}%` }} /></div>
      <ol>
        {analysisSteps.map((step, index) => (
          <li key={step} className={index <= activeStep ? 'active' : ''}>
            <CheckCircle2 />
            <span>{step}</span>
          </li>
        ))}
      </ol>
      <div className='terminal-lines'>
        <span>Image preprocessing...</span>
        <span>Feature extraction...</span>
        <span>Validated model gate...</span>
        <span>Metrics-backed report check...</span>
      </div>
    </article>
  );
}

function HeatmapPreview({ file, previewUrl, result, inferred, loading }) {
  const regions = result?.attention?.regions?.length ? result.attention.regions : [];
  return (
    <article className='heatmap-panel'>
      <div className='panel-title'>
        <Eye />
        <div>
          <span>Grad-CAM heatmap</span>
          <strong>AI’nin dikkat ettiği bölgeler</strong>
        </div>
      </div>
      <div className={`image-scan ${loading ? 'is-scanning' : ''}`}>
        {previewUrl ? <img src={previewUrl} alt='Yüklenen medikal görsel önizlemesi' /> : <div className='dicom-placeholder'><Microscope /><span>{file ? 'DICOM / önizleme dışı dosya' : 'Görüntü bekleniyor'}</span></div>}
        <div className='heat-layer'>
          {regions.map((region, index) => (
            <span
              key={`${region.label}-${index}`}
              className='heat-region'
              style={{ left: `${region.x}%`, top: `${region.y}%`, width: `${region.w}%`, height: `${region.h}%` }}
              title={`${region.label} ${Math.round(region.score * 100)}%`}
            />
          ))}
        </div>
        <i className='scan-beam' />
      </div>
      {!regions.length && <p className='heatmap-note'>{file ? 'Gerçek Grad-CAM alanı validasyonlu model sonucu gelince gösterilir.' : 'Görüntü ve model sonucu bekleniyor.'}</p>}
    </article>
  );
}

function ReportPanel({ latest, displayedImageType, selectedModel, modelArchitecture, onDownloadPdf }) {
  const validated = isValidatedAnalysis(latest);
  return (
    <section className='report-panel'>
      <div className='report-header'>
        <div>
          <p className='eyebrow'>AI Diagnostic Report</p>
          <h2>{latest ? (validated ? latest.hantavirusResult : 'Legacy demo sonucu gizlendi') : 'Analiz sonucu bekleniyor'}</h2>
        </div>
        <span className={`risk-badge ${riskClass(latest)}`}>Risk Durumu: {riskLabel(latest)}</span>
      </div>
      <div className='report-metrics'>
        <div><span>Güven Skoru</span><strong>{latest ? (validated ? formatPercent(latest.confidence) : 'Legacy') : 'Beklemede'}</strong></div>
        <div><span>Görüntü Türü</span><strong>{displayedImageType}</strong></div>
        <div><span>Model</span><strong>{modelArchitecture}</strong></div>
        <div><span>Analiz Süresi</span><strong>{latest ? '2.4 saniye' : 'Beklemede'}</strong></div>
      </div>
      <div className='explain-panel'>
        <FlaskConical />
        <p>{latest ? (validated ? latest.explanation : 'Bu eski kayıt validasyonlu model runtime bilgisi taşımıyor. Profesyonel modda yeni analizler yalnızca onaylı model artefact ile raporlanır.') : 'Profesyonel modda sahte bulgu üretilmez. Gerçek açıklama, validasyonlu CNN/ResNet/EfficientNet artefact yüklendikten ve analiz tamamlandıktan sonra burada gösterilir.'}</p>
      </div>
      <div className='report-actions'>
        <button type='button' className='primary-action' onClick={onDownloadPdf} disabled={!latest}><Download />AI Medical Report PDF</button>
        <span>Model seçimi: {selectedModel}</span>
      </div>
    </section>
  );
}

function AuthPanel({ session, auth, setAuth, authMode, setAuthMode, loading, onSubmit, onGoogle, logout }) {
  if (session) {
    return (
      <section className='auth-card user-card' id='auth'>
        <p className='eyebrow'>Kullanıcı paneli</p>
        <h2>{session.user.fullName}</h2>
        <p>{session.user.email}</p>
        <div className='user-role'><ShieldCheck />{session.user.role}</div>
        <button type='button' className='secondary-action full-width' onClick={logout}><X />Çıkış yap</button>
      </section>
    );
  }

  return (
    <section className='auth-card' id='auth'>
      <p className='eyebrow'>Kullanıcı girişi</p>
      <h2>Profesyonel oturum</h2>
      <div className='auth-tabs'>
        <button type='button' className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}><LogIn />Giriş yap</button>
        <button type='button' className={authMode === 'register' ? 'active' : ''} onClick={() => setAuthMode('register')}><UserPlus />Üye ol</button>
        <button type='button' className={authMode === 'forgot' ? 'active' : ''} onClick={() => setAuthMode('forgot')}><LockKeyhole />Şifremi unuttum</button>
      </div>
      <form onSubmit={onSubmit} className='auth-form'>
        {authMode === 'register' && <label>Ad Soyad<input value={auth.fullName} onChange={(event) => setAuth({ ...auth, fullName: event.target.value })} /></label>}
        <label>E-posta<input type='email' value={auth.email} onChange={(event) => setAuth({ ...auth, email: event.target.value })} /></label>
        {authMode !== 'forgot' && <label>Parola<input type='password' value={auth.password} onChange={(event) => setAuth({ ...auth, password: event.target.value })} /></label>}
        <button className='primary-action full-width' disabled={loading}>{loading ? 'Bekleyin' : authMode === 'register' ? 'Üye ol' : authMode === 'forgot' ? 'Sıfırlama iste' : 'Giriş yap'}</button>
      </form>
      <button type='button' className='secondary-action full-width' onClick={onGoogle}><Chrome />Google ile giriş</button>
    </section>
  );
}

function HistoryPanel({ history: items, setResult, onDownloadPdf }) {
  return (
    <section className='history-section'>
      <div className='section-heading'>
        <p className='eyebrow'>Geçmiş analizler</p>
        <h2>Kullanıcı analiz geçmişi</h2>
      </div>
      <div className='history-table'>
        <div className='history-head'>
          <span>Tarih</span>
          <span>Görsel türü</span>
          <span>Risk sonucu</span>
          <span>Güven skoru</span>
          <span>Rapor</span>
        </div>
        {items.length === 0 && <p className='empty-state'>Henüz kayıtlı analiz yok.</p>}
        {items.map((item) => (
          <button type='button' className='history-row' key={item.id} onClick={() => setResult(item)}>
            <span>{formatDate(item.createdAt)}</span>
            <span>{normalizeImageType(item.imageType)}</span>
            <span>{riskLabel(item)}</span>
            <span>{isValidatedAnalysis(item) ? formatPercent(item.confidence) : 'Legacy'}</span>
            <span onClick={(event) => { event.stopPropagation(); onDownloadPdf(); }}><Download />Rapor görüntüle</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function AssistantWidget({ open, setOpen, question, setQuestion, answer, onSubmit }) {
  return (
    <div className={`assistant-widget ${open ? 'open' : ''}`}>
      {open && (
        <section className='assistant-panel'>
          <div className='assistant-head'>
            <span><Bot />AI asistan</span>
            <button type='button' onClick={() => setOpen(false)}><X /></button>
          </div>
          <p>{answer}</p>
          <form onSubmit={onSubmit}>
            <input value={question} onChange={(event) => setQuestion(event.target.value)} />
            <button type='submit'><ChevronRight /></button>
          </form>
        </section>
      )}
      <button type='button' className='assistant-toggle' onClick={() => setOpen((value) => !value)}><MessageCircle />AI asistan</button>
    </div>
  );
}

export default App;
