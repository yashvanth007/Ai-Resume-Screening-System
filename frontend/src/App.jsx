import { useDeferredValue, useEffect, useEffectEvent, useRef, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Activity, ArrowDownUp, ArrowLeft, ArrowRight, BarChart3, BriefcaseBusiness, Building2, Check, CheckCheck, ChevronRight, CircleHelp, CloudUpload, FileCheck2, FileSearch, Filter, FolderKanban, Gauge, GitCompareArrows, GraduationCap, LayoutDashboard, LoaderCircle, LogOut, MapPin, MoreHorizontal, Plus, Search, Settings2, ShieldCheck, SlidersHorizontal, Sparkles, Upload, Users, X, } from 'lucide-react'
import './App.css'
import './design.css'
import './profile.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const NAVIGATION = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'jobs', label: 'Job openings', icon: BriefcaseBusiness },
  { id: 'candidates', label: 'Candidates', icon: Users },
  { id: 'analytics', label: 'Insights', icon: BarChart3 },
]
const STATUS_OPTIONS = ['New', 'Reviewed', 'Shortlisted', 'Interview', 'Rejected', 'Hired']
const PIE_COLORS = ['#337969', '#d67c59', '#dfbc62', '#6697a0', '#aabbb1']

async function api(path, options = {}) {
  const token = localStorage.getItem('screening-token')
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData) && options.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API}${path}`, { ...options, headers })
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || 'Something went wrong. Please try again.')
  return data
}

function money(value) {
  return value == null ? 'Not specified' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function scoreTone(score = 0) {
  if (score >= 80) return 'strong'
  if (score >= 60) return 'moderate'
  return 'low'
}

function Avatar({ name = 'Candidate', size = '' }) {
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
  return <span className={`avatar ${size}`}>{initials || 'C'}</span>
}

function Score({ value = 0, small = false }) {
  return <span className={`score ${scoreTone(value)} ${small ? 'score-small' : ''}`}><span>{Math.round(value)}</span><small>%</small></span>
}

function Toast({ toast, close }) {
  if (!toast) return null
  return <div className={`toast ${toast.type || 'success'}`} role="status"><span>{toast.message}</span><button className="icon-button ghost" onClick={close} aria-label="Dismiss notification"><X size={15} /></button></div>
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await api(`/api/auth/${mode === 'login' ? 'login' : 'register'}`, { method: 'POST', body: JSON.stringify(form) })
      localStorage.setItem('screening-token', result.access_token)
      onAuthenticated(result.user)
    } catch (cause) {
      setError(cause.message)
    } finally {
      setBusy(false)
    }
  }

  return <main className="auth-page">
    <section className="auth-story">
      <div className="auth-brand"><span className="brand-symbol"><Activity size={19} /></span> shortlist<span className="brand-dot">.</span></div>
      <div className="story-copy"><div className="eyebrow"><span className="eyebrow-line" /> PEOPLE, NOT JUST PROFILES</div><h1>Find the signal<br />in every story.</h1><p>Thoughtful resume intelligence for hiring teams who look beyond the keywords.</p><div className="story-stats"><div><strong>Evidence-led</strong><span>Transparent match factors</span></div><div><strong>People-first</strong><span>Human decisions, always</span></div></div></div>
      <div className="story-foot"><ShieldCheck size={15} /> Designed for responsible hiring</div>
    </section>
    <section className="auth-form-wrap">
      <div className="auth-form-inner"><div className="mobile-brand"><span className="brand-symbol"><Activity size={19} /></span> shortlist<span className="brand-dot">.</span></div><span className="auth-kicker">RECRUITER WORKSPACE</span><h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2><p className="auth-subtitle">{mode === 'login' ? 'Sign in to continue to your hiring workspace.' : 'Set up your private recruiter workspace.'}</p>
        <form onSubmit={submit} className="auth-form">
          {mode === 'register' && <label>Full name<input required minLength="2" autoComplete="name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} placeholder="Alex Morgan" /></label>}
          <label>Work email<input required type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="you@company.com" /></label>
          <label>Password<input required minLength="8" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="At least 8 characters" /></label>
          {error && <div className="form-error">{error}</div>}
          <button className="button primary full" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : null}{mode === 'login' ? 'Sign in' : 'Create account'}<ArrowRight size={16} /></button>
        </form>
        <p className="auth-toggle">{mode === 'login' ? 'New to Shortlist?' : 'Already have an account?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p>
        <div className="auth-privacy"><ShieldCheck size={15} /> Your candidate data stays within your workspace.</div>
      </div>
    </section>
  </main>
}

function JobDialog({ close, save, busy }) {
  const [form, setForm] = useState({ title: '', company: '', location: '', employment_type: 'Full-time', experience_required: '0', salary_min: '', salary_max: '', description: '', required_skills: '', preferred_skills: '', education_requirement: '' })
  const change = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))
  function submit(event) {
    event.preventDefault()
    save({ ...form, experience_required: Number(form.experience_required), salary_min: form.salary_min ? Number(form.salary_min) : null, salary_max: form.salary_max ? Number(form.salary_max) : null, required_skills: form.required_skills.split(',').map((item) => item.trim()).filter(Boolean), preferred_skills: form.preferred_skills.split(',').map((item) => item.trim()).filter(Boolean) })
  }
  return <Modal close={close} title="Create a job opening" subtitle="Add the role details and the system will identify skills from the description."><form className="job-form" onSubmit={submit}>
    <div className="form-grid"><label>Job title<input required value={form.title} onChange={change('title')} placeholder="Senior ML Engineer" /></label><label>Company<input required value={form.company} onChange={change('company')} placeholder="Company name" /></label><label>Location<input value={form.location} onChange={change('location')} placeholder="City or remote" /></label><label>Employment type<select value={form.employment_type} onChange={change('employment_type')}><option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option></select></label><label>Experience required <span className="label-note">years</span><input type="number" min="0" max="60" step="0.5" value={form.experience_required} onChange={change('experience_required')} /></label><label>Salary range <span className="label-note">annual USD</span><span className="salary-fields"><input type="number" min="0" value={form.salary_min} onChange={change('salary_min')} placeholder="Min" /><input type="number" min="0" value={form.salary_max} onChange={change('salary_max')} placeholder="Max" /></span></label></div>
    <label>Job description<textarea required minLength="30" rows="5" value={form.description} onChange={change('description')} placeholder="Describe the work, responsibilities, and qualifications..." /></label>
    <div className="form-grid"><label>Required skills <span className="label-note">comma separated; auto-detected if empty</span><input value={form.required_skills} onChange={change('required_skills')} placeholder="Python, FastAPI, SQL" /></label><label>Preferred skills <span className="label-note">comma separated</span><input value={form.preferred_skills} onChange={change('preferred_skills')} placeholder="Docker, AWS" /></label><label>Education requirement <span className="label-note">optional, used as a match factor</span><input value={form.education_requirement} onChange={change('education_requirement')} placeholder="Bachelor's in Computer Science" /></label></div>
    <div className="modal-actions"><button type="button" className="button subtle" onClick={close}>Cancel</button><button className="button primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />} Create opening</button></div>
  </form></Modal>
}

function Modal({ close, title, subtitle, children, wide = false }) {
  useEffect(() => { const listener = (event) => { if (event.key === 'Escape') close() }; window.addEventListener('keydown', listener); return () => window.removeEventListener('keydown', listener) }, [close])
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close() }}><section className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><header className="modal-heading"><div><span className="auth-kicker">SHORTLIST WORKSPACE</span><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-button" onClick={close} aria-label="Close dialog"><X size={17} /></button></header>{children}</section></div>
}

function EmptyState({ icon: Icon = FolderKanban, title, body, action, onAction }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={22} /></span><h3>{title}</h3><p>{body}</p>{action && <button className="button primary" onClick={onAction}><Plus size={16} />{action}</button>}</div>
}

function CandidateTable({ candidates, onOpen, selected = [], onToggle, compareMode = false, loading = false }) {
  if (loading) return <div className="table-loading"><LoaderCircle className="spin" size={20} /> Loading candidate records...</div>
  if (!candidates.length) return <EmptyState icon={FileSearch} title="No candidates found" body="Upload resumes for this opening, or adjust your search and filters." />
  return <div className="table-scroll"><table className="candidate-table"><thead><tr><th>{compareMode && 'Select'}</th><th>Candidate</th><th>Fit score</th><th>Skills</th><th>Experience</th><th>Status</th><th aria-label="Actions" /></tr></thead><tbody>{candidates.map((candidate, index) => { const score = candidate.match?.overall_score || 0; return <tr key={candidate.application_id || candidate.id} aria-rowindex={index + 1} onClick={() => onOpen(candidate)} className="candidate-row"><td onClick={(event) => event.stopPropagation()}>{compareMode && <input className="row-check" type="checkbox" aria-label={`Select ${candidate.name} for comparison`} checked={selected.includes(candidate.application_id || candidate.id)} onChange={() => onToggle(candidate)} />}</td><td><div className="person-cell"><Avatar name={candidate.name} /><span><strong>{candidate.name}</strong><small>{candidate.email || candidate.location || 'Contact not detected'}</small></span></div></td><td><div className="score-cell"><Score value={score} small /><div className="score-track"><span className={scoreTone(score)} style={{ width: `${score}%` }} /></div></div></td><td><div className="skill-pills">{(candidate.match?.matched_skills || candidate.skills?.map((skill) => skill.name) || []).slice(0, 3).map((skill) => <span key={skill} className="skill-pill">{skill}</span>)}{(candidate.match?.matched_skills || candidate.skills || []).length > 3 && <span className="skill-more">+{(candidate.match?.matched_skills || candidate.skills).length - 3}</span>}</div></td><td>{candidate.experience_years ? `${candidate.experience_years} yrs` : 'Not detected'}</td><td><span className={`status-pill status-${(candidate.status || 'new').toLowerCase()}`}>{candidate.status || 'New'}</span></td><td><button className="icon-button ghost row-action" title="View candidate" onClick={(event) => { event.stopPropagation(); onOpen(candidate) }}><ChevronRight size={16} /></button></td></tr> })}</tbody></table></div>
}

function CandidateDialog({ candidate, close, reload, notify }) {
  const [detail, setDetail] = useState(candidate)
  const [generated, setGenerated] = useState(null)
  const [questions, setQuestions] = useState(null)
  const [busy, setBusy] = useState('')
  const activeApplication = detail.applications?.[0] || { application_id: detail.application_id, job_id: detail.job_id, match: detail.match, status: detail.status }
  const match = activeApplication?.match || detail.match || {}
  const [status, setStatus] = useState(activeApplication?.status || detail.status || 'New')
  const [notes, setNotes] = useState(activeApplication?.notes || [])
  const [noteDraft, setNoteDraft] = useState('')
  const [resumeText, setResumeText] = useState('')

  async function updateStatus(value) {
    setStatus(value)
    try {
      const updated = await api(`/api/candidates/${detail.id}`, { method: 'PUT', body: JSON.stringify({ status: value, application_id: activeApplication?.application_id }) })
      setDetail(updated)
      notify(`Status updated to ${value}.`)
      reload()
    } catch (error) { notify(error.message, 'error') }
  }

  async function generate(kind) {
    setBusy(kind)
    try {
      const result = await api(`/api/candidates/${detail.id}/applications/${activeApplication.application_id}/${kind === 'summary' ? 'summary' : 'interview-questions'}`, { method: 'POST' })
      if (kind === 'summary') setGenerated(result)
      else setQuestions(result)
    } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  async function addNote(event) {
    event.preventDefault()
    if (!noteDraft.trim() || !activeApplication?.application_id) return
    setBusy('note')
    try {
      const note = await api(`/api/candidates/${detail.id}/applications/${activeApplication.application_id}/notes`, { method: 'POST', body: JSON.stringify({ body: noteDraft.trim() }) })
      setNotes((previous) => [note, ...previous])
      setNoteDraft('')
      notify('Recruiter note added.')
    } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  async function showResume() {
    const resumeId = detail.resumes?.[0]?.id
    if (!resumeId) { notify('No uploaded resume is available to preview.', 'error'); return }
    setBusy('resume')
    try { const resume = await api(`/api/resumes/${resumeId}`); setResumeText(resume.extracted_text) } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  return <Modal close={close} title="Candidate profile" subtitle="Review extracted information and the evidence behind this job match." wide><div className="candidate-profile"><div className="profile-main"><div className="profile-identity"><Avatar name={detail.name} size="avatar-large" /><div><h3>{detail.name}</h3><p>{detail.email || 'Email not detected'}{detail.location ? ` · ${detail.location}` : ''}</p></div><select className="status-select" aria-label="Application status" value={status} onChange={(event) => updateStatus(event.target.value)}>{STATUS_OPTIONS.map((item) => <option key={item}>{item}</option>)}</select></div>
    <section className="profile-section"><div className="profile-section-title"><h4>Extracted skills</h4><span>{detail.skills?.length || 0} detected</span></div><div className="profile-skills">{detail.skills?.length ? detail.skills.map((skill) => <span key={skill.name} className="skill-pill">{skill.name}<small>{skill.category}</small></span>) : <p className="muted">No skills detected in the uploaded resume.</p>}</div></section>
    <section className="profile-section"><div className="profile-section-title"><h4>Experience</h4><span>{detail.experience_years || 0} years stated</span></div>{detail.experiences?.length ? detail.experiences.map((item, index) => <div className="timeline-item" key={index}><strong>{item.title || 'Experience'}</strong><span>{item.company || 'Organization not detected'}</span><p>{item.description}</p></div>) : <p className="muted">Detailed work history was not clearly sectioned in this resume.</p>}</section>
    <section className="profile-section"><div className="profile-section-title"><h4>Education & projects</h4></div><div className="profile-columns"><div>{detail.education?.length ? detail.education.map((item, index) => <div className="detail-line" key={index}><GraduationCap size={15} /><span><strong>{item.degree || 'Degree not detected'}</strong><small>{item.institution || 'Institution not detected'}{item.graduation_year ? ` · ${item.graduation_year}` : ''}</small></span></div>) : <p className="muted">Education not detected.</p>}</div><div>{detail.projects?.length ? detail.projects.map((item, index) => <div className="detail-line" key={index}><FolderKanban size={15} /><span><strong>{item.name || 'Project'}</strong><small>{item.description}</small></span></div>) : <p className="muted">Projects not detected.</p>}</div></div></section>
    <section className="profile-section notes-section"><div className="profile-section-title"><h4>Recruiter notes</h4><span>{notes.length} notes</span></div><form className="note-form" onSubmit={addNote}><textarea value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} maxLength={5000} rows={2} placeholder="Add an evidence-based note for your team..." /><button className="button secondary" disabled={!noteDraft.trim() || busy === 'note'}>{busy === 'note' ? <LoaderCircle className="spin" size={14} /> : <Plus size={14} />} Add note</button></form>{notes.map((note) => <div className="recruiter-note" key={note.id}><p>{note.body}</p><time>{new Date(note.created_at).toLocaleString()}</time></div>)}</section>
    {resumeText && <section className="generated-panel resume-preview"><div className="profile-section-title"><h4><FileSearch size={14} /> Extracted resume text</h4><span>Parsed source content</span></div><pre>{resumeText}</pre></section>}
    {generated && <section className="generated-panel"><div className="profile-section-title"><h4><Sparkles size={15} /> Candidate summary</h4><span>{generated.source}</span></div><p>{generated.summary}</p><div className="generated-columns"><div><strong>Strengths</strong><span>{generated.strengths?.join(', ') || 'None detected'}</span></div><div><strong>Interview focus</strong><span>{generated.interview_focus?.join(', ') || 'Explore relevant work in detail'}</span></div></div></section>}
    {questions && <section className="generated-panel"><div className="profile-section-title"><h4><CircleHelp size={15} /> Interview prompts</h4><span>Generated, not factual claims</span></div>{[['Technical', questions.technical], ['Project', questions.project], ['Behavioral', questions.behavioral]].map(([heading, items]) => <div className="question-group" key={heading}><strong>{heading}</strong><ol>{items.map((item, index) => <li key={`${heading}-${index}`}>{item}</li>)}</ol></div>)}</section>}</div>
    <aside className="profile-aside"><div className="match-card"><div className="match-score-header"><span>OVERALL MATCH</span><Score value={match.overall_score || 0} /></div><div className="match-components">{[['Skills', 'skill_score'], ['Description', 'semantic_score'], ['Experience', 'experience_score'], ['Education', 'education_score'], ['Projects', 'project_score'], ['Certifications', 'certification_score']].map(([label, key]) => <div className="component-row" key={key}><span>{label}</span><strong>{Math.round(match[key] || 0)}%</strong></div>)}</div><p className="weights-note">35% skills · 25% description · 15% experience · 10% education · 10% projects · 5% certifications</p></div>
      <div className="profile-section compact-profile"><h4><CheckCheck size={15} /> Matched skills</h4><div className="profile-skills">{match.matched_skills?.length ? match.matched_skills.map((item) => <span className="skill-pill matched" key={item}>{item}</span>) : <span className="muted">No direct matches detected.</span>}</div></div><div className="profile-section compact-profile"><h4><X size={15} /> Missing required</h4><div className="profile-skills">{match.missing_skills?.length ? match.missing_skills.map((item) => <span className="skill-pill missing" key={item}>{item}</span>) : <span className="muted">No required skills missing.</span>}</div></div>
      <div className="profile-actions"><button className="button secondary full" onClick={() => generate('summary')} disabled={busy === 'summary'}>{busy === 'summary' ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />} Generate candidate summary</button><button className="button subtle full" onClick={() => generate('questions')} disabled={busy === 'questions'}>{busy === 'questions' ? <LoaderCircle className="spin" size={15} /> : <CircleHelp size={15} />} Generate interview questions</button><button className="button subtle full" onClick={showResume} disabled={busy === 'resume'}>{busy === 'resume' ? <LoaderCircle className="spin" size={15} /> : <FileSearch size={15} />} View extracted resume</button></div>
    </aside></div><div className="fairness-note"><ShieldCheck size={15} /><span>Decision-support only. Review the evidence and make hiring decisions with qualified human judgment.</span></div></Modal>
}

function CompareDialog({ candidates, close }) {
  return <Modal close={close} title="Candidate comparison" subtitle="Compare transparent match signals side by side." wide><div className="compare-table-scroll"><table className="compare-table"><thead><tr><th>Signal</th>{candidates.map((candidate) => <th key={candidate.application_id || candidate.id}><div className="person-cell"><Avatar name={candidate.name} /><strong>{candidate.name}</strong></div></th>)}</tr></thead><tbody>{[['Overall match', (item) => `${Math.round(item.match?.overall_score || 0)}%`], ['Skill match', (item) => `${Math.round(item.match?.skill_score || 0)}%`], ['Description similarity', (item) => `${Math.round(item.match?.semantic_score || 0)}%`], ['Experience', (item) => `${item.experience_years || 0} years`], ['Education', (item) => item.education?.[0]?.degree || 'Not detected'], ['Projects', (item) => `${item.projects?.length || 0} detected`], ['Missing required skills', (item) => item.match?.missing_skills?.join(', ') || 'None detected']].map(([label, value]) => <tr key={label}><th>{label}</th>{candidates.map((candidate) => <td key={candidate.application_id || candidate.id}>{value(candidate)}</td>)}</tr>)}</tbody></table></div></Modal>
}

function App() {
  const [user, setUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(() => !localStorage.getItem('screening-token'))
  const [view, setView] = useState('dashboard')
  const [jobs, setJobs] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [candidateTotal, setCandidateTotal] = useState(0)
  const [activeJob, setActiveJob] = useState(null)
  const [activeCandidate, setActiveCandidate] = useState(null)
  const [showJobDialog, setShowJobDialog] = useState(false)
  const [compareCandidates, setCompareCandidates] = useState([])
  const [compareMode, setCompareMode] = useState(false)
  const [filters, setFilters] = useState({ search: '', status: '', min_score: '', sort_by: 'score', skill: '' })
  const deferredSearch = useDeferredValue(filters.search)
  const [busy, setBusy] = useState('')
  const [pageLoading, setPageLoading] = useState(false)
  const [toast, setToast] = useState(null)
  const [candidateOffset, setCandidateOffset] = useState(0)

  function notify(message, type = 'success') {
    setToast({ message, type })
    window.clearTimeout(notify.timer)
    notify.timer = window.setTimeout(() => setToast(null), 3600)
  }

  async function loadJobs() {
    const data = await api('/api/jobs')
    setJobs(data)
    return data
  }

  async function loadDashboard() {
    const [stats, jobData] = await Promise.all([api('/api/analytics/dashboard'), api('/api/jobs')])
    setDashboard(stats)
    setJobs(jobData)
  }

  async function loadCandidates() {
    setPageLoading(true)
    try {
      const query = new URLSearchParams({ search: deferredSearch, sort_by: filters.sort_by, offset: String(candidateOffset), limit: '20' })
      if (filters.status) query.set('status', filters.status)
      if (filters.skill) query.set('skill', filters.skill)
      if (filters.min_score) query.set('min_score', filters.min_score)
      if (activeJob?.id) query.set('job_id', String(activeJob.id))
      const data = await api(`/api/candidates?${query}`)
      setCandidates(data.items)
      setCandidateTotal(data.total)
    } catch (error) { notify(error.message, 'error') } finally { setPageLoading(false) }
  }

  const refreshDashboardFromEffect = useEffectEvent(() => loadDashboard().catch((error) => notify(error.message, 'error')))
  const refreshCandidatesFromEffect = useEffectEvent(() => loadCandidates())

  async function loadJob(id) {
    setPageLoading(true)
    try {
      const job = await api(`/api/jobs/${id}`)
      setActiveJob(job)
      setCandidates(job.candidates || [])
      setCandidateTotal((job.candidates || []).length)
      setView('job')
    } catch (error) { notify(error.message, 'error') } finally { setPageLoading(false) }
  }

  useEffect(() => {
    const token = localStorage.getItem('screening-token')
    if (!token) return
    let active = true
    api('/api/auth/me').then((account) => { if (active) setUser(account) }).catch(() => localStorage.removeItem('screening-token')).finally(() => { if (active) setAuthChecked(true) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    const navigate = (event) => { setView(event.detail); setActiveJob(null) }
    window.addEventListener('navigate', navigate)
    return () => window.removeEventListener('navigate', navigate)
  }, [])

  useEffect(() => {
    if (!user || view !== 'dashboard') return
    const task = window.setTimeout(() => refreshDashboardFromEffect(), 0)
    return () => window.clearTimeout(task)
  }, [user, view])
  useEffect(() => {
    if (!user || view !== 'candidates') return
    const task = window.setTimeout(() => refreshCandidatesFromEffect(), 0)
    return () => window.clearTimeout(task)
  }, [user, view, deferredSearch, filters.status, filters.skill, filters.sort_by, filters.min_score, candidateOffset])

  async function createJob(data) {
    setBusy('create-job')
    try {
      const job = await api('/api/jobs', { method: 'POST', body: JSON.stringify(data) })
      setShowJobDialog(false)
      notify('Job opening created. Add resumes to start matching.')
      await loadJobs()
      setActiveJob(job)
      setCandidates([])
      setCandidateTotal(0)
      setView('job')
    } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  async function uploadResumes(files) {
    if (!activeJob || !files.length) return
    setBusy('upload')
    const form = new FormData()
    form.append('job_id', activeJob.id)
    Array.from(files).forEach((file) => form.append('files', file))
    try {
      const result = await api('/api/resumes/upload-multiple', { method: 'POST', body: form })
      notify(`${result.processed} resume${result.processed === 1 ? '' : 's'} processed${result.failed ? `, ${result.failed} could not be read` : ''}.`)
      if (result.errors?.length) setToast({ message: result.errors.map((item) => `${item.filename}: ${item.error}`).join(' · '), type: 'error' })
      await loadJob(activeJob.id)
    } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  async function openCandidate(candidate) {
    try {
      const detail = await api(`/api/candidates/${candidate.id}`)
      if (candidate.application_id && detail.applications) {
        const application = detail.applications.find((item) => item.application_id === candidate.application_id)
        if (application) detail.applications = [application]
      }
      if (candidate.match && !detail.match) detail.match = candidate.match
      if (candidate.application_id) { detail.application_id = candidate.application_id; detail.job_id = candidate.job_id }
      setActiveCandidate(detail)
    } catch (error) { notify(error.message, 'error') }
  }

  async function refreshView() {
    if (activeJob && view === 'job') await loadJob(activeJob.id)
    else if (view === 'dashboard') await loadDashboard()
    else if (view === 'candidates') await loadCandidates()
    else if (view === 'analytics') setDashboard(await api('/api/analytics/dashboard'))
  }

  async function loadDemoData() {
    setBusy('demo')
    try {
      const result = await api('/api/demo/seed', { method: 'POST' })
      if (result.created) notify(`Loaded ${result.candidates} synthetic candidates across ${result.jobs} roles.`)
      else notify(result.message, 'error')
      await loadDashboard()
    } catch (error) { notify(error.message, 'error') } finally { setBusy('') }
  }

  async function deleteJob(job) {
    if (!window.confirm(`Delete ${job.title}? Its applications and match records will also be removed.`)) return
    try { await api(`/api/jobs/${job.id}`, { method: 'DELETE' }); setJobs((previous) => previous.filter((item) => item.id !== job.id)); notify('Job opening deleted.'); if (activeJob?.id === job.id) { setActiveJob(null); setView('jobs') } } catch (error) { notify(error.message, 'error') }
  }

  function toggleCompare(candidate) {
    const id = candidate.application_id || candidate.id
    setCompareCandidates((previous) => previous.some((item) => (item.application_id || item.id) === id) ? previous.filter((item) => (item.application_id || item.id) !== id) : previous.length < 5 ? [...previous, candidate] : (notify('Choose up to five candidates to compare.', 'error'), previous))
  }

  function signOut() { localStorage.removeItem('screening-token'); setUser(null); setJobs([]); setDashboard(null); setActiveJob(null); setView('dashboard') }

  if (!authChecked) return <div className="app-loading"><span className="brand-symbol"><Activity size={19} /></span><LoaderCircle className="spin" size={19} /> Checking your workspace</div>
  if (!user) return <AuthScreen onAuthenticated={(account) => { setUser(account); setView('dashboard') }} />

  const average = dashboard?.average_match_score || 0
  const pageTitle = view === 'job' ? activeJob?.title || 'Job opening' : ({ dashboard: 'Good morning', jobs: 'Job openings', candidates: 'Candidates', analytics: 'Insights', settings: 'Workspace settings' }[view] || 'Overview')

  return <div className="app-layout">
    <aside className="sidebar"><a className="app-brand" href="#overview" onClick={(event) => { event.preventDefault(); setView('dashboard'); setActiveJob(null) }}><span className="brand-symbol"><Activity size={18} /></span><span>shortlist<span className="brand-dot">.</span></span></a><span className="sidebar-label">WORKSPACE</span><nav className="main-nav">{NAVIGATION.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${view === id || (id === 'jobs' && view === 'job') ? 'active' : ''}`} onClick={() => { setView(id); if (id !== 'job') setActiveJob(null); setCandidateOffset(0) }}><Icon size={17} /><span>{label}</span>{id === 'candidates' && candidateTotal > 0 && <small>{candidateTotal}</small>}</button>)}</nav><div className="sidebar-jobs-head"><span className="sidebar-label">RECENT OPENINGS</span><button className="icon-button ghost tiny" title="Create a job" onClick={() => setShowJobDialog(true)}><Plus size={15} /></button></div><div className="sidebar-jobs">{jobs.slice(0, 5).map((job) => <button key={job.id} className={`sidebar-job ${activeJob?.id === job.id ? 'active' : ''}`} onClick={() => loadJob(job.id)}><span className="job-dot" /><span>{job.title}</span><small>{job.candidate_count || 0}</small></button>)}{!jobs.length && <span className="sidebar-empty">Your openings appear here</span>}</div><div className="sidebar-bottom"><div className="fairness-sidebar"><ShieldCheck size={15} /><span>Human decisions.<br />Evidence-led signals.</span></div><button className={`nav-item ${view === 'settings' ? 'active' : ''}`} onClick={() => setView('settings')}><Settings2 size={17} /><span>Settings</span></button><button className="account-row" onClick={signOut} title="Sign out"><Avatar name={user.full_name} /><span><strong>{user.full_name}</strong><small>{user.email}</small></span><LogOut size={15} /></button></div></aside>
    <main className="main-area"><header className="topbar"><div className="mobile-title">shortlist<span className="brand-dot">.</span></div><div className="crumbs"><span>Workspace</span><ChevronRight size={14} /><strong>{activeJob && view === 'job' ? activeJob.title : pageTitle}</strong></div><div className="topbar-right"><span className="workspace-state"><span /> Screening workspace</span><button className="icon-button" title="Settings" aria-label="Workspace settings" onClick={() => setView('settings')}><Settings2 size={17} /></button><button className="top-avatar" title="Sign out" onClick={signOut}><Avatar name={user.full_name} size="avatar-small" /></button></div></header>
      <div className="page-wrap">
        {view === 'dashboard' && <Dashboard stats={dashboard} jobs={jobs} average={average} onNew={() => setShowJobDialog(true)} onOpenJob={loadJob} onOpenCandidates={() => setView('candidates')} onDemo={loadDemoData} demoBusy={busy === 'demo'} />}
        {view === 'jobs' && <JobsPage jobs={jobs} loading={pageLoading} onNew={() => setShowJobDialog(true)} onOpen={loadJob} onDelete={deleteJob} />}
        {view === 'job' && activeJob && <JobPage job={activeJob} candidates={candidates} loading={pageLoading} busy={busy} compareMode={compareMode} selected={compareCandidates.map((item) => item.application_id || item.id)} filters={filters} setFilters={setFilters} onUpload={uploadResumes} onCandidate={openCandidate} onToggleCompare={toggleCompare} onCompare={() => setCompareMode((value) => !value)} onShowCompare={() => setView('job')} onDelete={() => deleteJob(activeJob)} onRefresh={() => loadJob(activeJob.id)} onCompareResults={() => setCompareCandidates(compareCandidates)} compareCount={compareCandidates.length} />}
        {view === 'candidates' && <CandidatesPage candidates={candidates} total={candidateTotal} loading={pageLoading} filters={filters} setFilters={setFilters} offset={candidateOffset} setOffset={setCandidateOffset} onCandidate={openCandidate} />}
        {view === 'analytics' && <AnalyticsPage stats={dashboard} reload={async () => setDashboard(await api('/api/analytics/dashboard'))} />}
        {view === 'settings' && <SettingsPage user={user} onSignOut={signOut} />}
      </div>
    </main>
    <Toast toast={toast} close={() => setToast(null)} />
    {showJobDialog && <JobDialog close={() => setShowJobDialog(false)} save={createJob} busy={busy === 'create-job'} />}
    {activeCandidate && <CandidateDialog candidate={activeCandidate} close={() => setActiveCandidate(null)} reload={refreshView} notify={notify} />}
    {compareMode && <div className="compare-dock"><span><GitCompareArrows size={15} />{compareCandidates.length} of 5 selected</span><button className="button subtle" onClick={() => { setCompareMode(false); setCompareCandidates([]) }}>Cancel</button><button className="button primary" disabled={compareCandidates.length < 2} onClick={() => { if (compareCandidates.length >= 2) setView('compare') }}>Compare <ArrowRight size={14} /></button></div>}
    {view === 'compare' && <CompareDialog candidates={compareCandidates} close={() => { setCompareMode(false); setView(activeJob ? 'job' : 'candidates') }} />}
  </div>
}

