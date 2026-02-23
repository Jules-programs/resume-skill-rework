import json
import os
from pathlib import Path
from dotenv import load_dotenv
import pdfkit
import ollama
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
        "LINKEDIN": os.getenv("LINKEDIN", ""),
        "SCHOOL": os.getenv("SCHOOL", ""),
        "DEGREE": os.getenv("DEGREE", ""),
        "GRADUATION_DATE": os.getenv("GRADUATION_DATE", ""),
        "PROGRAM": os.getenv("PROGRAM", ""),
        "GPA": os.getenv("GPA", ""),
        "LANGUAGES": os.getenv("LANGUAGES", ""),
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
    """Call Ollama LLM with retry logic and error handling."""
    try:
        logger.info("Calling LLM...")
        response = ollama.chat(
            model="phi3",   # or "llama3", "mistral", etc.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


# -----------------------------
# JOB PROFILE EXTRACTION
# -----------------------------

def extract_job_profile(job_posting: str) -> dict:
    """Extract job requirements from job posting using LLM."""
    system_prompt = """You are an expert recruiter analyzing job postings.
    Extract the key requirements, skills, and responsibilities.
    Always return ONLY valid JSON, no markdown or extra text.
    Focus on technical skills, tools, soft skills, and core responsibilities.
    """
    
    user_prompt = f"""
    Extract job details from this posting. Return ONLY this JSON structure:

    {{
      "job_title": "exact job title",
      "company_name": "company name if mentioned",
      "required_skills": ["skill1", "skill2"],
      "preferred_skills": ["skill3", "skill4"],
      "tools": ["tool1", "tool2"],
      "responsibilities": ["responsibility1", "responsibility2"],
      "soft_skills": ["communication", "teamwork"],
      "keywords": ["keyword1", "keyword2"]
    }}

    Job posting:
    {job_posting}
    """

    text = call_llm(system_prompt, user_prompt)

    try:
        # Try to extract JSON from the response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Failed to parse job profile JSON: {e}")
    
    # Default fallback
    return {
        "job_title": "",
        "company_name": "",
        "required_skills": [],
        "preferred_skills": [],
        "tools": [],
        "responsibilities": [],
        "soft_skills": [],
        "keywords": []
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
        "TypeScript", 
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
    """Generate a professional resume summary tailored to the job."""
    system_prompt = """You are an expert resume writer specializing in junior full-stack developers.
    Write compelling, concise professional summaries that:
    - Highlight relevant skills and experience
    - Use strong action words
    - Match the job requirements
    - Are 2-3 sentences that fit on one line in a resume
    - Focus on technical skills and the value you bring
    """
    
    user_prompt = f"""
    Write a professional resume summary (2-3 sentences) for a Full-Stack Developer applying to this position:
    
    Job Title: {job_profile.get('job_title', 'Full-Stack Developer')}
    Required Skills: {', '.join(job_profile.get('required_skills', [])[:5])}
    Key Responsibilities: {', '.join(job_profile.get('responsibilities', [])[:3])}
    
    The summary should:
    - Be 2-3 sentences maximum
    - Include relevant technical skills from the job posting
    - Use action-oriented language
    - Show enthusiasm for the role
    - Return ONLY the summary text, nothing else
    """
    return call_llm(system_prompt, user_prompt).strip()

def build_projects_html(projects_text: str) -> str:
    """Convert project text to HTML with proper structure."""
    html = []
    lines = projects_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        elif line.startswith('**') and line.endswith('**'):
            # Project title
            title = line.replace('**', '')
            html.append(f'<div class="entry"><div class="entry-title"><strong>{title}</strong></div>')
            html.append('<ul class="entry-bullets">')
        elif line.startswith('•'):
            # Bullet point
            text = line[1:].strip()
            html.append(f'<li>{text}</li>')
    
    if html and not html[-1].startswith('<ul'):
        html.append('</ul></div>')
    
    return '\n'.join(html)


def build_experience_html(experience_text: str) -> str:
    """Convert experience text to HTML with proper structure."""
    html = []
    lines = experience_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        elif line.startswith('**') and line.endswith('**'):
            # Role | Company header
            header = line.replace('**', '')
            html.append(f'<div class="entry"><div class="entry-title"><strong>{header}</strong></div>')
            html.append('<ul class="entry-bullets">')
        elif line.startswith('•'):
            # Bullet point
            text = line[1:].strip()
            html.append(f'<li>{text}</li>')
    
    if html and not html[-1].startswith('<ul'):
        html.append('</ul></div>')
    
    return '\n'.join(html)


def generate_projects_section(job_profile):
    """Rewrite projects to highlight relevant skills from the job posting."""
    projects = load_projects()

    system_prompt = """You are an expert resume writer.
    Rewrite project descriptions to:
    - Highlight technologies matching the job posting
    - Use strong action verbs (Built, Designed, Implemented, etc.)
    - Show measurable impact where possible
    - Keep bullet points concise and scannable
    - Match the technical depth of the role
    """
    
    user_prompt = f"""
    Rewrite these projects for a job posting focusing on:
    - Tech Stack: {', '.join(job_profile.get('required_skills', [])[:5])}
    - Key Responsibilities: {', '.join(job_profile.get('responsibilities', [])[:2])}
    
    For each project, provide 3-4 bullet points that:
    1. Emphasize technologies used that match the job
    2. Show the business/user impact
    3. Use active voice and power verbs
    4. Keep each point under 15 words
    
    Projects to rewrite:
    {json.dumps(projects, indent=2)}
    
    Return formatted as:
    **Project Name**
    • Bullet 1
    • Bullet 2
    • Bullet 3
    """
    return call_llm(system_prompt, user_prompt).strip()

def generate_experience_section(job_profile):
    """Rewrite work experience to show transferable skills for the target role."""
    experience = load_experience()

    system_prompt = """You are an expert resume writer specializing in career transitions.
    Rewrite work experience to:
    - Translate non-tech roles into technical/professional value
    - Highlight transferable skills (teamwork, problem-solving, leadership)
    - Connect experience to the job requirements
    - Use metrics and concrete examples
    - Show growth and learning potential
    """
    
    user_prompt = f"""
    Rewrite work experience to highlight transferable value for a development role seeking:
    - Soft Skills: {', '.join(job_profile.get('soft_skills', [])[:3])}
    - Key Traits: Attention to detail, collaboration, problem-solving
    
    For each role, rewrite as 2-3 bullet points that:
    1. Show relevant soft skills
    2. Demonstrate learning and responsibility
    3. Connect to development/technical work mindset
    4. Use metrics or concrete examples
    
    Experience:
    {json.dumps(experience, indent=2)}
    
    Return formatted as:
    **Role | Company** (dates)
    • Impact-focused bullet point
    • Skill-focused bullet point
    • Growth-focused bullet point
    """
    return call_llm(system_prompt, user_prompt).strip()


# -----------------------------
# COVER LETTER
# -----------------------------

def generate_cover_letter(job_profile):
    """Generate a compelling, personalized cover letter."""
    profile = load_profile()
    
    system_prompt = """You are an expert cover letter writer.
    Write compelling cover letters that:
    - Open with genuine enthusiasm
    - Show understanding of the company/role
    - Connect your skills to their needs
    - Include a memorable personal story or insight
    - Close with a strong call-to-action
    - Are professional yet conversational
    - Use the candidate's actual background
    """
    
    user_prompt = f"""
    Write a cover letter for {profile.get('FIRST_NAME', 'the candidate')} applying for:
    
    Position: {job_profile.get('job_title', 'Full-Stack Developer')}
    Company: {job_profile.get('company_name', 'the company')}
    
    Candidate Background:
    - Education: {profile.get('DEGREE', 'Computer Science program')}
    - Key Projects: Building full-stack applications with modern tech
    - Work Style: Collaborative, detail-oriented, eager to learn
    
    Job Requirements:
    - Required Skills: {', '.join(job_profile.get('required_skills', [])[:4])}
    - Soft Skills Needed: {', '.join(job_profile.get('soft_skills', [])[:3])}
    - Responsibilities: {', '.join(job_profile.get('responsibilities', [])[:2])}
    
    Write exactly 3 paragraphs:
    1. Opening: Why you're excited about THIS role and company
    2. Body: How your skills/experience match their needs (use specific examples)
    3. Closing: Call to action and enthusiasm for discussion
    
    Keep it concise (250-350 words total), professional, and authentic.
    Return ONLY the cover letter text.
    """
    return call_llm(system_prompt, user_prompt).strip()


# -----------------------------
# TEMPLATE FILLING
# -----------------------------

def fill_static_placeholders(html: str) -> str:
    profile = load_profile()
    for key, value in profile.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html

def fill_resume_template(summary, projects, experience, skills_table_html):
    """Fill static template with generated content."""
    html = Path("resume-tailor/resume_template.html").read_text()

    html = fill_static_placeholders(html)
    html = html.replace("{{SUMMARY}}", summary.strip())
    
    # Convert markdown-style content to HTML
    projects_html = build_projects_html(projects)
    experience_html = build_experience_html(experience)
    
    html = html.replace("{{PROJECTS}}", projects_html)
    html = html.replace("{{EXPERIENCE}}", experience_html)
    html = html.replace("{{SKILLS_TABLE}}", skills_table_html)

    return html


def build_cover_letter_html(text, job_profile):
    """Build a professional HTML cover letter."""
    profile = load_profile()
    
    # Convert paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    paragraphs_html = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Cover Letter - {profile.get('FIRST_NAME', 'Candidate')}</title>
    <style>
        body {{
            font-family: "Georgia", serif;
            line-height: 1.6;
            color: #333;
            margin: 40px;
        }}
        .cover-letter {{
            max-width: 8.5in;
            margin: 0 auto;
        }}
        .letter-header {{
            margin-bottom: 30px;
        }}
        .sender-address {{
            font-size: 12px;
            color: #666;
            line-height: 1.4;
            margin-bottom: 20px;
        }}
        .letter-date {{
            font-size: 12px;
            color: #666;
            margin-bottom: 20px;
        }}
        .letter-content p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        .closing {{
            margin-top: 25px;
            font-size: 14px;
        }}
        .signature {{
            margin-top: 35px;
        }}
    </style>
</head>
<body>
<div class="cover-letter">
    <div class="letter-header">
        <div class="sender-address">
            <strong>{profile.get('FIRST_NAME', '')} {profile.get('LAST_NAME', '')}</strong><br>
            {profile.get('EMAIL', '')}<br>
            {profile.get('PHONE', '')}
        </div>
        <div class="letter-date">{datetime.now().strftime('%B %d, %Y')}</div>
    </div>
    
    <div class="letter-content">
        {paragraphs_html}
    </div>
    
    <div class="closing">
        <p>Sincerely,</p>
        <div class="signature">
            {profile.get('FIRST_NAME', '')} {profile.get('LAST_NAME', '')}
        </div>
    </div>
</div>
</body>
</html>
    """
    return html


# -----------------------------
# HTML → PDF
# -----------------------------

def html_to_pdf(html: str, output_file: str) -> bool:
    """Convert HTML string to PDF file."""
    try:
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", output_file)
        
        options = {
            'enable-local-file-access': None,
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in'
        }
        
        pdfkit.from_string(html, output_path, options=options)
        logger.info(f"✓ Generated: {output_path}")
        return True
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False


# -----------------------------
# MAIN PIPELINE
# -----------------------------

def tailor_for_job(job_posting: str):
    """Main pipeline: Extract job profile → Generate tailored content → Export PDFs."""
    try:
        logger.info("="*50)
        logger.info("RESUME TAILOR - Starting")
        logger.info("="*50)
        
        logger.info("\n📋 Extracting job profile...")
        job_profile = extract_job_profile(job_posting)
        logger.info(f"  ✓ Job Title: {job_profile.get('job_title', 'N/A')}")
        logger.info(f"  ✓ Company: {job_profile.get('company_name', 'N/A')}")
        
        logger.info("\n🎯 Building relevant skills...")
        filtered_skills = build_relevant_skills(job_profile)
        skills_table_html = generate_skills_table_html(filtered_skills)
        logger.info(f"  ✓ {sum(len(v) for v in filtered_skills.values())} relevant skills identified")

        logger.info("\n✍️  Generating tailored content...")
        summary = generate_summary(job_profile)
        logger.info("  ✓ Professional summary created")
        
        projects = generate_projects_section(job_profile)
        logger.info("  ✓ Projects rewritten to match role")
        
        experience = generate_experience_section(job_profile)
        logger.info("  ✓ Experience tailored with transferable skills")
        
        cover_letter_text = generate_cover_letter(job_profile)
        logger.info("  ✓ Personalized cover letter written")

        logger.info("\n📄 Building HTML documents...")
        resume_html = fill_resume_template(summary, projects, experience, skills_table_html)
        cover_letter_html = build_cover_letter_html(cover_letter_text, job_profile)
        logger.info("  ✓ HTML generated")

        logger.info("\n📑 Converting to PDF...")
        success_resume = html_to_pdf(resume_html, "tailored_resume.pdf")
        success_letter = html_to_pdf(cover_letter_html, "tailored_cover_letter.pdf")
        
        if success_resume and success_letter:
            logger.info("\n" + "="*50)
            logger.info("✨ SUCCESS! Documents ready in /output/")
            logger.info("="*50)
        else:
            logger.warning("\n⚠️  Some PDFs failed to generate")
            
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        raise


# -----------------------------
# CLI ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    try:
        print("\n" + "="*50)
        print("  🚀 RESUME TAILORING SYSTEM")
        print("="*50)
        print("\nPaste the job posting below.")
        print("When done, press Enter twice to submit:\n")
        
        lines = []
        blank_count = 0
        while True:
            try:
                line = input()
                if not line.strip():
                    blank_count += 1
                    if blank_count >= 2:
                        break
                else:
                    blank_count = 0
                    lines.append(line)
            except EOFError:
                break

        job_posting_text = "\n".join(lines)
        
        if not job_posting_text.strip():
            print("\n❌ No job posting provided!")
        else:
            tailor_for_job(job_posting_text)
            
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")