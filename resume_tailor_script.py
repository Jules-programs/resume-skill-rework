import json
import os
from pathlib import Path
from dotenv import load_dotenv
import pdfkit
import ollama

# Load environment variables
load_dotenv()

# -----------------------------
# LOAD EXTERNAL DATA
# -----------------------------

def load_profile():
    """Load personal info from .env file."""
    return {
        "FIRST_NAME": os.getenv("FIRST_NAME", ""),
        "LAST_NAME": os.getenv("LAST_NAME", ""),
        "EMAIL": os.getenv("EMAIL", ""),
        "PHONE": os.getenv("PHONE", ""),
        "ADDRESS": os.getenv("ADDRESS", ""),
        "GITHUB": os.getenv("GITHUB", ""),
        "LINKEDIN": os.getenv("LINKEDIN", "")
    }

def load_projects():
    return json.loads(Path("projects.json").read_text())["projects"]

def load_experience():
    return json.loads(Path("experience.json").read_text())["experience"]

def load_master_skills():
    return json.loads(Path("skills.json").read_text())


# -----------------------------
# LLM CALL (YOU IMPLEMENT)
# -----------------------------

def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = ollama.chat(
        model="phi3",   # or "llama3" if you prefer
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["message"]["content"]


# -----------------------------
# JOB PROFILE EXTRACTION
# -----------------------------

def extract_job_profile(job_posting: str) -> dict:
    system_prompt = "Extract structured job requirements. Always return valid JSON."
    user_prompt = f"""
    Extract the following fields from the job posting and return ONLY valid JSON:

    {{
      "required_skills": [],
      "preferred_skills": [],
      "tools": [],
      "responsibilities": [],
      "soft_skills": [],
      "keywords": [],
      "job_title": "",
      "company_name": ""
    }}

    Job posting:
    {job_posting}
    """

    text = call_llm(system_prompt, user_prompt)

    try:
        return json.loads(text)
    except:
        return {
            "required_skills": [],
            "preferred_skills": [],
            "tools": [],
            "responsibilities": [],
            "soft_skills": [],
            "keywords": [],
            "job_title": "",
            "company_name": ""
        }


# -----------------------------
# SKILL FILTERING
# -----------------------------

def normalize_skill(s: str) -> str:
    return s.lower().strip()

def build_relevant_skills(job_profile: dict) -> dict:
    master = load_master_skills()

    job_terms = set(
        normalize_skill(x)
        for key in ["required_skills", "preferred_skills", "tools", "keywords"]
        for x in job_profile.get(key, [])
    )

    ALWAYS_KEEP = {
        "git", "github", "debugging", "react", "next.js",
        "node.js", "express.js", "sql", "mysql", "mongodb"
    }

    filtered = {}

    for category, skills in master.items():
        kept = []
        for skill in skills:
            norm = normalize_skill(skill)
            if any(term in norm or norm in term for term in job_terms) or norm in ALWAYS_KEEP:
                kept.append(skill)

        if kept:
            filtered[category] = kept

    return filtered


# -----------------------------
# SKILLS TABLE HTML
# -----------------------------

def generate_skills_table_html(filtered_skills: dict) -> str:
    rows = []

    for category, skills in filtered_skills.items():
        rows.append(f'<tr><td class="category">{category}</td><td></td></tr>')

        for i in range(0, len(skills), 2):
            left = skills[i]
            right = skills[i + 1] if i + 1 < len(skills) else ""
            rows.append(
                f"<tr><td class='skill-item'>{left}</td>"
                f"<td class='skill-item'>{right}</td></tr>"
            )

    return "<table>\n" + "\n".join(rows) + "\n</table>"


# -----------------------------
# GENERATE SUMMARY / PROJECTS / EXPERIENCE
# -----------------------------

def generate_summary(job_profile):
    system_prompt = "Write a concise resume summary for a junior full-stack developer."
    user_prompt = f"""
    Job profile:
    {json.dumps(job_profile, indent=2)}

    Write a 3–4 line summary aligned with the job.
    """
    return call_llm(system_prompt, user_prompt)

def generate_projects_section(job_profile):
    projects = load_projects()

    system_prompt = "Rewrite project descriptions to align with the job posting."
    user_prompt = f"""
    Job profile:
    {json.dumps(job_profile, indent=2)}

    Projects:
    {json.dumps(projects, indent=2)}

    Rewrite them professionally with bullet points.
    """
    return call_llm(system_prompt, user_prompt)

def generate_experience_section(job_profile):
    experience = load_experience()

    system_prompt = "Rewrite work experience to highlight transferable skills."
    user_prompt = f"""
    Job profile:
    {json.dumps(job_profile, indent=2)}

    Experience:
    {json.dumps(experience, indent=2)}

    Rewrite them professionally with bullet points.
    """
    return call_llm(system_prompt, user_prompt)


# -----------------------------
# COVER LETTER
# -----------------------------

def generate_cover_letter(job_profile):
    system_prompt = "Write a tailored cover letter for a junior full-stack developer."
    user_prompt = f"""
    Job profile:
    {json.dumps(job_profile, indent=2)}

    Write a 3–4 paragraph cover letter.
    """
    return call_llm(system_prompt, user_prompt)


# -----------------------------
# TEMPLATE FILLING
# -----------------------------

def fill_static_placeholders(html: str) -> str:
    profile = load_profile()
    for key, value in profile.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html

def fill_resume_template(summary, projects, experience, skills_table_html):
    html = Path("resume_template.html").read_text()

    html = fill_static_placeholders(html)
    html = html.replace("{{SUMMARY}}", summary.strip())
    html = html.replace("{{PROJECTS}}", projects.strip().replace("\n", "<br>"))
    html = html.replace("{{EXPERIENCE}}", experience.strip().replace("\n", "<br>"))
    html = html.replace("{{SKILLS_TABLE}}", skills_table_html)

    return html


def build_cover_letter_html(text, job_profile):
    html = f"""
    <html><body>
    <div class="container">
        <h2>Cover Letter</h2>
        <p>{text.replace("\n", "<br>")}</p>
    </div>
    </body></html>
    """
    return html


# -----------------------------
# HTML → PDF
# -----------------------------

def html_to_pdf(html: str, output_path: str):
    pdfkit.from_string(html, output_path, options={"enable-local-file-access": None})


# -----------------------------
# MAIN PIPELINE
# -----------------------------

def tailor_for_job(job_posting: str):
    job_profile = extract_job_profile(job_posting)

    filtered_skills = build_relevant_skills(job_profile)
    skills_table_html = generate_skills_table_html(filtered_skills)

    summary = generate_summary(job_profile)
    projects = generate_projects_section(job_profile)
    experience = generate_experience_section(job_profile)
    cover_letter_text = generate_cover_letter(job_profile)

    resume_html = fill_resume_template(summary, projects, experience, skills_table_html)
    cover_letter_html = build_cover_letter_html(cover_letter_text, job_profile)

    html_to_pdf(resume_html, "tailored_resume.pdf")
    html_to_pdf(cover_letter_html, "tailored_cover_letter.pdf")

    print("Generated tailored_resume.pdf and tailored_cover_letter.pdf")


# -----------------------------
# CLI ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    print("Paste the job posting below. End with an empty line:")
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)

    job_posting_text = "\n".join(lines)
    tailor_for_job(job_posting_text)