function Dashboard({ stats, jobs, average, onNew, onOpenJob, onOpenCandidates, onDemo, demoBusy }) {
  const metrics = [{ label: 'Open positions', value: stats?.total_jobs || 0, note: 'Across your workspace', icon: BriefcaseBusiness, tint: 'sage' }, { label: 'Candidates', value: stats?.total_candidates || 0, note: 'Unique profiles reviewed', icon: Users, tint: 'coral' }, { label: 'Resumes processed', value: stats?.resumes_processed || 0, note: 'PDF and DOCX files', icon: FileCheck2, tint: 'gold' }, { label: 'Average match', value: `${average}%`, note: 'Across scored candidates', icon: Gauge, tint: 'blue' }]
  return <><div className="page-heading"><div><span className="eyebrow dark">HIRING OVERVIEW <span className="eyebrow-line" /></span><h1>Hiring, in focus.</h1><p>A clear view of your open roles and the people behind them.</p></div><button className="button primary" onClick={onNew}><Plus size={16} /> New opening</button></div>
    <section className="metric-grid">{metrics.map(({ label, value, note, icon: Icon, tint }) => <article className="metric-card" key={label}><div className={`metric-icon ${tint}`}><Icon size={18} /></div><span className="metric-label">{label}</span><strong className="metric-value">{value}</strong><span className="metric-note">{note}</span></article>)}</section>
    <section className="dashboard-grid"><article className="panel jobs-panel"><div className="panel-heading"><div><span className="eyebrow dark">YOUR PIPELINE</span><h2>Recent openings</h2></div><button className="text-button" onClick={onOpenCandidates}>View candidates <ArrowRight size={14} /></button></div>{jobs.length ? <div className="recent-job-list">{jobs.slice(0, 5).map((job, index) => <button className="recent-job" key={job.id} onClick={() => onOpenJob(job.id)}><span className={`job-index index-${index % 3}`}>{String(index + 1).padStart(2, '0')}</span><span className="recent-job-main"><strong>{job.title}</strong><small><Building2 size={12} />{job.company} <span>·</span> {job.location}</small></span><span className="recent-job-count"><Users size={14} />{job.candidate_count || 0}</span><span className="recent-job-cta"><ArrowRight size={15} /></span></button>)}</div> : <div className="inline-empty"><span className="empty-icon"><BriefcaseBusiness size={19} /></span><strong>Your first opening starts here</strong><p>Create a role to begin matching resumes against real requirements.</p><div className="empty-actions"><button className="button secondary" onClick={onNew}><Plus size={15} />Create an opening</button><button className="text-button" disabled={demoBusy} onClick={onDemo}>{demoBusy ? <LoaderCircle className="spin" size={14} /> : <Sparkles size={14} />}Try sample workspace</button></div></div>}</article>
      <article className="panel pipeline-panel"><div className="panel-heading"><div><span className="eyebrow dark">CANDIDATE FLOW</span><h2>Review pipeline</h2></div><span className="panel-icon"><Activity size={16} /></span></div>{stats?.total_candidates ? <><div className="pipeline-total"><strong>{stats.total_candidates}</strong><span>candidates<br />in review</span></div><div className="pipeline-bars">{[{ label: 'New', color: 'bar-new' }, { label: 'Reviewed', color: 'bar-reviewed' }, { label: 'Shortlisted', color: 'bar-shortlisted' }, { label: 'Interview', color: 'bar-interview' }, { label: 'Hired', color: 'bar-hired' }].map((item) => { const count = stats.status_distribution?.[item.label] || 0; const pct = Math.max(count > 0 ? 4 : 0, count / stats.total_candidates * 100); return <div className="pipeline-row" key={item.label}><span>{item.label}</span><div className="pipeline-track"><i className={item.color} style={{ width: `${pct}%` }} /></div><strong>{count}</strong></div> })}</div></> : <div className="pipeline-empty"><span className="pipeline-mark"><BarChart3 size={20} /></span><p>Your candidate pipeline will build here once resumes are matched to a role.</p></div>}</article></section>
    <div className="responsibility-banner"><span className="responsibility-icon"><ShieldCheck size={17} /></span><p><strong>People-first screening.</strong> Match scores are decision-support signals based on job-related information only. Qualified recruiters make every hiring decision.</p><span className="responsibility-stamp">RESPONSIBLE AI</span></div>
  </>
}

