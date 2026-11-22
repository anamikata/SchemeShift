import { useMemo, useState } from 'react';
import {
  ArrowUpRight, ArrowRight, Check, CheckCircle2, ChevronDown, CircleAlert,
  FileText, FileUp, Globe2, Info, LoaderCircle, ShieldCheck, Sparkles,
  UploadCloud, XCircle,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || ''; // Same-origin /api; Vite and Nginx proxy it to FastAPI.

const copy = {
  en: {
    eyebrow: 'KERALA POLICY INTELLIGENCE',
    titleA: 'Understand what changed.',
    titleB: 'See who it affects.',
    intro: 'Compare two versions of a government order, trace each extracted condition to its source, and test a sample applicant profile.',
    old: 'OLDER ORDER', newer: 'NEWER ORDER / AMENDMENT', uploadHint: 'Upload a searchable PDF · max 18 MB',
    profile: 'Applicant profile', profileHint: 'Optional · evaluated locally by the rule engine, not sent to Gemini',
    analyze: 'Compare versions', analyzing: 'Reading and verifying documents…',
    age: 'Age (years)', income: 'Annual family income (₹)', marks: 'Marks (%)', community: 'Community',
    rank: 'University rank', degree: 'Degree level', discipline: 'Discipline', fullTime: 'Full-time research',
    otherFellowship: 'Receiving another fellowship', onlyChild: 'Only applicant from family', previous: 'Previously received this scheme',
    yes: 'Yes', no: 'No', select: 'Select', results: 'Comparison report', oldRules: 'Older version', newRules: 'Newer version',
    changes: 'What changed', warnings: 'Important limitations', verified: 'evidence verified', rejected: 'not verified',
    oldOutcome: 'Under older order', newOutcome: 'Under newer order',
    meets: 'Meets all evaluated conditions', fails: 'Fails one or more conditions', insufficient: 'Insufficient evidence', notEvaluated: 'Not evaluated',
    modified: 'Modified', unchanged: 'Unchanged', notRestated: 'Not restated in newer document', notFound: 'Not found in older document', review: 'Needs manual review', unchangedByScope: 'Unchanged by explicitly limited amendment', scopeVerified: 'Limited amendment scope verified', scopeUnverified: 'Limited amendment scope could not be verified',
    source: 'Source quotation', page: 'Page', oldValue: 'Older value', newValue: 'Newer value',
    disclaimer: 'SchemeShift is an independent comparison aid, not a government service or official eligibility decision. Always confirm the latest applicable order with the issuing department.',
    privacy: 'PDFs are processed in memory and are not saved by this MVP. Only document text is sent to the configured AI provider; applicant profile fields are evaluated in local code.',
    reset: 'Clear report', empty: 'Your comparison will appear here.', choose: 'Choose PDF',
    workspaceTitle: 'Compare two versions', workspaceSub: 'Start with an original order and its amendment or revised guidelines.', filesNotStored: 'Files are not stored',
    profileLocal: 'Applicant profile stays in the rule engine; it is not sent to Gemini.', passed: 'passed', failed: 'failed', unknown: 'unknown',
    conditions: 'extracted conditions', items: 'items', dateMissing: 'Date not extracted', noRules: 'No rules were extracted from this document.',
    demoLine: 'Two source documents in. A traceable comparison out.', readMore: 'Read carefully',
    amendmentsTitle: 'Verified explicit corrections', correctionVerified: 'Source-verified correction', correctionUnverified: 'Could not verify correction', target: 'Corrected item', from: 'Original', to: 'Corrected',
  },
  ml: {
    eyebrow: 'കേരള സർക്കാർ ഉത്തരവ് വിശകലനം',
    titleA: 'എന്താണ് മാറിയത്?',
    titleB: 'ആരെയാണ് ബാധിക്കുന്നത്?',
    intro: 'സർക്കാർ ഉത്തരവുകളുടെ രണ്ട് പതിപ്പുകൾ താരതമ്യം ചെയ്യുക. ഓരോ വ്യവസ്ഥയ്ക്കും ഉറവിട തെളിവ് കാണുക. അപേക്ഷകന്റെ വിവരങ്ങൾ ഉപയോഗിച്ച് വ്യവസ്ഥകൾ പരിശോധിക്കുക.',
    old: 'പഴയ ഉത്തരവ്', newer: 'പുതിയ ഉത്തരവ് / ഭേദഗതി', uploadHint: 'തിരയാവുന്ന PDF അപ്‌ലോഡ് ചെയ്യുക · പരമാവധി 18 MB',
    profile: 'അപേക്ഷകന്റെ വിവരങ്ങൾ', profileHint: 'ഐച്ഛികം · പ്രൊഫൈൽ Gemini-യിലേക്ക് അയയ്ക്കാതെ നിയമ എൻജിനിൽ പരിശോധിക്കും',
    analyze: 'പതിപ്പുകൾ താരതമ്യം ചെയ്യുക', analyzing: 'രേഖകൾ പരിശോധിക്കുന്നു…',
    age: 'പ്രായം (വർഷം)', income: 'വാർഷിക കുടുംബ വരുമാനം (₹)', marks: 'മാർക്ക് (%)', community: 'സമുദായം',
    rank: 'സർവകലാശാല റാങ്ക്', degree: 'ബിരുദനില', discipline: 'വിഷയം', fullTime: 'ഫുൾ-ടൈം ഗവേഷണം',
    otherFellowship: 'മറ്റൊരു ഫെല്ലോഷിപ്പ് ലഭിക്കുന്നുണ്ടോ?', onlyChild: 'കുടുംബത്തിൽ ഈ പദ്ധതിക്ക് അപേക്ഷിക്കുന്ന ഏക വ്യക്തിയാണോ?', previous: 'ഈ പദ്ധതി മുമ്പ് ലഭിച്ചിട്ടുണ്ടോ?',
    yes: 'ഉണ്ട്', no: 'ഇല്ല', select: 'തിരഞ്ഞെടുക്കുക', results: 'താരതമ്യ റിപ്പോർട്ട്', oldRules: 'പഴയ പതിപ്പ്', newRules: 'പുതിയ പതിപ്പ്',
    changes: 'എന്താണ് മാറിയത്', warnings: 'പ്രധാന പരിമിതികൾ', verified: 'തെളിവ് പരിശോധിച്ചു', rejected: 'പരിശോധിക്കാനായില്ല',
    oldOutcome: 'പഴയ ഉത്തരവ് പ്രകാരം', newOutcome: 'പുതിയ ഉത്തരവ് പ്രകാരം',
    meets: 'പരിശോധിച്ച വ്യവസ്ഥകൾ പാലിക്കുന്നു', fails: 'ഒന്നോ അതിലധികമോ വ്യവസ്ഥകൾ പാലിക്കുന്നില്ല', insufficient: 'തെളിവ് അപര്യാപ്തം', notEvaluated: 'പരിശോധിച്ചിട്ടില്ല',
    modified: 'മാറ്റം വരുത്തി', unchanged: 'മാറ്റമില്ല', notRestated: 'പുതിയ ഉത്തരവിൽ ആവർത്തിച്ചിട്ടില്ല', notFound: 'പഴയ ഉത്തരവിൽ കണ്ടെത്തിയില്ല', review: 'മാനുഷിക പരിശോധന ആവശ്യമാണ്', unchangedByScope: 'പരിമിത ഭേദഗതിയിൽ മാറ്റമില്ല', scopeVerified: 'ഭേദഗതിയുടെ പരിധി പരിശോധിച്ചു', scopeUnverified: 'ഭേദഗതിയുടെ പരിധി സ്ഥിരീകരിക്കാനായില്ല',
    source: 'ഉറവിട ഉദ്ധരണി', page: 'പേജ്', oldValue: 'പഴയ മൂല്യം', newValue: 'പുതിയ മൂല്യം',
    disclaimer: 'SchemeShift ഒരു സ്വതന്ത്ര താരതമ്യ സഹായിയാണ്. ഇത് സർക്കാർ സേവനമോ ഔദ്യോഗിക അർഹതാ തീരുമാനമോ അല്ല. ബന്ധപ്പെട്ട വകുപ്പിൽ നിന്ന് ഏറ്റവും പുതിയ ഉത്തരവ് ഉറപ്പാക്കുക.',
    privacy: 'ഈ MVP PDF ഫയലുകൾ മെമ്മറിയിൽ മാത്രം പ്രോസസ്സ് ചെയ്യുന്നു. രേഖയിലെ ടെക്സ്റ്റ് മാത്രമാണ് AI സേവനത്തിലേക്ക് അയയ്ക്കുന്നത്; അപേക്ഷകന്റെ വിവരങ്ങൾ പ്രാദേശിക നിയമ എൻജിനിലാണ് പരിശോധിക്കുന്നത്.',
    reset: 'റിപ്പോർട്ട് മായ്ക്കുക', empty: 'താരതമ്യ റിപ്പോർട്ട് ഇവിടെ കാണിക്കും.', choose: 'PDF തിരഞ്ഞെടുക്കുക',
    workspaceTitle: 'രണ്ട് പതിപ്പുകൾ താരതമ്യം ചെയ്യുക', workspaceSub: 'യഥാർത്ഥ ഉത്തരവും അതിന്റെ ഭേദഗതിയും അല്ലെങ്കിൽ പുതുക്കിയ മാർഗ്ഗനിർദ്ദേശവും നൽകുക.', filesNotStored: 'ഫയലുകൾ സൂക്ഷിക്കുന്നില്ല',
    profileLocal: 'അപേക്ഷകന്റെ വിവരങ്ങൾ Gemini-യിലേക്ക് അയയ്ക്കില്ല; പ്രാദേശിക നിയമ എൻജിനിലാണ് പരിശോധിക്കുന്നത്.', passed: 'പാലിച്ചു', failed: 'പാലിച്ചില്ല', unknown: 'അജ്ഞാതം',
    conditions: 'വ്യവസ്ഥകൾ കണ്ടെത്തി', items: 'ഇനങ്ങൾ', dateMissing: 'തീയതി കണ്ടെത്തിയില്ല', noRules: 'ഈ രേഖയിൽ വ്യവസ്ഥകൾ കണ്ടെത്തിയില്ല.',
    demoLine: 'രണ്ട് ഉറവിട രേഖകൾ നൽകുക. തെളിവോടെയുള്ള താരതമ്യം നേടുക.', readMore: 'ശ്രദ്ധിച്ച് വായിക്കുക',
    amendmentsTitle: 'തെളിവ് പരിശോധിച്ച വ്യക്തമായ തിരുത്തലുകൾ', correctionVerified: 'ഉറവിടം പരിശോധിച്ച തിരുത്തൽ', correctionUnverified: 'തിരുത്തൽ സ്ഥിരീകരിക്കാനായില്ല', target: 'തിരുത്തിയ ഇനം', from: 'പഴയത്', to: 'തിരുത്തിയത്',
  },
};

const fieldLabelsMl = {
  max_age_years: 'പരമാവധി പ്രായം',
  max_annual_family_income_inr: 'വാർഷിക കുടുംബ വരുമാന പരിധി',
  min_marks_percent: 'കുറഞ്ഞ മാർക്ക് ശതമാനം',
  eligible_communities: 'അർഹമായ സമുദായങ്ങൾ',
  excluded_communities: 'ഒഴിവാക്കിയ സമുദായങ്ങൾ',
  university_rank_max: 'സർവകലാശാല റാങ്ക് പരിധി',
  eligible_degree_levels: 'അർഹമായ പഠനനിലകൾ',
  eligible_disciplines: 'അർഹമായ വിഷയങ്ങൾ',
  requires_full_time: 'ഫുൾ-ടൈം പഠന നിബന്ധന',
  other_fellowship_prohibited: 'മറ്റു ഫെല്ലോഷിപ്പ് നിയന്ത്രണം',
  one_child_per_family: 'ഒരു കുടുംബത്തിൽ ഒരു കുട്ടി',
  scholarship_one_time: 'ഒറ്റത്തവണ മാത്രം ലഭിക്കുന്ന പദ്ധതി',
  monthly_fellowship_inr: 'പ്രതിമാസ ഫെല്ലോഷിപ്പ്',
  max_fellowship_years: 'ഫെല്ലോഷിപ്പിന്റെ പരമാവധി കാലാവധി',
  beneficiary_limit: 'ഗുണഭോക്താക്കളുടെ പരിധി',
  application_deadline: 'അപേക്ഷയുടെ അവസാന തീയതി',
  required_documents: 'ആവശ്യമായ രേഖകൾ',
  other: 'മറ്റ് വ്യവസ്ഥ',
};

function fieldLabel(field, language) {
  return (language === 'ml' ? fieldLabelsMl[field] : fieldLabels[field]) || field;
}

const fieldLabels = {
  max_age_years: 'Maximum age',
  max_annual_family_income_inr: 'Annual family income ceiling',
  min_marks_percent: 'Minimum marks',
  eligible_communities: 'Eligible communities',
  excluded_communities: 'Excluded communities',
  university_rank_max: 'University ranking limit',
  eligible_degree_levels: 'Eligible degree levels',
  eligible_disciplines: 'Eligible disciplines',
  requires_full_time: 'Full-time requirement',
  other_fellowship_prohibited: 'Other fellowship restriction',
  one_child_per_family: 'One child per family',
  scholarship_one_time: 'One-time scholarship limit',
  monthly_fellowship_inr: 'Monthly fellowship',
  max_fellowship_years: 'Maximum fellowship duration',
  beneficiary_limit: 'Beneficiary limit',
  application_deadline: 'Application deadline',
  required_documents: 'Required documents',
  other: 'Other condition',
};

function prettyValue(value, unit) {
  if (value === null || value === undefined || value === '') return '—';
  const rendered = Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : String(value);
  if (!unit) return rendered;
  const normalizedValue = rendered.toLocaleLowerCase().replace(/[.\s]+$/g, '');
  const normalizedUnit = String(unit).toLocaleLowerCase().trim();
  return normalizedValue.endsWith(normalizedUnit) ? rendered : `${rendered} ${unit}`;
}

function outcomeLabel(outcome, t) {
  return ({
    meets_extracted_conditions: t.meets,
    fails_extracted_conditions: t.fails,
    insufficient_evidence: t.insufficient,
    not_evaluated: t.notEvaluated,
  })[outcome] || t.insufficient;
}

function StatusIcon({ outcome }) {
  if (outcome === 'meets_extracted_conditions') return <CheckCircle2 size={18} />;
  if (outcome === 'fails_extracted_conditions') return <XCircle size={18} />;
  return <CircleAlert size={18} />;
}

function FilePicker({ label, hint, file, onFile, t }) {
  return (
    <label className={`file-picker ${file ? 'has-file' : ''}`}>
      <div className="file-picker-icon">{file ? <FileText size={21} /> : <UploadCloud size={21} />}</div>
      <div className="file-picker-copy">
        <strong>{label}</strong>
        <span>{file ? file.name : hint}</span>
      </div>
      <span className="file-picker-action">{file ? <Check size={16} /> : t.choose}</span>
      <input key={file ? `${file.name}-${file.lastModified}` : 'empty'} type="file" accept="application/pdf,.pdf" onChange={(event) => onFile(event.target.files?.[0] || null)} />
    </label>
  );
}

function ProfileField({ label, value, onChange, type = 'text', placeholder = '', options, selectLabel = 'Select' }) {
  if (options) {
    return (
      <label className="field">
        <span>{label}</span>
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">{selectLabel}</option>
          {options.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}
        </select>
      </label>
    );
  }
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} min={type === 'number' ? 0 : undefined} />
    </label>
  );
}

