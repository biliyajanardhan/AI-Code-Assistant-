import streamlit as st
import requests
import re

OLLAMA_API_URL = "http://localhost:11434/api/generate"

st.set_page_config(page_title="🤖 AI Coding Assistant", layout="wide")
st.title("🤖 AI Coding Assistant using Ollama + CodeLlama")

# Sidebar
with st.sidebar:
    st.subheader("Choose Assistance Type")
    task = st.radio("Select Task", ["Explain", "Debug", "Complete", "Optimize"])

# --- Language Detection ---
import re

def detect_language(code):
    code = code.strip()

    # Python
    if re.search(r"^\s*def\s+\w+\s*\(", code, re.MULTILINE) or \
       re.search(r"^\s*import\s+\w+", code, re.MULTILINE) or \
       "print(" in code:
        return "Python"

    # C / C++
    if re.search(r"#include\s*<\w+>", code) or \
       re.search(r"\bint\s+main\s*\(", code):
        return "C++"

    # Java
    if re.search(r"public\s+class\s+\w+", code) or \
       re.search(r"public\s+static\s+void\s+main\s*\(", code):
        return "Java"

    # JavaScript / TypeScript
    if re.search(r"function\s+\w+\s*\(", code) or \
       re.search(r"console\.log\(", code) or \
       re.search(r"let\s+\w+", code) or \
       re.search(r"const\s+\w+", code):
        return "JavaScript"

    # Go
    if re.search(r"package\s+main", code) or \
       re.search(r"func\s+main\s*\(", code):
        return "Go"

    # Ruby
    if re.search(r"^\s*def\s+\w+", code, re.MULTILINE) and "end" in code:
        return "Ruby"

    # PHP
    if code.startswith("<?php") or re.search(r"\$\w+", code):
        return "PHP"

    # Bash / Shell
    if code.startswith("#!/bin/bash") or code.startswith("#!/bin/sh") or re.search(r"\becho\s+", code):
        return "Shell"

    # SQL
    if re.search(r"SELECT\s+.+\s+FROM\s+.+", code, re.IGNORECASE):
        return "SQL"

    # HTML
    if re.search(r"<!DOCTYPE html>", code, re.IGNORECASE) or \
       re.search(r"<html.*>", code):
        return "HTML"

    # CSS
    if re.search(r"\.\w+\s*{", code) or re.search(r"\#\w+\s*{", code):
        return "CSS"

    # JSON
    if code.startswith("{") and code.endswith("}"):
        try:
            import json
            json.loads(code)
            return "JSON"
        except Exception:
            pass

    # Default fallback
    return "Unknown"


# --- Prompt Builder ---
def build_prompt(task, code, language):
    base_prompt = (
        f"You are CodeLlama, an expert AI coding assistant.\n"
        f"Act like a senior software engineer mentoring a junior developer.\n"
        f"Be clear, thorough, and provide examples.\n"
        f"Detected Language: {language}\n\n"
        f"If any functions are declared but not implemented, complete them.\n"
    )

    task_prompts = {
        "Explain": (
            "Task: Explain the following code in simple terms.\n"
            "Also suggest improvements if any.\n\n"
        ),
        "Debug": (
            "Task: Debug the following code.\n"
            "Identify issues, provide a corrected version, and explain the fixes.\n\n"
        ),
        "Complete": (
            "Task: Complete the following incomplete code.\n"
            "Explain the logic and give an example usage.\n\n"
        ),
        "Optimize": (
            "Task: Optimize the following code for better performance and readability.\n"
            "Also implement any incomplete function definitions.\n"
            "Explain the changes and provide a sample usage.\n\n"
        )
    }

    return base_prompt + task_prompts[task] + f"Code:\n{code.strip()}\n"

# --- UI: Code Input ---
code_input = st.text_area(
    "Paste your code here:",
    placeholder="e.g., def factorial(n): ...",
    height=350
)

# --- Run Assistant ---
if st.button("Run Assistant"):
    if not code_input.strip():
        st.warning("Please enter code before running the assistant.")
    else:
        language = detect_language(code_input)
        prompt = build_prompt(task, code_input, language)

        with st.spinner("Consulting CodeLlama..."):
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": "codellama-3",
                    "prompt": prompt,
                    "stream": False
                }
            )

        if response.status_code == 200:
            output = response.json().get("response", "")

            st.markdown(f"### 🧠 Code Assistant Output — Task: `{task}`")
            st.markdown(f"**🔍 Detected Language:** `{language}`")

            if "```" in output:
                # Split on triple backticks to separate code and text
                blocks = output.split("```")

                for block in blocks:
                    stripped = block.strip()
                    # Detect code blocks starting with language tags (e.g. python, cpp)
                    if any(stripped.startswith(lang) for lang in ("python", "cpp", "java", "js", "c")):
                        # Display code block (skip the first line which is language)
                        code_content = "\n".join(stripped.split('\n')[1:]).strip()
                        st.code(code_content)
                    else:
                        # This is non-code block (like explanations or sample outputs)
                        # Let's highlight if it contains keywords for sample usage/output
                        lowered = stripped.lower()
                        if "sample usage" in lowered or "example" in lowered or "output" in lowered:
                            st.markdown(f"**Sample Output / Usage:**\n```\n{stripped}\n```")
                        else:
                            st.markdown(stripped)
            else:
                st.markdown(output)
        else:
            st.error(f"Error from Ollama API: {response.status_code}\n{response.text}")