function JobsPage({ jobs, loading, onNew, onOpen, onDelete }) {
  const [search, setSearch] = useState('')
  const filtered = jobs.filter((job) => `${job.title} ${job.company} ${job.location}`.toLowerCase().includes(search.toLowerCase()))
  return <><div className="page-heading"><div><span className="eyebrow dark">ROLE MANAGEMENT <span className="eyebrow-line" /></span><h1>Job openings</h1><p>Manage the roles and requirements your team is hiring for.</p></div><button className="button primary" onClick={onNew}><Plus size={16} /> New opening</button></div><div className="filter-bar"><label className="search-field"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search openings..." /></label><span className="filter-count">{filtered.length} {filtered.length === 1 ? 'opening' : 'openings'}</span></div>{loading ? <div className="table-loading"><LoaderCircle className="spin" />Loading roles...</div> : filtered.length ? <div className="job-card-grid">{filtered.map((job) => <article className="job-card" key={job.id}><div className="job-card-top"><span className="job-type"><BriefcaseBusiness size={13} />{job.employment_type}</span><button className="icon-button ghost" aria-label={`Delete ${job.title}`} title="Delete opening" onClick={() => onDelete(job)}><MoreHorizontal size={17} /></button></div><button className="job-card-title" onClick={() => onOpen(job.id)}><h2>{job.title}</h2><span><Building2 size={14} />{job.company}</span></button><div className="job-card-meta"><span><MapPin size={13} />{job.location || 'Location not specified'}</span><span><Users size={13} />{job.candidate_count || 0} candidates</span></div><div className="job-card-skills">{(job.required_skills || []).slice(0, 4).map((skill) => <span key={skill}>{skill}</span>)}{job.required_skills?.length > 4 && <span>+{job.required_skills.length - 4}</span>}</div><button className="job-card-footer" onClick={() => onOpen(job.id)}><span>View role & candidates</span><ArrowRight size={15} /></button></article>)}</div> : <EmptyState icon={BriefcaseBusiness} title={search ? 'No openings match that search' : 'No job openings yet'} body={search ? 'Try another title, company, or location.' : 'Create your first opening and add a job description to start matching.'} action="Create opening" onAction={onNew} />}</>
}

