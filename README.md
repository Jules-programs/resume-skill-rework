# Resume Tailor System 🚀

Automatically tailor your resume and cover letter to specific job postings using AI. This system extracts job requirements from postings and regenerates your resume/cover letter to highlight the most relevant skills and experiences.

## Features ✨

- **Smart Job Extraction**: LLM analyzes job postings to extract requirements, skills, and responsibilities
- **Intelligent Skill Filtering**: Only shows skills that match the job posting  
- **Automated Content Generation**:
  - Professional resume summary aligned with the role
  - Rewritten projects emphasizing relevant technologies
  - Tailored experience highlighting transferable skills
  - Personalized cover letter with specific details
- **Professional Formatting**: Optimized CSS styling for PDF export
- **One-Click Output**: Generates both PDF resume and cover letter in minutes

## Installation 🔧

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- wkhtmltopdf (for PDF generation)

### Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Ollama (in a separate terminal)
ollama serve

# 3. Pull a model (if not already available)
ollama pull phi3
# or: ollama pull llama2, mistral, etc.

# 4. Set up your profile (.env file)
# Create a .env file in the root directory:
FIRST_NAME=Your
LAST_NAME=Name
EMAIL=your.email@example.com
PHONE=+1-555-0000
ADDRESS=City, State
GITHUB=https://github.com/yourprofile
LINKEDIN=https://linkedin.com/in/yourprofile
SCHOOL=University Name
DEGREE=Bachelor of Science in Computer Science
GRADUATION_DATE=May 2024
PROGRAM=Major/Focus Area
GPA=3.75
LANGUAGES=English, Spanish
```

## Usage 📝

1. **Populate your data**:
   - Update `experience.json` with your work history
   - Update `projects.json` with your projects
   - Update `skills.json` with your technical skills
   - Set your profile in `.env` file

2. **Run the script**:
   ```bash
   python resume_tailor_script.py
   ```

3. **Paste job posting**:
   ```
   We are hiring a Senior Full-Stack Developer with 5+ years of experience 
   in React, Node.js, TypeScript, and AWS. You'll lead the platform team...
   [Continue pasting the full job posting]
   
   [Press Enter twice when done]
   ```

4. **Generated files** appear in `output/`:
   - `tailored_resume.pdf` - Your resume optimized for this job
   - `tailored_cover_letter.pdf` - Personalized cover letter

## Data Files 📋

### experience.json
```json
{
  "experience": [
    {
      "role": "Senior Developer",
      "company": "Tech Corp",
      "dates": "Jan 2022 - Present",
      "bullets": [
        "Led development of real-time analytics platform serving 100k+ users",
        "Architected microservices reducing latency by 40%"
      ]
    }
  ]
}
```

### projects.json
```json
{
  "projects": [
    {
      "name": "Project Name",
      "bullets": [
        "Key technical achievement",
        "Problem solved and result"
      ]
    }
  ]
}
```

### skills.json
Organize skills by category:
```json
{
  "Programming Languages": ["JavaScript", "TypeScript", "Python"],
  "Frontend": ["React", "Next.js", "Tailwind CSS"],
  "Backend": ["Node.js", "Express", "PostgreSQL"],
  "Tools & DevOps": ["Docker", "Kubernetes", "AWS"]
}
```

## LLM Configuration ⚙️

The script uses **Ollama** for local LLM inference. You can change the model in `resume_tailor_script.py`:

```python
# Line 48 - Change model
response = ollama.chat(
    model="phi3",  # <-- Change this
    messages=[...]
)
```

### Recommended Models:
- **phi3** (smallest, fastest) - Good for quick iterations
- **mistral** (balanced) - Better quality, moderate speed
- **llama2** (largest) - Highest quality, slower

Pull a model:
```bash
ollama pull mistral
```

## How It Works 🔄

1. **Job Profile Extraction** - LLM analyzes job posting and extracts:
   - Required & preferred skills
   - Tools & technologies
   - Soft skills
   - Responsibilities & keywords

2. **Skill Filtering** - Matches extracted skills against your master skill list

3. **Content Generation** - LLM rewrites:
   - Professional summary (2-3 sentences)
   - Project descriptions (emphasis on matching tech)
   - Experience bullets (transfer to dev roles)
   - Cover letter (personalized, 3 paragraphs)

4. **HTML Generation** - Professional resume/letter HTML with:
   - Clean, modern styling
   - Proper semantic structure
   - Print-optimized for PDF

5. **PDF Export** - Converts HTML to PDFs ready to send

## Troubleshooting 🔧

### "Ollama connection failed"
- Make sure Ollama is running: `ollama serve`
- Check it's accessible: `curl http://localhost:11434/api/tags`

### "PDF generation failed"
- Install wkhtmltopdf:
  - **Windows**: Download from https://wkhtmltopdf.org/downloads.html
  - **Mac**: `brew install --cask wkhtmltopdf`
  - **Linux**: `sudo apt-get install wkhtmltopdf`

### "Bad JSON from LLM"
- This can happen with smaller models. Try a larger model:
  ```bash
  ollama pull mistral
  # Change model in script to "mistral"
  ```

### Output PDFs look wrong
- Check that all template placeholders are filled in `.env`
- Verify HTML files generated in `/output/` look correct
- Ensure CSS file exists at `resume-tailor/styles/styles.css`

## Tips for Best Results 💡

1. **Be detailed in experience.json**: The more context you provide, the better the AI can tailor content

2. **Comprehensive skills.json**: Include all skills you want highlighted when relevant

3. **Job posting length**: Longer postings with more details = better extraction

4. **Review outputs**: Always review generated resume/letter before sending. Customize if needed.

5. **Try different models**: Experiment with different Ollama models for varied output quality

6. **Update regularly**: Keep your `skills.json` and `projects.json` current

## Advanced Usage 🚀

### Batch Processing
To tailor to multiple jobs, simply run the script multiple times:
```bash
python resume_tailor_script.py
# Paste first job posting
# Outputs to /output/tailored_resume.pdf
# Move/rename these files
python resume_tailor_script.py
# Paste second job posting
# Outputs new versions
```

### Customize Prompts
Edit the LLM system prompts in `resume_tailor_script.py` to change the AI behavior:
- `generate_summary()` - Controls professional summary style
- `generate_projects_section()` - How projects are rewritten
- `generate_experience_section()` - How experience is tailored
- `generate_cover_letter()` - Cover letter tone and content

### Custom Styling  
Modify `resume-tailor/styles/styles.css` to change:
- Colors (currently #003d82 blue primary color)
- Fonts (currently sans-serif for modern look)
- Spacing (adjust margins/padding)
- PDF layout (paper size, margins)

## Performance Notes 📊

- **Speed**: Depends on LLM model and hardware
  - phi3: ~10-15 seconds per run
  - mistral: ~20-30 seconds per run
  - llama2: ~40-60 seconds per run

- **Quality**: Larger models generally produce better output
- **Memory**: Requires ~4GB+ RAM for most models

## License

MIT - Use freely and modify as needed!
