import re
from typing import Optional


def detect_code_language(code: str) -> Optional[str]:
    """
    Intelligently analyzes a code snippet and returns the detected language/framework name:
    'Java', 'Python', 'Node', 'Shell', 'LangChain', 'Go', 'Rust', 'C++', 'C#',
    'PHP', 'Ruby', 'Kotlin', 'Swift', 'SQL', 'HTML', 'JSON', 'YAML', etc.
    Returns None if undetermined.
    """
    if not code or not code.strip():
        return None

    trimmed = code.strip()

    # 1. Shell / cURL / Bash / CLI
    if (
        re.match(r"^#!\s*/bin/(bash|sh|zsh)", trimmed)
        or re.match(r"^(curl|wget|npm|yarn|pnpm|bun|pip|pip3|git|brew|docker|kubectl|export|source|npx)\b", trimmed)
        or re.search(r"\bcurl\b", trimmed)
        or re.search(r"\$\(cat\s*<<\s*['\"]?\w+['\"]?", trimmed)
        or re.search(r"<<\s*['\"]?(JSON|EOF|BASH|SHELL|TXT)['\"]?", trimmed)
        or re.search(r"^\s*export\s+[A-Z0-9_]+\s*=", trimmed, re.MULTILINE)
        or re.search(r"--header\s+[\"']", trimmed)
        or re.search(r"-H\s+[\"']", trimmed)
        or " -H \"" in trimmed
        or " -H '" in trimmed
        or "--request POST" in trimmed
        or "--request GET" in trimmed
        or "--data-raw" in trimmed
        or "--data-binary" in trimmed
        or "curl -X" in trimmed
        or "curl https://" in trimmed
        or "curl http://" in trimmed
        or "invoke_url=" in trimmed
    ):
        return "Shell"

    # 2. LangChain (specific check before general Python/JS)
    if (
        "ChatNVIDIA" in trimmed
        or "from langchain" in trimmed
        or "import langchain" in trimmed
        or "langchain_nvidia_ai_endpoints" in trimmed
        or "langchain_core" in trimmed
        or "langchain_community" in trimmed
        or "ChatOpenAI" in trimmed
        or "ChatAnthropic" in trimmed
        or "ChatGoogleGenerativeAI" in trimmed
        or "HumanMessage" in trimmed
        or "SystemMessage" in trimmed
    ):
        return "LangChain"

    # 3. HTML / XML
    if re.search(r"^\s*<!DOCTYPE\s+html", trimmed, re.IGNORECASE) or (
        re.search(r"^\s*<html\b", trimmed, re.IGNORECASE) and "</html>" in trimmed
    ):
        return "HTML"

    # 4. PHP
    if "<?php" in trimmed or re.search(r"<\?php\b", trimmed):
        return "PHP"

    # 5. C# / .NET (evaluate before Java to prevent 'public class' ambiguity)
    if (
        re.search(r"^\s*using\s+System(\.[a-zA-Z0-9_]+)*;", trimmed, re.MULTILINE)
        or re.search(r"^\s*using\s+Microsoft(\.[a-zA-Z0-9_]+)*;", trimmed, re.MULTILINE)
        or "Console.WriteLine(" in trimmed
        or "Console.Write(" in trimmed
        or re.search(r"\bpublic\s+static\s+void\s+Main\s*\(\s*string\s*\[\s*\]", trimmed)
        or re.search(r"\bpublic\s+async\s+Task", trimmed)
        or re.search(r"^\s*namespace\s+[a-zA-Z0-9_.]+\s*\{?", trimmed, re.MULTILINE)
        or re.search(r"\bvar\s+\w+\s*=\s*new\s+HttpClient\(\);", trimmed)
    ):
        return "C#"

    # 6. Java
    if (
        re.search(r"^\s*package\s+[a-zA-Z0-9_.]+;", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+java\.[a-zA-Z0-9_.]+;", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+javax\.[a-zA-Z0-9_.]+;", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+jakarta\.[a-zA-Z0-9_.]+;", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+org\.springframework\.", trimmed, re.MULTILINE)
        or re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+\w+", trimmed)
        or re.search(r"\bpublic\s+static\s+void\s+main\s*\(\s*String\s*(?:\[\]|\.\.\.)", trimmed)
        or "System.out.println(" in trimmed
        or "System.out.print(" in trimmed
        or "System.err.println(" in trimmed
        or re.search(r"\bHttpClient\s+\w+\s*=\s*HttpClient\.newHttpClient\(\)", trimmed)
        or re.search(r"\bHttpRequest\.newBuilder\(\)", trimmed)
        or "@SpringBootApplication" in trimmed
        or "@RestController" in trimmed
        or "@Override" in trimmed
    ):
        return "Java"

    # 7. Kotlin
    if (
        re.search(r"\bfun\s+main\s*\(", trimmed)
        or re.search(r"^\s*import\s+kotlinx\.", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+io\.ktor\.", trimmed, re.MULTILINE)
        or re.search(r"\bdata\s+class\s+\w+\s*\(", trimmed)
        or (re.search(r"\bsuspend\s+fun\b", trimmed) and ("val " in trimmed or "var " in trimmed))
    ):
        return "Kotlin"

    # 8. Swift
    if (
        re.search(r"^\s*import\s+(SwiftUI|UIKit|Foundation|Combine)\b", trimmed, re.MULTILINE)
        or re.search(r"\bstruct\s+\w+\s*:\s*View\b", trimmed)
        or (re.search(r"\bfunc\s+\w+\s*\(", trimmed) and " -> " in trimmed and ("let " in trimmed or "var " in trimmed))
    ):
        return "Swift"

    # 9. C++ / C
    if (
        re.search(r"^\s*#include\s*<[a-zA-Z0-9_./]+>", trimmed, re.MULTILINE)
        or "std::cout" in trimmed
        or "std::cin" in trimmed
        or "std::endl" in trimmed
        or "std::vector" in trimmed
        or "std::string" in trimmed
        or "std::make_shared" in trimmed
        or "std::unique_ptr" in trimmed
        or "using namespace std;" in trimmed
        or re.search(r"\bint\s+main\s*\(\s*(?:int\s+argc)?", trimmed)
    ):
        return "C++"

    # 10. Rust
    if (
        re.search(r"\bfn\s+main\s*\(", trimmed)
        or re.search(r"\bpub\s+fn\s+\w+", trimmed)
        or re.search(r"^\s*use\s+std::", trimmed, re.MULTILINE)
        or re.search(r"^\s*use\s+tokio::", trimmed, re.MULTILINE)
        or re.search(r"^\s*use\s+anyhow::", trimmed, re.MULTILINE)
        or "println!(" in trimmed
        or "eprintln!(" in trimmed
        or "vec![" in trimmed
        or re.search(r"\blet\s+mut\s+\w+", trimmed)
        or "#[tokio::main]" in trimmed
    ):
        return "Rust"

    # 11. Go / Golang
    if (
        re.search(r"^\s*package\s+[a-zA-Z0-9_]+\s*(?://.*)?$", trimmed, re.MULTILINE)
        or re.search(r"\bfunc\s+main\s*\(", trimmed)
        or re.search(r"^\s*import\s+\(\s*\"fmt\"", trimmed, re.MULTILINE)
        or "fmt.Println(" in trimmed
        or "fmt.Printf(" in trimmed
        or "fmt.Sprintf(" in trimmed
        or re.search(r"\bfunc\s+\([a-zA-Z0-9_]+\s+\*?[a-zA-Z0-9_]+\)", trimmed)
    ):
        return "Go"

    # 12. Ruby
    if (
        (re.search(r"^\s*def\s+\w+", trimmed, re.MULTILINE) and re.search(r"\bend\s*$", trimmed, re.MULTILINE))
        or re.search(r"^\s*require\s+['\"](net/http|json|uri)['\"]", trimmed, re.MULTILINE)
        or "puts " in trimmed
        or "attr_accessor" in trimmed
        or "attr_reader" in trimmed
    ):
        return "Ruby"

    # 13. SQL
    if re.search(
        r"^\s*(SELECT\s+.*\s+FROM|INSERT\s+INTO\s+.*|UPDATE\s+.*\s+SET|DELETE\s+FROM|CREATE\s+TABLE)\b",
        trimmed,
        re.IGNORECASE | re.DOTALL,
    ):
        return "SQL"

    # 14. Node.js / TypeScript / JavaScript
    if (
        re.search(r"^\s*import\s+.*\s+from\s+[\"']", trimmed, re.MULTILINE)
        or re.search(r"\bconst\s+\w+\s*=", trimmed)
        or re.search(r"\blet\s+\w+\s*=", trimmed)
        or "console.log(" in trimmed
        or "require(" in trimmed
        or "await openai." in trimmed
        or "for await (const" in trimmed
        or "process.stdout.write" in trimmed
        or "process.env." in trimmed
        or "export default" in trimmed
        or "export const" in trimmed
        or re.search(r"\binterface\s+\w+\s*\{", trimmed)
        or re.search(r"\btype\s+\w+\s*=", trimmed)
    ):
        return "Node"

    # 15. Python
    if (
        re.search(r"^\s*from\s+[a-zA-Z0-9_.]+\s+import\b", trimmed, re.MULTILINE)
        or re.search(r"^\s*import\s+[a-zA-Z0-9_.]+\b", trimmed, re.MULTILINE)
        or re.search(r"^\s*def\s+[a-zA-Z0-9_]+\s*\(", trimmed, re.MULTILINE)
        or re.search(r"^\s*async\s+def\s+[a-zA-Z0-9_]+\s*\(", trimmed, re.MULTILINE)
        or re.search(r"^\s*class\s+[a-zA-Z0-9_]+[:\(]", trimmed, re.MULTILINE)
        or "from openai import" in trimmed
        or "import anthropic" in trimmed
        or "import google.generativeai" in trimmed
        or "import os" in trimmed
        or "import sys" in trimmed
        or "def " in trimmed
        or "print(" in trimmed
        or "if __name__" in trimmed
        or "completion = client." in trimmed
        or "client = OpenAI(" in trimmed
        or "client = openai." in trimmed
        or "client = anthropic." in trimmed
        or "__init__" in trimmed
        or "try:" in trimmed
        or "except " in trimmed
        or "with open(" in trimmed
    ):
        return "Python"

    # 16. JSON
    if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
        if '"model":' in trimmed or '"messages":' in trimmed or '"role":' in trimmed or (
            re.search(r'"[a-zA-Z0-9_]+"\s*:\s*', trimmed)
        ):
            return "JSON"

    # 17. YAML
    if trimmed.startswith("---") or re.search(r"^\s*(apiVersion|kind|metadata):\s*\S+", trimmed, re.MULTILINE):
        return "YAML"

    return None
