import { useEffect, useMemo, useState } from 'react';
import {
  BrainCircuit,
  CheckCircle2,
  Database,
  FileText,
  LineChart,
  ShieldCheck,
} from 'lucide-react';
import { getModelStatus, getResearchEvidence } from './lib/api';

const fallbackEvidence = {
  mode: 'Yalnızca hantavirüs kanıt modu',
  honestyNotice: 'Kaynak kayıt sistemi yükleniyor. Klinik doğrulama metrikleri gerçek eğitim çıktısı olmadan gösterilmez.',
  datasets: [],
  referenceMedia: [],
  auxiliaryDatasets: [],
  models: [],
  validationProtocol: [],
  bibliography: [],
};

function statusLabel(value = '') {
  const normalized = value.replaceAll('-', ' ');
  const dictionary = {
    'hantavirus specific': 'hantavirüse özel',
    'hantavirus reference': 'hantavirüs referansı',
    'auxiliary only': 'yalnızca yardımcı',
    'requires training': 'eğitim gerekli',
    'curation ready': 'kürasyona hazır',
    'requires label curation': 'etiket kürasyonu gerekli',
    'manual verification required': 'manuel doğrulama gerekli',
    'teacher provided genomic source': 'hocanın verdiği genomik kaynak',
    'pipeline ready': 'hat hazır',
    'pending real training run': 'gerçek eğitim koşusu bekleniyor',
    candidate: 'aday',
    pending: 'beklemede',
    loaded: 'yüklü',
  };
  return dictionary[normalized] || normalized;
}

function metricValue(value) {
  if (value === null || value === undefined) return 'Beklemede';
  if (typeof value === 'number') return value.toFixed(3);
  return value;
}

export default function StartupEvidenceLayer() {
  const [evidence, setEvidence] = useState(fallbackEvidence);
  const [modelStatus, setModelStatus] = useState(null);

  useEffect(() => {
    getResearchEvidence()
      .then((payload) => setEvidence({ ...fallbackEvidence, ...payload }))
      .catch(() => setEvidence(fallbackEvidence));
    getModelStatus()
      .then(setModelStatus)
      .catch(() => setModelStatus(null));
  }, []);

  const registryStats = useMemo(() => [
    { label: 'Hantavirüs Veri Seti', value: evidence.datasets.length || '2+', icon: Database },
    { label: 'Model Adayı', value: evidence.models.length || '3', icon: BrainCircuit },
    { label: 'Doğrulama Metrikleri', value: modelStatus?.runtime?.ready ? 'Yüklü' : 'Beklemede', icon: LineChart },
    { label: 'Tahmin Kapısı', value: modelStatus?.acceptsDiagnosticPredictions ? 'Açık' : 'Model bekliyor', icon: ShieldCheck },
  ], [evidence, modelStatus]);

  return (
    <>
      <section className='startup-evidence-layer' id='hantavirus-evidence'>
        <div className='evidence-hero'>
          <p>Startup seviyesinde medikal AI kanıt paketi</p>
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

        <div className={`model-gate ${modelStatus?.acceptsDiagnosticPredictions ? 'ready' : 'locked'}`}>
          <ShieldCheck />
          <div>
            <span>Üretim çıkarım kapısı</span>
            <strong>{modelStatus?.acceptsDiagnosticPredictions ? 'Doğrulanmış model kurulu' : 'Doğrulanmış model gerekli'}</strong>
            <p>{modelStatus?.predictionPolicy || 'API doğrulanmış model artefact onayı verene kadar tıbbi risk tahmini kapalıdır.'}</p>
            <small>{modelStatus?.runtime?.reason || 'Model durumu yükleniyor.'}</small>
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
                  <div><dt>Modalite</dt><dd>{dataset.modality}</dd></div>
                  <div><dt>Etiket</dt><dd>{dataset.labelSignal}</dd></div>
                  <div><dt>Dosyalar</dt><dd>{dataset.files?.join(', ')}</dd></div>
                  <div><dt>Eğitim</dt><dd>{dataset.trainingSuitability}</dd></div>
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
              <p>Referans medya</p>
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
              <p>Doğrulama protokolü</p>
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
            <p>Kaggle / yardımcı kaynak keşfi</p>
            <h3>Hantavirüs dışı kaynaklar sadece yardımcı</h3>
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
    </>
  );
}