function JobPage({ job, candidates, loading, busy, compareMode, selected, filters, setFilters, onUpload, onCandidate, onToggleCompare, onCompare, onDelete, compareCount }) {
  const [showUpload, setShowUpload] = useState(false)
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef(null)
  const avg = candidates.length ? candidates.reduce((sum, candidate) => sum + (candidate.match?.overall_score || 0), 0) / candidates.length : 0
  return <><div className="job-detail-heading"><div><button className="back-link" onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'jobs' }))}><ArrowLeft size={14} /> All openings</button><span className="eyebrow dark">ROLE OVERVIEW <span className="eyebrow-line" /></span><h1>{job.title}</h1><p><Building2 size={14} />{job.company}<span>·</span><MapPin size={14} />{job.location || 'Location not specified'}<span>·</span>{job.employment_type}</p></div><div className="job-heading-actions"><button className="button subtle" onClick={onDelete}><X size={15} /> Close opening</button><button className="button primary" onClick={() => setShowUpload((value) => !value)}><Upload size={15} /> Add resumes</button></div></div>
    <div className="job-summary-strip"><div><span>REQUIRED SKILLS</span><div className="job-skill-row">{job.required_skills?.length ? job.required_skills.map((skill) => <span className="skill-pill" key={skill}>{skill}</span>) : <small>No required skills detected</small>}</div></div><div><span>EXPERIENCE</span><strong>{job.experience_required ? `${job.experience_required}+ years` : 'Flexible'}</strong></div><div><span>COMPENSATION</span><strong>{job.salary_min || job.salary_max ? `${money(job.salary_min)} – ${money(job.salary_max)}` : 'Not specified'}</strong></div><div><span>AVERAGE MATCH</span><strong className="summary-score">{Math.round(avg)}%</strong></div></div>
    {showUpload && <section className="upload-zone-wrap"><div className={`upload-zone ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); onUpload(event.dataTransfer.files) }}><input ref={fileInput} type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" multiple hidden onChange={(event) => { onUpload(event.target.files); event.target.value = '' }} /><span className="upload-icon"><CloudUpload size={21} /></span><div><strong>{busy === 'upload' ? 'Reading and matching resumes...' : 'Drop resumes here, or browse files'}</strong><p>PDF or DOCX · Up to 10 MB per file · Multiple files supported</p></div><button className="button secondary" disabled={busy === 'upload'} onClick={() => fileInput.current?.click()}>{busy === 'upload' ? <LoaderCircle className="spin" size={15} /> : <Upload size={15} />}{busy === 'upload' ? 'Processing' : 'Browse files'}</button></div>{busy === 'upload' && <div className="upload-progress"><i /></div>}</section>}
    <div className="candidate-toolbar"><div><span className="eyebrow dark">RANKED BY JOB-RELATED SIGNALS <span className="eyebrow-line" /></span><h2>Candidates <span className="result-count">{candidates.length}</span></h2></div><div className="candidate-tools"><label className="search-field candidate-search"><Search size={15} /><input value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Search candidates" /></label><select className="filter-select" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">All statuses</option>{STATUS_OPTIONS.map((status) => <option key={status}>{status}</option>)}</select><button className={`button ${compareMode ? 'secondary' : 'subtle'}`} onClick={onCompare}><GitCompareArrows size={15} />{compareMode ? `Compare (${compareCount})` : 'Compare'}</button></div></div>
    {compareMode && <div className="compare-hint"><GitCompareArrows size={15} />Select 2–5 candidates from the list, then use the compare button.</div>}
    <CandidateTable candidates={candidates.filter((candidate) => { const query = filters.search.toLowerCase(); return (!query || `${candidate.name} ${candidate.email || ''} ${(candidate.skills || []).map((item) => item.name).join(' ')}`.toLowerCase().includes(query)) && (!filters.status || candidate.status === filters.status) && (!filters.min_score || (candidate.match?.overall_score || 0) >= Number(filters.min_score)) })} onOpen={onCandidate} selected={selected} onToggle={onToggleCompare} compareMode={compareMode} loading={loading} />
    {!candidates.length && !loading && <div className="job-upload-empty"><span><FileSearch size={20} /></span><strong>Match the first resume to this role</strong><p>Upload PDF or DOCX resumes to extract job-related evidence and create a ranked review list.</p><button className="button secondary" onClick={() => setShowUpload(true)}><Upload size={15} />Add resumes</button></div>}
    <div className="fairness-note job-fairness"><ShieldCheck size={15} /><span>Scores are decision-support signals, not autonomous hiring decisions. Review each candidate’s evidence and consider the full context.</span></div>
  </>
}

function CandidatesPage({ candidates, total, loading, filters, setFilters, offset, setOffset, onCandidate }) {
  return <><div className="page-heading"><div><span className="eyebrow dark">TALENT DIRECTORY <span className="eyebrow-line" /></span><h1>Candidate pool</h1><p>Search and review profiles across your open roles.</p></div><span className="candidate-total"><Users size={15} />{total} profiles</span></div><div className="filter-bar candidate-filter-bar"><label className="search-field"><Search size={16} /><input value={filters.search} onChange={(event) => { setFilters({ ...filters, search: event.target.value }); setOffset(0) }} placeholder="Search names, skills, or experience..." /></label><label className="filter-control"><Filter size={14} /><select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">All statuses</option>{STATUS_OPTIONS.map((item) => <option key={item}>{item}</option>)}</select></label><label className="filter-control"><SlidersHorizontal size={14} /><select value={filters.sort_by} onChange={(event) => setFilters({ ...filters, sort_by: event.target.value })}><option value="score">Best match</option><option value="experience">Most experience</option><option value="name">Name A–Z</option><option value="date">Recently added</option></select></label><label className="filter-score">Min score<input type="number" min="0" max="100" value={filters.min_score} onChange={(event) => setFilters({ ...filters, min_score: event.target.value })} placeholder="0" /></label></div><div className="candidate-list-panel"><CandidateTable candidates={candidates} onOpen={onCandidate} loading={loading} /></div><div className="pagination"><span>Showing {total ? offset + 1 : 0}–{Math.min(offset + candidates.length, total)} of {total}</span><div><button className="icon-button" disabled={offset === 0} aria-label="Previous page" onClick={() => setOffset(Math.max(0, offset - 20))}><ArrowLeft size={15} /></button><button className="icon-button" disabled={offset + 20 >= total} aria-label="Next page" onClick={() => setOffset(offset + 20)}><ArrowRight size={15} /></button></div></div></>
}

function AnalyticsPage({ stats, reload }) {
  const [loading, setLoading] = useState(false)
  const jobData = stats?.candidates_per_job || []
  const pipeline = Object.entries(stats?.status_distribution || {}).map(([name, value]) => ({ name, value }))
  async function refresh() { setLoading(true); try { await reload() } finally { setLoading(false) } }
  return <><div className="page-heading"><div><span className="eyebrow dark">WORKSPACE METRICS <span className="eyebrow-line" /></span><h1>Insights</h1><p>Understand your pipeline and the skills appearing across your talent pool.</p></div><button className="button subtle" onClick={refresh} disabled={loading}>{loading ? <LoaderCircle className="spin" size={15} /> : <ArrowDownUp size={15} />} Refresh data</button></div><section className="analytics-metrics"><article><span>Match average</span><strong>{stats?.average_match_score || 0}%</strong><small>Across scored applications</small></article><article><span>Shortlisted</span><strong>{stats?.shortlisted_candidates || 0}</strong><small>Candidate profiles moved forward</small></article><article><span>Open positions</span><strong>{stats?.total_jobs || 0}</strong><small>Active roles in workspace</small></article><article><span>Resumes reviewed</span><strong>{stats?.resumes_processed || 0}</strong><small>Uploaded documents processed</small></article></section><section className="analytics-grid"><article className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow dark">ROLE ACTIVITY</span><h2>Candidates per opening</h2></div><span className="panel-icon"><BriefcaseBusiness size={15} /></span></div>{jobData.length ? <ResponsiveContainer width="100%" height={245}><BarChart data={jobData} margin={{ top: 10, right: 5, bottom: 5, left: -20 }}><CartesianGrid vertical={false} stroke="#eaf0eb" /><XAxis dataKey="title" tick={{ fill: '#7a8d87', fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fill: '#9aa8a1', fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip cursor={{ fill: '#f4f7f3' }} contentStyle={{ border: '1px solid #e4eae4', borderRadius: 6, fontSize: 12 }} /><Bar dataKey="candidates" fill="#548c78" radius={[4, 4, 0, 0]} maxBarSize={42} /></BarChart></ResponsiveContainer> : <div className="chart-empty">Create a job and process resumes to populate this chart.</div>}</article><article className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow dark">APPLICATION STATUS</span><h2>Candidate pipeline</h2></div><span className="panel-icon coral-panel"><Users size={15} /></span></div>{pipeline.length ? <div className="pie-layout"><ResponsiveContainer width="54%" height={220}><PieChart><Pie data={pipeline} dataKey="value" nameKey="name" innerRadius={58} outerRadius={83} paddingAngle={3}>{pipeline.map((entry, index) => <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="none" />)}</Pie><Tooltip contentStyle={{ border: '1px solid #e4eae4', borderRadius: 6, fontSize: 12 }} /></PieChart></ResponsiveContainer><div className="pie-legend">{pipeline.map((item, index) => <div key={item.name}><i style={{ background: PIE_COLORS[index % PIE_COLORS.length] }} /><span>{item.name}</span><strong>{item.value}</strong></div>)}</div></div> : <div className="chart-empty">Status counts appear after candidates are matched to a job.</div>}</article><article className="panel chart-panel skills-chart"><div className="panel-heading"><div><span className="eyebrow dark">TALENT LANDSCAPE</span><h2>Most detected skills</h2></div><span className="panel-icon"><Sparkles size={15} /></span></div>{stats?.top_skills?.length ? <ResponsiveContainer width="100%" height={245}><BarChart data={stats.top_skills.slice(0, 8)} layout="vertical" margin={{ top: 4, right: 10, bottom: 0, left: 30 }}><CartesianGrid horizontal={false} stroke="#eaf0eb" /><XAxis type="number" allowDecimals={false} hide /><YAxis type="category" dataKey="name" width={88} tick={{ fill: '#6e827b', fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ border: '1px solid #e4eae4', borderRadius: 6, fontSize: 12 }} /><Bar dataKey="count" fill="#d88162" radius={[0, 4, 4, 0]} maxBarSize={17} /></BarChart></ResponsiveContainer> : <div className="chart-empty">Skill distribution appears when resumes have been processed.</div>}</article><article className="panel missing-panel"><div className="panel-heading"><div><span className="eyebrow dark">SKILL GAPS</span><h2>Often missing requirements</h2></div><span className="panel-icon gold-panel"><GraduationCap size={15} /></span></div>{stats?.missing_skills?.length ? <div className="missing-list">{stats.missing_skills.slice(0, 8).map((item, index) => <div key={item.name}><span className="missing-rank">{String(index + 1).padStart(2, '0')}</span><span>{item.name}</span><small>{item.count} candidates</small></div>)}</div> : <div className="chart-empty">Missing requirements will appear after matching begins.</div>}</article></section><div className="fairness-note"><ShieldCheck size={15} /><span>These aggregate metrics describe submitted profiles only. They should not be interpreted as measures of protected groups or used as autonomous hiring criteria.</span></div></>
}

function SettingsPage({ user, onSignOut }) {
  return <><div className="page-heading"><div><span className="eyebrow dark">PREFERENCES & ACCESS <span className="eyebrow-line" /></span><h1>Workspace settings</h1><p>Account access, screening transparency, and privacy.</p></div></div><section className="settings-grid"><article className="panel settings-panel"><span className="panel-icon"><Users size={16} /></span><div><span className="eyebrow dark">ACCOUNT</span><h2>Recruiter profile</h2><p>Your signed-in workspace identity.</p></div><dl><div><dt>Full name</dt><dd>{user.full_name}</dd></div><div><dt>Email address</dt><dd>{user.email}</dd></div><div><dt>Workspace role</dt><dd>Recruiter</dd></div></dl><button className="button subtle" onClick={onSignOut}><LogOut size={15} /> Sign out</button></article><article className="panel settings-panel policy-panel"><span className="panel-icon gold-panel"><ShieldCheck size={16} /></span><div><span className="eyebrow dark">RESPONSIBLE SCREENING</span><h2>How matching works</h2><p>Scores combine six inspectable factors: skills (35%), description similarity (25%), experience (15%), education (10%), projects (10%), and certifications (5%).</p><p>Names and demographic attributes are excluded from scoring. Missing or ambiguous resume details are shown as not detected rather than inferred.</p><div className="policy-callout"><ShieldCheck size={16} /><p>AI-generated scores are decision-support signals and should be reviewed by qualified recruiters. The system does not make final hiring decisions.</p></div></div></article><article className="panel settings-panel"><span className="panel-icon coral-panel"><FileSearch size={16} /></span><div><span className="eyebrow dark">DATA HANDLING</span><h2>Candidate information</h2><p>Resume documents and parsed candidate records are stored in the configured database and upload directory.</p><ul className="privacy-list"><li><Check size={14} />Files are restricted to PDF and DOCX</li><li><Check size={14} />Uploads are limited to 10 MB each</li><li><Check size={14} />Passwords are hashed; session tokens expire</li><li><Check size={14} />LLM summaries use only relevant extracted details</li></ul></div></article></section></>
}

export default App
