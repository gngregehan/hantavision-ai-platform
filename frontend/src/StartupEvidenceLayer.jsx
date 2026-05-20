import { useEffect, useMemo, useState } from 'react';
import {
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Database,
  FileText,
  LineChart,
  ShieldCheck,
  X,
} from 'lucide-react';
import { assistantChat, getModelStatus, getResearchEvidence } from './lib/api';

const fallbackEvidence = {
  mode: 'Hantavirus-only evidence mode',
  honestyNotice: 'Kaynak kayıt sistemi yükleniyor. Klinik doğrulama metrikleri gerçek eğitim çıktısı olmadan gösterilmez.',
  datasets: [],
  referenceMedia: [],
  auxiliaryDatasets: [],
  models: [],
  validationProtocol: [],
  bibliography: [],
};

function statusLabel(value = '') {
  return value.replaceAll('-', ' ');
}

function metricValue(value) {
  if (value === null || value === undefined) return 'Pending';
  if (typeof value === 'number') return value.toFixed(3);
  return value;
}

export default function StartupEvidenceLayer() {
  const [evidence, setEvidence] = useState(fallbackEvidence);
  const [modelStatus, setModelStatus] = useState(null);
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('Dataset ve metrikler gerçek mi?');
  const [answer, setAnswer] = useState('Sorunu dataset, model, metrik veya risk olarak sorabilirsin. Yanıtlar hantavirüs kaynak kayıt sistemine göre verilir.');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getResearchEvidence()
      .then((payload) => setEvidence({ ...fallbackEvidence, ...payload }))
      .catch(() => setEvidence(fallbackEvidence));
    getModelStatus()
      .then(setModelStatus)
      .catch(() => setModelStatus(null));
  }, []);

  const registryStats = useMemo(() => [
    { label: 'Hantavirus Dataset', value: evidence.datasets.length || '2+', icon: Database },
    { label: 'Model Adayı', value: evidence.models.length || '3', icon: BrainCircuit },
    { label: 'Validation Metrics', value: modelStatus?.runtime?.ready ? 'Loaded' : 'Pending', icon: LineChart },
    { label: 'Prediction Gate', value: modelStatus?.acceptsUploads ? 'Open' : 'Locked', icon: ShieldCheck },
  ], [evidence, modelStatus]);

  async function askAssistant(event) {
    event.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const response = await assistantChat({
        message: question,
        context: {
          risk: 'research-mode',
          imageType: 'hantavirus evidence registry',
          model: 'CNN / ResNet-50 / EfficientNet-B0',
        },
      });
      setAnswer(response.reply);
    } catch {
      setAnswer('AI asistan şu an API yanıtı alamadı; yine de sistemin kuralı net: sahte metrik yok, sadece hantavirüs kaynaklı veri ve eğitim sonrası doğrulama.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className='startup-evidence-layer' id='hantavirus-evidence'>
        <div className='evidence-hero'>
          <p>Startup-Level Medical AI Evidence Pack</p>
          <h2>Hantavirüs odaklı veri seti, model ve doğrulama katmanı</h2>
          <span>{evidence.honestyNotice}</span>
        </div>

        <div className='evidence-stat-grid'>
          {registryStats.map(({ label, value, icon: Icon }) => (
            <article key={label}>
              <Icon />
              <span>{label}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </div>

        <div className={`model-gate ${modelStatus?.acceptsUploads ? 'ready' : 'locked'}`}>
          <ShieldCheck />
          <div>
            <span>Production inference gate</span>
            <strong>{modelStatus?.acceptsUploads ? 'Validated model installed' : 'Validated model required'}</strong>
            <p>{modelStatus?.predictionPolicy || 'Upload predictions are blocked until the API confirms a validated model artifact.'}</p>
            <small>{modelStatus?.runtime?.reason || 'Model status endpoint is loading.'}</small>
          </div>
        </div>

        <div className='evidence-board'>
          <div className='evidence-heading'>
            <p>Etiketli veri setleri</p>
            <h3>Sadece hantavirüs ilişkili kaynaklar</h3>
          </div>
          <div className='dataset-registry-grid'>
            {evidence.datasets.map((dataset) => (
              <article key={dataset.id}>
                <div className='registry-kicker'><Database />{statusLabel(dataset.status)}</div>
                <h4>{dataset.name}</h4>
                <p>{dataset.hantavirusRelation}</p>
                <dl>
                  <div><dt>Modality</dt><dd>{dataset.modality}</dd></div>
                  <div><dt>Label</dt><dd>{dataset.labelSignal}</dd></div>
                  <div><dt>Files</dt><dd>{dataset.files?.join(', ')}</dd></div>
                  <div><dt>Training</dt><dd>{dataset.trainingSuitability}</dd></div>
                </dl>
                <a href={dataset.url} target='_blank' rel='noreferrer'>Kaynağı aç</a>
              </article>
            ))}
          </div>
        </div>

        <div className='evidence-board'>
          <div className='evidence-heading'>
            <p>CNN / ResNet / EfficientNet</p>
            <h3>Eğitilmiş model ve validasyon panosu</h3>
          </div>
          <div className='model-validation-grid'>
            {evidence.models.map((model) => (
              <article key={model.id}>
                <div className='registry-kicker'><BrainCircuit />{statusLabel(model.trainingStatus)}</div>
                <h4>{model.architecture}</h4>
                <p>{model.target}</p>
                <div className='metrics-grid'>
                  {['accuracy', 'precision', 'recall', 'f1', 'auroc'].map((metric) => (
                    <span key={metric}><small>{metric}</small>{metricValue(model.metrics?.[metric])}</span>
                  ))}
                </div>
                <strong>{model.metrics?.note}</strong>
              </article>
            ))}
          </div>
        </div>

        <div className='evidence-board split-board'>
          <article>
            <div className='evidence-heading'>
              <p>Reference media</p>
              <h3>Kaynaklı eğitim dışı örnekler</h3>
            </div>
            <div className='reference-media-list'>
              {evidence.referenceMedia.map((item) => (
                <a href={item.url} target='_blank' rel='noreferrer' key={item.id}>
                  <FileText />
                  <span>{item.name}</span>
                  <small>{item.trainingSuitability}</small>
                </a>
              ))}
            </div>
          </article>

          <article>
            <div className='evidence-heading'>
              <p>Validation protocol</p>
              <h3>Doğrulama akışı</h3>
            </div>
            <ol className='validation-steps'>
              {evidence.validationProtocol.map((step) => (
                <li key={step}><CheckCircle2 />{step}</li>
              ))}
            </ol>
          </article>
        </div>

        <div className='evidence-board'>
          <div className='evidence-heading'>
            <p>Kaggle / auxiliary discovery</p>
            <h3>HantavirÃ¼s dÄ±ÅŸÄ± kaynaklar sadece yardÄ±mcÄ±</h3>
          </div>
          <div className='source-registry-grid'>
            {evidence.auxiliaryDatasets.map((dataset) => (
              <a href={dataset.url} target='_blank' rel='noreferrer' key={dataset.id}>
                <span>{statusLabel(dataset.status)}</span>
                <strong>{dataset.name}</strong>
                <small>{dataset.trainingSuitability}</small>
              </a>
            ))}
          </div>
        </div>

        <div className='evidence-board' id='sources'>
          <div className='evidence-heading'>
            <p>Kaynakça</p>
            <h3>Neyi nereden aldık?</h3>
          </div>
          <div className='source-registry-grid'>
            {evidence.bibliography.map((source) => (
              <a href={source.url} target='_blank' rel='noreferrer' key={source.url}>
                <span>{source.publisher}</span>
                <strong>{source.title}</strong>
                <small>{source.note}</small>
              </a>
            ))}
          </div>
        </div>
      </section>

      <div className={`startup-assistant ${open ? 'open' : ''}`}>
        {open && (
          <section>
            <div>
              <span><Bot />HantaVision AI Assistant</span>
              <button type='button' onClick={() => setOpen(false)}><X /></button>
            </div>
            <p>{loading ? 'Yanıt hazırlanıyor...' : answer}</p>
            <form onSubmit={askAssistant}>
              <input value={question} onChange={(event) => setQuestion(event.target.value)} />
              <button type='submit' disabled={loading}><ChevronRight /></button>
            </form>
          </section>
        )}
        <button type='button' onClick={() => setOpen((value) => !value)}><Bot />AI asistan</button>
      </div>
    </>
  );
}
