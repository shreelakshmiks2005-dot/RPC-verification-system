import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

// ── Resume ──────────────────────────────────────────────────
export async function verifyResume(
  candidateId: string,
  candidateName: string,
  requiredSkills: string,
  preferredSkills: string,
  file: File,
) {
  const form = new FormData()
  form.append('candidate_id', candidateId)
  form.append('candidate_name', candidateName)
  form.append('required_skills', requiredSkills)
  form.append('preferred_skills', preferredSkills)
  form.append('file', file)
  const { data } = await api.post('/verify-resume', form)
  return data
}

// ── Project ─────────────────────────────────────────────────
export async function verifyProject(payload: {
  candidate_id: string
  candidate_name: string
  github_username: string
  repo_link: string
  project_type: string
}) {
  const { data } = await api.post('/verify-project', payload)
  return data
}

// ── Certificate ─────────────────────────────────────────────
export async function verifyCertificate(
  candidateId: string,
  candidateName: string,
  expectedCourse: string,
  verifyOnline: boolean,
  file: File,
) {
  const form = new FormData()
  form.append('candidate_id', candidateId)
  form.append('candidate_name', candidateName)
  form.append('expected_course', expectedCourse)
  form.append('verify_online', String(verifyOnline))
  form.append('file', file)
  const { data } = await api.post('/verify-certificate', form)
  return data
}

// ── Full ─────────────────────────────────────────────────────
export async function verifyFull(
  fields: {
    candidate_id: string
    candidate_name: string
    github_username: string
    repo_link: string
    project_type: string
    required_skills: string
    preferred_skills: string
    expected_course: string
    verify_online: boolean
  },
  resumeFile?: File | null,
  certFile?: File | null,
) {
  const form = new FormData()
  Object.entries(fields).forEach(([k, v]) => form.append(k, String(v)))
  if (resumeFile) form.append('resume_file', resumeFile)
  if (certFile) form.append('certificate_file', certFile)
  const { data } = await api.post('/verify-full', form)
  return data
}