function AssessmentCard({ title, assessment, t }) {
  const tone = assessment.outcome === 'meets_extracted_conditions' ? 'positive' : assessment.outcome === 'fails_extracted_conditions' ? 'negative' : 'caution';
  return (
    <section className={`assessment-card ${tone}`}>
      <div className="assessment-top"><span>{title}</span><StatusIcon outcome={assessment.outcome} /></div>
      <strong>{outcomeLabel(assessment.outcome, t)}</strong>
      <div className="assessment-counts">
        <span><b>{assessment.passed.length}</b> {t.passed}</span>
        <span><b>{assessment.failed.length}</b> {t.failed}</span>
        <span><b>{assessment.unknown.length}</b> {t.unknown}</span>
      </div>
      {[...assessment.failed, ...assessment.unknown].slice(0, 3).map((line, i) => <p className="assessment-note" key={i}>{line}</p>)}
    </section>
  );
}

function RuleEvidence({ rules, title, t, language }) {
  return (
    <section className="rules-panel">
      <div className="section-head"><div><span className="eyebrow small">{title}</span><h3>{rules.length} {t.conditions}</h3></div></div>
      {rules.length === 0 && <p className="muted">{t.noRules}</p>}
      {rules.map((item, index) => (
        <article className={`rule-row ${item.evidence.verified ? '' : 'rule-unverified'}`} key={`${item.rule.field}-${index}`}>
          <div className="rule-title-line">
            <strong>{fieldLabel(item.rule.field, language)}</strong>
            <span className={`evidence-pill ${item.evidence.verified ? 'verified' : 'unverified'}`}>{item.evidence.verified ? <Check size={12} /> : <CircleAlert size={12} />}{item.evidence.verified ? t.verified : t.rejected}</span>
          </div>
          <div className="rule-value">{prettyValue(item.rule.value, item.rule.unit)}</div>
          <blockquote>{item.rule.quote}</blockquote>
          <div className="quote-foot"><span>{t.page} {item.rule.page}</span><span>{item.rule.status}</span></div>
          {(language === 'ml' ? item.rule.explanation_ml : item.rule.explanation_en) && <p className="rule-explanation">{language === 'ml' ? item.rule.explanation_ml : item.rule.explanation_en}</p>}
          {!item.evidence.verified && <p className="error-text">{item.evidence.reason}</p>}
        </article>
      ))}
    </section>
  );
}

export default function App() {
  const [language, setLanguage] = useState('en');
  const t = copy[language];
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [profileOpen, setProfileOpen] = useState(true);
  const [profile, setProfile] = useState({
    age_years: '', annual_family_income_inr: '', marks_percent: '', community: '', university_rank: '',
    degree_level: '', discipline: '', full_time_research: '', currently_receives_other_fellowship: '',
    is_only_applicant_child_from_family: '', previously_received_same_scheme: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);

  const canSubmit = Boolean(oldFile && newFile && !loading);
  const filledProfile = useMemo(() => Object.values(profile).some((value) => value !== ''), [profile]);

  function updateProfile(key, value) {
    setProfile((current) => ({ ...current, [key]: value }));
  }

  async function analyze(event) {
    event.preventDefault();
    if (!oldFile || !newFile) return;
    setLoading(true);
    setError('');
    setReport(null);
    try {
      const form = new FormData();
      form.append('old_document', oldFile);
      form.append('new_document', newFile);
      if (filledProfile) {
        const cleaned = {};
        for (const [key, value] of Object.entries(profile)) {
          if (value === '') continue;
          if (['full_time_research', 'currently_receives_other_fellowship', 'is_only_applicant_child_from_family', 'previously_received_same_scheme'].includes(key)) cleaned[key] = value === 'true';
          else if (['community', 'degree_level', 'discipline'].includes(key)) cleaned[key] = value;
          else cleaned[key] = Number(value);
        }
        form.append('applicant_profile', JSON.stringify(cleaned));
      }
      const response = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not analyze these documents.');
      setReport(data);
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setReport(null);
    setError('');
    setOldFile(null);
    setNewFile(null);
  }

  const changeLabel = (type) => ({
    modified: t.modified,
    unchanged: t.unchanged,
    not_restated_in_new_document: t.notRestated,
    not_found_in_old_document: t.notFound,
    unchanged_by_limited_amendment: t.unchangedByScope,
    needs_review: t.review,
  })[type] || t.insufficient;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top"><span className="brand-mark">S</span><span>Scheme<span>Shift</span></span></a>
        <div className="topbar-right">
          <span className="beta-label"><span /> Evidence-first policy intelligence</span>
          <button className="language-toggle" onClick={() => setLanguage(language === 'en' ? 'ml' : 'en')}><Globe2 size={15} /> {language === 'en' ? 'മലയാളം' : 'English'}</button>
        </div>
      </header>

      <main id="top" className="main-content">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" />{t.eyebrow}</div>
            <h1>{t.titleA}<br /><em>{t.titleB}</em></h1>
            <p>{t.intro}</p>
            <div className="hero-proof"><span><ShieldCheck size={15} /> Quote-verified rules</span><span><Sparkles size={15} /> AI extraction + deterministic checks</span></div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="orbit orbit-one" /><div className="orbit orbit-two" />
            <div className="paper paper-back"><div /><div /><div /></div>
            <div className="paper paper-front"><div className="paper-kicker">GOVERNMENT ORDER</div><div className="paper-rule long" /><div className="paper-rule" /><div className="paper-rule short" /><div className="paper-highlight">₹ 6,00,000</div><div className="paper-rule long" /><div className="paper-rule short" /><div className="paper-stamp">VERIFIED</div></div>
            <div className="diff-chip"><span>OLD</span><ArrowRight size={14} /><span>NEW</span></div>
          </div>
        </section>

        <section className="workspace">
          <div className="workspace-heading"><div><span className="eyebrow small">01 / DOCUMENTS</span><h2>{t.workspaceTitle}</h2><p>{t.workspaceSub}</p></div><div className="secure-note"><ShieldCheck size={16} /><span>{t.filesNotStored}</span></div></div>
          <form onSubmit={analyze}>
            <div className="upload-grid">
              <FilePicker label={t.old} hint={t.uploadHint} file={oldFile} onFile={setOldFile} t={t} />
              <FilePicker label={t.newer} hint={t.uploadHint} file={newFile} onFile={setNewFile} t={t} />
            </div>

            <div className="profile-accordion">
              <button type="button" className="accordion-head" onClick={() => setProfileOpen(!profileOpen)}>
                <div><span className="eyebrow small">02 / IMPACT CHECK</span><strong>{t.profile}</strong><small>{t.profileHint}</small></div>
                <ChevronDown size={18} className={profileOpen ? 'rotate' : ''} />
              </button>
              {profileOpen && <div className="profile-grid">
                <ProfileField label={t.age} type="number" value={profile.age_years} onChange={(v) => updateProfile('age_years', v)} />
                <ProfileField label={t.income} type="number" value={profile.annual_family_income_inr} onChange={(v) => updateProfile('annual_family_income_inr', v)} />
                <ProfileField label={t.marks} type="number" value={profile.marks_percent} onChange={(v) => updateProfile('marks_percent', v)} />
                <ProfileField label={t.community} value={profile.community} onChange={(v) => updateProfile('community', v)} placeholder="e.g. OBC / OEC" />
                <ProfileField label={t.rank} type="number" value={profile.university_rank} onChange={(v) => updateProfile('university_rank', v)} />
                <ProfileField label={t.degree} value={profile.degree_level} onChange={(v) => updateProfile('degree_level', v)} placeholder="e.g. PG / PhD" />
                <ProfileField label={t.discipline} value={profile.discipline} onChange={(v) => updateProfile('discipline', v)} placeholder="e.g. Computer Science" />
                <ProfileField label={t.fullTime} value={profile.full_time_research} onChange={(v) => updateProfile('full_time_research', v)} options={[{ value: 'true', label: t.yes }, { value: 'false', label: t.no }]} selectLabel={t.select} />
                <ProfileField label={t.otherFellowship} value={profile.currently_receives_other_fellowship} onChange={(v) => updateProfile('currently_receives_other_fellowship', v)} options={[{ value: 'true', label: t.yes }, { value: 'false', label: t.no }]} selectLabel={t.select} />
                <ProfileField label={t.onlyChild} value={profile.is_only_applicant_child_from_family} onChange={(v) => updateProfile('is_only_applicant_child_from_family', v)} options={[{ value: 'true', label: t.yes }, { value: 'false', label: t.no }]} selectLabel={t.select} />
                <ProfileField label={t.previous} value={profile.previously_received_same_scheme} onChange={(v) => updateProfile('previously_received_same_scheme', v)} options={[{ value: 'true', label: t.yes }, { value: 'false', label: t.no }]} selectLabel={t.select} />
              </div>}
            </div>

            <div className="form-footer">
              <div className="privacy-inline"><Info size={15} /><span>{t.profileLocal}</span></div>
              <button className="primary-button" type="submit" disabled={!canSubmit}>{loading ? <><LoaderCircle className="spin" size={17} />{t.analyzing}</> : <>{t.analyze}<ArrowUpRight size={17} /></>}</button>
            </div>
          </form>
          {error && <div className="error-banner"><CircleAlert size={17} /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss"><XCircle size={16} /></button></div>}
        </section>

        {report ? <section className="report-section">
          <div className="report-title-row"><div><span className="eyebrow small">03 / ANALYSIS</span><h2>{t.results}</h2></div><button className="quiet-button" onClick={reset}>{t.reset}</button></div>
          <div className="document-summary-grid">
            {[report.old_document, report.new_document].map((doc, i) => <div className="summary-card" key={i}><div className="summary-icon"><FileText size={18} /></div><div><span>{i === 0 ? t.oldRules : t.newRules}</span><strong>{doc.order_number || doc.title || (i === 0 ? t.old : t.newer)}</strong><small>{doc.order_date || t.dateMissing} · {doc.verified_rule_count} / {doc.extracted_rule_count} {t.verified}</small><small className="source-hash" title={doc.source_sha256}>{doc.source_filename} · SHA-256 {doc.source_sha256.slice(0, 12)}… · {doc.processed_page_count}/{doc.page_count} pages</small></div></div>)}
          </div>
          <div className="assessment-grid"><AssessmentCard title={t.oldOutcome} assessment={report.old_assessment} t={t} /><AssessmentCard title={t.newOutcome} assessment={report.new_assessment} t={t} /></div>

          {report.amendment_scope?.effect === 'specific_changes_only' && <div className={`scope-proof ${report.amendment_scope.verified ? 'verified' : 'caution'}`}>
            <div className="scope-proof-title"><ShieldCheck size={17} /><strong>{report.amendment_scope.verified ? t.scopeVerified : t.scopeUnverified}</strong></div>
            {report.amendment_scope.scope_quote && <blockquote>{report.amendment_scope.scope_quote}<small>{t.page} {report.amendment_scope.scope_page || '—'}</small></blockquote>}
            <p>{report.amendment_scope.reason}</p>
          </div>}

          {report.amendment_pairs?.length > 0 && <section className="amendment-pairs-panel">
            <div className="section-head"><div><span className="eyebrow small">VERIFIED AMENDMENT LINKS</span><h3>{t.amendmentsTitle}</h3></div><span className="count-chip">{report.amendment_pairs.filter((pair) => pair.verified).length} / {report.amendment_pairs.length} verified</span></div>
            {report.amendment_pairs.map((pair, index) => <article className={`amendment-pair ${pair.verified ? 'verified' : 'unverified'}`} key={`${pair.target}-${index}`}>
              <div className="change-row-head"><strong>{pair.target || t.target}</strong><span className={`change-badge ${pair.verified ? 'unchanged' : 'needs_review'}`}>{pair.verified ? t.correctionVerified : t.correctionUnverified}</span></div>
              <div className="amendment-values"><div><small>{t.from}</small><strong>₹{prettyValue(pair.old_value, pair.old_unit)}</strong></div><ArrowRight size={18} /><div><small>{t.to}</small><strong>₹{prettyValue(pair.new_value, pair.new_unit)}</strong></div></div>
              <p>{pair.reason}</p>
              {pair.old_document_quote && <blockquote><small>{t.oldRules} · {t.source} · {t.page} {pair.old_document_page}</small>{pair.old_document_quote}</blockquote>}
              <blockquote><small>{t.newRules} · {t.source} · {t.page} {pair.page}</small>{pair.quote}</blockquote>
            </article>)}
          </section>}

          <div className="changes-panel">
            <div className="section-head"><div><span className="eyebrow small">04 / RULE DIFF</span><h3>{t.changes}</h3></div><span className="count-chip">{report.changes.length} {t.items}</span></div>
            {report.changes.map((change, index) => <article className="change-row" key={index}>
              <div className="change-row-head"><strong>{fieldLabel(change.field, language)}</strong><span className={`change-badge ${change.change_type}`}>{changeLabel(change.change_type)}</span></div>
              <div className="value-comparison"><div><small>{t.oldValue}</small><strong>{prettyValue(change.old_value, change.old_unit)}</strong></div><ArrowRight size={17} /><div><small>{t.newValue}</small><strong>{prettyValue(change.new_value, change.new_unit)}</strong></div></div>
              <p>{language === 'ml' ? (change.explanation_ml || change.explanation) : change.explanation}</p>
              <div className="quote-pair">{change.old_quote && <blockquote><small>{t.oldRules} · {t.source}{change.old_pages?.length ? ` · ${t.page} ${change.old_pages.join(', ')}` : ''}</small>{change.old_quote}</blockquote>}{change.new_quote && <blockquote><small>{t.newRules} · {t.source}{change.new_pages?.length ? ` · ${t.page} ${change.new_pages.join(', ')}` : ''}</small>{change.new_quote}</blockquote>}</div>
            </article>)}
            {report.changes.length === 0 && <p className="muted">No verified comparable conditions were found.</p>}
          </div>

          <div className="evidence-grid"><RuleEvidence rules={report.old_rules} title={t.oldRules} t={t} language={language} /><RuleEvidence rules={report.new_rules} title={t.newRules} t={t} language={language} /></div>

          <section className="warnings-panel"><div className="section-head"><div><span className="eyebrow small">05 / {t.readMore}</span><h3>{t.warnings}</h3></div><Info size={18} /></div><ul>{report.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></section>
        </section> : <section className="empty-state"><div className="empty-icon"><FileUp size={22} /></div><strong>{t.empty}</strong><span>{t.demoLine}</span></section>}

        <section className="trust-strip"><div><ShieldCheck size={19} /><div><strong>Evidence before explanation</strong><span>Unverified model output is excluded from the change comparison.</span></div></div><div><Info size={19} /><div><strong>Human-readable uncertainty</strong><span>Missing parent orders and unobserved conditions are never silently guessed.</span></div></div></section>
      </main>

      <footer className="footer"><div className="brand"><span className="brand-mark">S</span><span>Scheme<span>Shift</span></span></div><p>{t.disclaimer}</p><small>{t.privacy}</small><div className="footer-bottom"><span>Independent prototype · Kerala, India</span><span>Built for transparent policy understanding</span></div></footer>
    </div>
  );
}
