#!/usr/bin/env python3
"""
GitHub Issue Mining Script for OS-Portability Project

This script systematically mines GitHub issues for OS-portability problems using:
1. Concept-based keyword matching (OS, FIX, TEST_CI, CAUSE, API buckets)
2. Proximity gating (sentence-level co-occurrence filtering)
3. Optional LLM-based validation for quality assurance

Key Features:
- Concept buckets: Organized keywords into semantic categories
- Strict proximity gating: OS and FIX keywords must co-occur in the same sentence/line
- Multithreaded processing: Scalable across many repositories
- Caching: Avoids redundant API calls
- AI validation: Optional post-processing with LLM for quality control

Usage:
  python mining_issues_script.py --input repos.csv --output results.csv --workers 8 \\
    --token <GITHUB_TOKEN> --openai-token <OPENAI_API_KEY>

Input Format:
  CSV file with repository identifiers (one per line):
  - owner/repo format, OR
  - full GitHub URLs

Output Format:
  CSV with columns: repository, type, source, keyword, summary, link, status, 
                    number, created_at, author, labels, ai_issue_summary, 
                    ai_is_os_portability, ai_is_fix_merged, ai_confidence_pct

Token Sources (priority order):
  1. Command-line arguments (--token, --openai-token)
  2. Environment variables (GITHUB_TOKEN, OPENAI_API_KEY, etc.)
  3. Local files (token.txt, .github_token, openai.key, etc.)

Note: This script requires valid API tokens to run. For research replication,
      obtain tokens from: https://github.com/settings/tokens (GitHub)
                         https://platform.openai.com/api-keys (OpenAI)
"""

import os
import re
import csv
import sys
import time
import argparse
from typing import List, Dict, Iterable, Optional, Tuple
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# -----------------------------
# Configuration
# -----------------------------

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "research-portability-mining/1.0"

# Global GitHub request counter for statistics
GLOBAL_REQUEST_COUNTER = [0]

# Output CSV field names
FIELDNAMES = [
    "repository", "type", "source", "keyword", "summary", "link",
    "status", "number", "created_at", "author", "labels",
    # AI post-analysis fields
    "ai_issue_summary", "ai_is_os_portability", "ai_is_fix_merged", "ai_confidence_pct",
]


# -----------------------------
# Concept Buckets for Mining
# -----------------------------

# Organized keywords into semantic categories for systematic mining
CONCEPTS: Dict[str, List[str]] = {
    "OS": [
        # Desktop/Server Operating Systems
        "windows", "win32", "win64",
        "linux", "ubuntu", "debian", "fedora", "centos", "rhel", "arch", "alpine", "manjaro",
        "macos", "osx", "os x", "darwin",
        "unix", "posix",
        # BSD variants
        "freebsd", "openbsd", "netbsd", "dragonflybsd",
        # Other Unix-like systems
        "solaris", "illumos", "aix", "hp-ux",
        # Compatibility layers
        "wsl", "cygwin", "msys", "msys2", "mingw", "mingw32", "mingw64",
    ],
    "FIX": [
        # Fix/bug terminology
        "fix", "fixes", "fixed", "bug", "bugfix", "regression",
        "broken", "breakage", "failing", "fail", "fails", "failure",
        "unbreak", "workaround",
        # Explicit portability context
        "portable", "portability", "cross-platform", "compatibility",
        # Test control patterns (OS-specific test handling)
        "skip", "xfail", "skipif", "pytest.skip", "pytest.mark.skipif", "mark.skipif",
    ],
    "TEST_CI": [
        # Testing frameworks
        "test", "tests", "pytest", "unittest", "nose", "tox", "nox",
        # CI/CD platforms
        "ci", "workflow", "matrix", "runs-on",
        "github actions", "gha", "appveyor", "travis", "azure pipelines", "azure-devops",
    ],
    "CAUSE": [
        # Common OS-specific failure causes
        "line ending", "newline", "crlf", "lf", "carriage return",
        "path separator", "backslash", "slash",
        "case sensitive", "case insensitive",
        "encoding", "utf-8", "latin-1", "cp1252", "locale",
        "timezone", "time zone", "dst",
        "permission denied", "executable", "chmod", "symlink",
        "o_text", "o_binary", "pathext", ".dll", ".so", "dynamic library",
    ],
    "API": [
        # Platform detection APIs
        "sys.platform", "os.name", "platform.system", "platform.release",
        # Path handling APIs
        "os.sep", "os.path", "pathlib", "ntpath", "posixpath",
        # Subprocess/encoding APIs
        "subprocess", "encoding=", "newline=", "errors=", "universal_newlines",
    ],
}


# -----------------------------
# Keyword Matching Logic
# -----------------------------

def compile_keyword_regexes(keywords: List[str]) -> List[Tuple[str, re.Pattern]]:
    """
    Compile keyword patterns with word boundary protection.
    
    Strategy:
    - For alphanumeric keywords: add word boundaries to avoid substring matches
      (e.g., 'arch' won't match 'search')
    - For keywords with special chars: preserve literal matching
      (e.g., '.dll' matches 'file.dll')
    """
    pairs: List[Tuple[str, re.Pattern]] = []
    for kw in keywords:
        starts_with_alnum = kw[:1].isalnum()
        ends_with_alnum = kw[-1:].isalnum()
        left = r"(?<![A-Za-z0-9_])" if starts_with_alnum else ""
        right = r"(?![A-Za-z0-9_])" if ends_with_alnum else ""
        pattern = f"{left}{re.escape(kw)}{right}"
        pairs.append((kw, re.compile(pattern, re.IGNORECASE)))
    return pairs


# Special handling for "nt" (Windows OS name): only match when quoted or standalone
# to avoid false positives (e.g., "important", "content")
NT_QUOTED_RE = re.compile(r'"nt"', re.IGNORECASE)
NT_STANDALONE_RE = re.compile(r'(?<!\S)nt(?!\S)', re.IGNORECASE)

# Pre-compile all concept patterns for efficiency
COMPILED_CONCEPTS: Dict[str, List[Tuple[str, re.Pattern]]] = {
    name: compile_keyword_regexes(kws)
    for name, kws in CONCEPTS.items()
}


def match_concepts(text: str) -> Dict[str, List[str]]:
    """
    Match concept keywords in text and return hits organized by category.
    
    Returns:
        Dict mapping category names to lists of matched keywords
    """
    hits: Dict[str, List[str]] = {}
    if not text:
        return hits
    
    for name, pairs in COMPILED_CONCEPTS.items():
        found: List[str] = []
        for kw, rx in pairs:
            if rx.search(text):
                found.append(kw)
        if found:
            hits[name] = sorted(set(found))
    
    # Special case: add "nt" to OS category only when properly delimited
    if NT_QUOTED_RE.search(text) or NT_STANDALONE_RE.search(text):
        hits.setdefault("OS", []).append("nt")
        hits["OS"] = sorted(set(hits["OS"]))
    
    return hits


def has_os_and_fix(hits: Dict[str, List[str]]) -> bool:
    """Check if both OS and FIX concepts are present."""
    return bool(hits.get("OS")) and bool(hits.get("FIX"))


def sentence_level_cooccurrence(text: str) -> bool:
    """
    Proximity gating: Check if OS and FIX keywords co-occur in the same sentence/line.
    
    This is critical for reducing false positives by ensuring the keywords
    appear in close proximity, not just anywhere in the document.
    """
    if not text:
        return False
    for frag in re.split(r"[\.!?\n]", text):
        if not frag:
            continue
        if has_os_and_fix(match_concepts(frag)):
            return True
    return False


def format_concept_hits(hits: Dict[str, List[str]]) -> str:
    """Format concept hits for CSV output (e.g., 'OS=windows|linux; FIX=bug|fix')."""
    order = ["OS", "FIX", "TEST_CI", "CAUSE", "API"]
    parts: List[str] = []
    for key in order:
        if key in hits and hits[key]:
            parts.append(f"{key}=" + "|".join(hits[key]))
    # Include any additional categories
    for key in sorted(hits.keys()):
        if key not in order and hits[key]:
            parts.append(f"{key}=" + "|".join(hits[key]))
    return "; ".join(parts)


# -----------------------------
# GitHub API Helpers
# -----------------------------

def sanitize_repo(owner_repo: str) -> str:
    """Convert owner/repo to filesystem-safe name."""
    return owner_repo.replace("/", "_")


def get_cache_paths(owner_repo: str) -> Tuple[str, str]:
    """Get cache directory and file paths for a repository."""
    base = os.path.join("cache", "issues", sanitize_repo(owner_repo))
    return base, os.path.join(base, "issues.jsonl")


def load_repo_cache(owner_repo: str) -> Optional[List[Dict]]:
    """Load cached issue data for a repository if available."""
    try:
        cache_dir, cache_file = get_cache_paths(owner_repo)
        if not os.path.exists(cache_file) or os.path.getsize(cache_file) == 0:
            return None
        records: List[Dict] = []
        with open(cache_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
        return records or None
    except Exception:
        return None


def save_repo_cache(owner_repo: str, records: List[Dict]) -> None:
    """Save issue data to cache for future runs."""
    try:
        cache_dir, cache_file = get_cache_paths(owner_repo)
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False))
                f.write("\n")
    except Exception:
        pass


def read_input_csv(path: str) -> List[str]:
    """
    Read repository list from CSV.
    
    Accepts:
    - owner/repo format
    - Full GitHub URLs (https://github.com/owner/repo)
    """
    repos: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            cell = row[0].strip()
            if not cell:
                continue
            if cell.startswith("http"):
                parts = cell.split("github.com/")
                if len(parts) == 2:
                    rest = parts[1].strip("/")
                    owner_repo = "/".join(rest.split("/")[:2])
                    repos.append(owner_repo)
            else:
                repos.append(cell)
    return repos


def ensure_output_with_header(path: str) -> None:
    """Ensure output CSV exists with proper header."""
    needs_header = True
    if os.path.exists(path):
        try:
            needs_header = os.path.getsize(path) == 0
        except OSError:
            needs_header = True
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if needs_header:
            writer.writeheader()


def append_rows(path: str, rows: Iterable[Dict]) -> None:
    """Append result rows to output CSV."""
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        for row in rows:
            for k in FIELDNAMES:
                row.setdefault(k, "")
            writer.writerow(row)


def read_token_from_file() -> Optional[str]:
    """
    Read GitHub token from local files (for convenience).
    
    Checks for: token.txt, .github_token, .token in current and script directories.
    """
    candidates = ["token.txt", ".github_token", ".token"]
    locations = [os.getcwd(), os.path.dirname(__file__)]
    for loc in locations:
        for name in candidates:
            path = os.path.join(loc, name)
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        token = f.read().strip()
                        if token:
                            return token
            except OSError:
                continue
    return None


def read_openai_token() -> Optional[str]:
    """
    Read OpenAI API key from environment or local files.
    
    Checks: OPENAI_API_KEY, OPENAI_KEY, OPENAI_TOKEN environment variables,
            then openai.key, .openai_key, .openai_token files.
    """
    candidates = [
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("OPENAI_KEY"),
        os.environ.get("OPENAI_TOKEN"),
    ]
    for c in candidates:
        if c:
            return c.strip()
    # Fallback to local files
    for loc in [os.getcwd(), os.path.dirname(__file__)]:
        for name in ["openai.key", ".openai_key", ".openai_token"]:
            path = os.path.join(loc, name)
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        token = f.read().strip()
                        if token:
                            return token
            except OSError:
                continue
    return None


def get_github_headers(token: Optional[str]) -> Dict[str, str]:
    """Construct GitHub API request headers."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_request(method: str, url: str, *, token: Optional[str], 
                   params: Optional[Dict[str, str]] = None, 
                   request_counter: Optional[List[int]] = None) -> requests.Response:
    """
    Make GitHub API request with automatic retry and rate limit handling.
    """
    headers = get_github_headers(token)
    backoff = 2.0
    
    for _ in range(6):
        if request_counter is not None:
            request_counter[0] += 1
        try:
            GLOBAL_REQUEST_COUNTER[0] += 1
        except Exception:
            pass
        
        resp = requests.request(method, url, headers=headers, params=params)
        
        # Handle rate limiting
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
            wait_s = max(0, reset_ts - int(time.time()) + 2)
            print(f"[rate-limit] Waiting {wait_s}s...", file=sys.stderr)
            time.sleep(wait_s)
            continue
        
        if 200 <= resp.status_code < 300:
            return resp
        
        # Exponential backoff for other errors
        time.sleep(backoff)
        backoff = min(backoff * 2.0, 60.0)
    
    raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")


def paginated_get(url: str, *, token: Optional[str], 
                  params: Optional[Dict[str, str]] = None, 
                  request_counter: Optional[List[int]] = None) -> Iterable[Dict]:
    """
    Fetch paginated results from GitHub API.
    
    Yields individual items from paginated API responses.
    """
    page = 1
    while True:
        merged_params = dict(params or {})
        merged_params.update({"per_page": 100, "page": page})
        resp = github_request("GET", url, token=token, params=merged_params, 
                            request_counter=request_counter)
        items = resp.json()
        if not isinstance(items, list):
            items = items.get("items", [])
        if not items:
            break
        for it in items:
            yield it
        page += 1


# -----------------------------
# LLM Validation (Optional)
# -----------------------------

def build_ai_prompt(owner_repo: str, issue_number: int, title: str, 
                   body: str, comments: List[str]) -> str:
    """
    Construct prompt for LLM validation of OS-portability relevance.
    
    The LLM is used as a quality gate to validate that keyword matches
    truly represent OS-portability issues.
    """
    context = {
        "repo": owner_repo,
        "issue_number": issue_number,
        "title": title or "",
        "body": (body or "")[:8000],  # Limit length for API constraints
        "comments": [c[:2000] for c in comments][:10],
    }
    instructions = (
        "You are an expert triaging GitHub issues for OS-dependent test failures and portability fixes.\n"
        "Given the issue content below, answer strictly in JSON with these keys: \n"
        "- ai_issue_summary: a 3-10 word summary of the issue (no punctuation except spaces). "
        "If not portability, briefly say what it is instead.\n"
        "- ai_is_os_portability: 'Yes' or 'No' (is this about OS portability / tests failing "
        "on one OS and not others, or OS-specific behavior)\n"
        "- ai_is_fix_merged: 'Yes' or 'No' (based on the text, has a fix been merged/resolved; "
        "if unclear, answer 'No')\n"
        "- ai_confidence_pct: integer 0-100 for your confidence in 'ai_is_os_portability'\n"
        "Respond with ONLY a single-line JSON object.\n"
    )
    return instructions + "\nINPUT:\n" + json.dumps(context, ensure_ascii=False)


def call_openai_analyze(token: str, model: str, prompt: str, *, 
                       logs_dir: Optional[str] = None, 
                       log_name: Optional[str] = None) -> Dict[str, str]:
    """
    Call OpenAI API for LLM-based validation.
    
    Returns structured analysis results including confidence scores.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    def _request(payload: Dict) -> requests.Response:
        return requests.post(url, headers=headers, json=payload, timeout=60)

    # Prepare logging
    log_path: Optional[str] = None
    if logs_dir and log_name:
        try:
            os.makedirs(logs_dir, exist_ok=True)
            log_path = os.path.join(logs_dir, log_name)
        except Exception:
            log_path = None

    def _append_log(text: str) -> None:
        if not log_path:
            return
        try:
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(text)
                if not text.endswith("\n"):
                    lf.write("\n")
        except Exception:
            pass

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a careful assistant that outputs strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    _append_log("--- BEGIN REQUEST ---")
    _append_log(f"model={model}")
    _append_log("PROMPT:\n" + prompt)
    
    resp = _request(payload)
    
    _append_log("--- BEGIN RESPONSE ---")
    _append_log(f"HTTP {resp.status_code}")
    _append_log((resp.text or "")[:5000])
    _append_log("--- END RESPONSE ---")

    if resp.status_code >= 300:
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()

    # Parse JSON response
    try:
        parsed = json.loads(text)
        # Enforce word limit on summary
        raw_summary = str(parsed.get("ai_issue_summary", "")).strip()
        words = [w for w in raw_summary.split() if w]
        summary_10 = " ".join(words[:10])
        
        out = {
            "ai_issue_summary": summary_10,
            "ai_is_os_portability": "Yes" if str(parsed.get("ai_is_os_portability", "No")).strip().lower().startswith("y") else "No",
            "ai_is_fix_merged": "Yes" if str(parsed.get("ai_is_fix_merged", "No")).strip().lower().startswith("y") else "No",
            "ai_confidence_pct": (lambda v: str(min(100, max(0, v))))(
                (lambda s: int(s) if s.isdigit() else 0)(str(parsed.get("ai_confidence_pct", "0")).strip())
            ),
        }
        _append_log("--- PARSED ---")
        _append_log(json.dumps(out, ensure_ascii=False))
        _append_log("--- END REQUEST ---")
        return out
    except Exception:
        # Return conservative defaults on parse failure
        fallback = {
            "ai_issue_summary": "",
            "ai_is_os_portability": "No",
            "ai_is_fix_merged": "No",
            "ai_confidence_pct": "0",
        }
        _append_log("--- PARSED (FALLBACK) ---")
        _append_log(json.dumps(fallback, ensure_ascii=False))
        _append_log("--- END REQUEST ---")
        return fallback


# -----------------------------
# Issue Scanning Logic
# -----------------------------

def sentence_level_artifact_scan(owner_repo: str, detail: Dict, *, 
                                preloaded_comments: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Scan issue for OS-portability keywords with proximity gating.
    
    Two-phase filtering:
    1. Check title/body first (fast path)
    2. If no match, check including comments (complete path)
    
    Returns enrichment data if issue passes filters, None otherwise.
    """
    # Phase 1: Quick check with title/body only
    text_blobs_tb: List[Tuple[str, str]] = [
        ("title", detail.get("title") or ""), 
        ("body", detail.get("body") or "")
    ]
    aggregated_hits_tb: Dict[str, List[str]] = {}
    source_parts_tb: List[str] = []
    local_ok_tb = False
    
    for source, text in text_blobs_tb:
        hits = match_concepts(text)
        if hits:
            for k, vals in hits.items():
                aggregated_hits_tb.setdefault(k, []).extend(vals)
            source_parts_tb.append(source)
        if not local_ok_tb and sentence_level_cooccurrence(text):
            local_ok_tb = True

    # If title/body already passes filters, return early
    if aggregated_hits_tb and local_ok_tb and has_os_and_fix({k: sorted(set(v)) for k, v in aggregated_hits_tb.items()}):
        dedup_hits = {k: sorted(set(v)) for k, v in aggregated_hits_tb.items()}
        enrichment_input = {
            "title": detail.get("title") or "",
            "body": detail.get("body") or "",
            "comments": [],
        }
        return {
            "source": "+".join(sorted(set(source_parts_tb))) or "title",
            "keyword": format_concept_hits(dedup_hits),
            "enrichment_input": enrichment_input,
        }

    # Phase 2: Check including comments
    text_blobs: List[Tuple[str, str]] = []
    text_blobs.extend(text_blobs_tb)
    for body in (preloaded_comments or []):
        text_blobs.append(("comment", body or ""))

    aggregated_hits: Dict[str, List[str]] = dict(aggregated_hits_tb)
    source_parts: List[str] = list(source_parts_tb)
    local_ok = local_ok_tb
    
    for source, text in text_blobs[2:]:  # Only new comments
        hits = match_concepts(text)
        if hits:
            for k, vals in hits.items():
                aggregated_hits.setdefault(k, []).extend(vals)
            source_parts.append(source)
        if not local_ok and sentence_level_cooccurrence(text):
            local_ok = True

    # Final filtering
    if not aggregated_hits or not local_ok or not has_os_and_fix({k: sorted(set(v)) for k, v in aggregated_hits.items()}):
        return None

    dedup_hits = {k: sorted(set(v)) for k, v in aggregated_hits.items()}
    comments_only = [c for s, c in text_blobs if s == "comment"]
    enrichment_input = {
        "title": detail.get("title") or "",
        "body": detail.get("body") or "",
        "comments": comments_only,
    }
    return {
        "source": "+".join(sorted(set(source_parts))) or "title",
        "keyword": format_concept_hits(dedup_hits),
        "enrichment_input": enrichment_input,
    }


def process_repo(owner_repo: str, token: Optional[str], *, 
                ai_token: Optional[str], ai_model: str, 
                max_issues: int, since_iso: Optional[str], 
                fetch_comments: bool, always_fetch_comments: bool, 
                max_comments: int) -> Tuple[List[Dict], int, int, int]:
    """
    Process a single repository: fetch issues, apply filters, optionally validate with LLM.
    
    Returns:
        Tuple of (result_rows, ai_calls_count, ai_errors_count, github_requests_count)
    """
    out: List[Dict] = []
    ai_calls = 0
    ai_errors = 0
    gh_requests = 0
    request_counter: List[int] = [0]
    
    try:
        # Try cache first
        cached = load_repo_cache(owner_repo)
        if cached is None:
            # Fetch from GitHub API
            base_url = f"{GITHUB_API_BASE}/repos/{owner_repo}/issues"
            list_params = {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100}
            fetched_records: List[Dict] = []
            
            for detail in paginated_get(base_url, token=token, params=list_params, 
                                       request_counter=request_counter):
                # Skip pull requests (GitHub API returns both)
                if "pull_request" in detail:
                    continue
                
                # Fetch comments for each issue
                comments_bodies: List[str] = []
                if detail.get("comments", 0) > 0 and detail.get("comments_url"):
                    comments_json = list(paginated_get(detail.get("comments_url"), 
                                                      token=token, params=None, 
                                                      request_counter=request_counter))
                    comments_bodies = [(c.get("body") or "") for c in comments_json]
                
                fetched_records.append({
                    "issue": detail,
                    "comments": comments_bodies,
                })
            
            save_repo_cache(owner_repo, fetched_records)
            records = fetched_records
        else:
            records = cached

        # Process each issue
        count_issues = 0
        for rec in records:
            detail = rec.get("issue") or {}
            
            # Skip pull requests
            if "pull_request" in detail:
                continue
            
            preloaded_comments: Optional[List[str]] = rec.get("comments") if isinstance(rec.get("comments"), list) else []
            
            # Apply keyword and proximity filters
            enriched = sentence_level_artifact_scan(owner_repo, detail, 
                                                   preloaded_comments=preloaded_comments)
            if not enriched:
                continue
            
            # Optional: LLM validation for quality assurance
            ai_fields = {"ai_issue_summary": "", "ai_is_os_portability": "", 
                        "ai_is_fix_merged": "", "ai_confidence_pct": ""}
            if ai_token:
                try:
                    prompt = build_ai_prompt(owner_repo, int(detail.get("number")), 
                                           enriched["enrichment_input"]["title"], 
                                           enriched["enrichment_input"]["body"], 
                                           enriched["enrichment_input"]["comments"])
                    safe_repo = owner_repo.replace("/", "_")
                    log_name = f"{safe_repo}_issue_{detail.get('number')}.log"
                    ai_fields = call_openai_analyze(ai_token, ai_model, prompt, 
                                                   logs_dir="logs", log_name=log_name)
                    ai_calls += 1
                except Exception as e:
                    print(f"[ai-error] {owner_repo}#{detail.get('number')}: {e}", file=sys.stderr)
                    ai_errors += 1
            
            # Construct result row
            out.append({
                "repository": owner_repo,
                "type": "Issue",
                "source": enriched["source"],
                "keyword": enriched["keyword"],
                "summary": (detail.get("title") or "").strip()[:180],
                "link": detail.get("html_url"),
                "status": "To review",
                "number": detail.get("number"),
                "created_at": detail.get("created_at"),
                "author": (detail.get("user") or {}).get("login"),
                "labels": ",".join([lb.get("name", "") for lb in (detail.get("labels") or [])]),
                **ai_fields,
            })
            count_issues += 1
            
    except Exception as e:
        print(f"[error] {owner_repo}: {e}", file=sys.stderr)
    
    gh_requests = request_counter[0]
    return out, ai_calls, ai_errors, gh_requests


# -----------------------------
# Main Entry Point
# -----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mine GitHub Issues for OS-portability problems (multithreaded with optional LLM validation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with GitHub token only
  python mining_issues_script.py --input repos.csv --output results.csv --token ghp_xxxxx

  # With LLM validation for quality assurance
  python mining_issues_script.py --input repos.csv --output results.csv \\
    --token ghp_xxxxx --openai-token sk-xxxxx --openai-model gpt-4o-mini

  # Higher parallelism for large-scale mining
  python mining_issues_script.py --input repos.csv --output results.csv \\
    --token ghp_xxxxx --workers 16

Note: API tokens can also be provided via environment variables (GITHUB_TOKEN, OPENAI_API_KEY)
      or local files (token.txt, openai.key). See script documentation for details.
"""
    )
    
    parser.add_argument("--input", default="all.csv", 
                       help="Input CSV with owner/repo or full GitHub URLs (one per line)")
    parser.add_argument("--output", default="findings_online.csv", 
                       help="Output CSV path for results")
    parser.add_argument("--token", default="", 
                       help="GitHub API token (or use env: GITHUB_TOKEN/GH_TOKEN/GH_PAT)")
    parser.add_argument("--workers", type=int, default=8, 
                       help="Number of parallel worker threads (default: 8)")
    parser.add_argument("--openai-model", default="gpt-4o-mini", 
                       help="OpenAI model for validation (default: gpt-4o-mini)")
    parser.add_argument("--openai-token", default="", 
                       help="OpenAI API key for validation (optional; or use env: OPENAI_API_KEY)")
    
    args = parser.parse_args()

    # Resolve GitHub token from multiple sources
    token = (
        args.token
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GH_PAT")
        or read_token_from_file()
        or ""
    )
    if not token:
        print("[warn] No GitHub token provided; you will hit low rate limits.", file=sys.stderr)
        print("[warn] Obtain a token at: https://github.com/settings/tokens", file=sys.stderr)

    # Read repository list
    repos = read_input_csv(args.input)
    if not repos:
        print("[info] No repositories found in input.", file=sys.stderr)
        return

    ensure_output_with_header(args.output)

    # Resolve OpenAI token (optional)
    ai_token = args.openai_token or read_openai_token()
    ai_model = args.openai_model
    total_rows = 0

    print(f"[start] Scanning {len(repos)} repositories with {args.workers} workers ...")
    if ai_token:
        print(f"[start] LLM validation enabled with model: {ai_model}")
    else:
        print(f"[start] LLM validation disabled (no OpenAI token provided)")
    
    # Process repositories in parallel
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_to_repo = {
            executor.submit(
                process_repo,
                repo,
                token,
                ai_token=ai_token,
                ai_model=ai_model,
                max_issues=0,
                since_iso=None,
                fetch_comments=True,
                always_fetch_comments=True,
                max_comments=-1,
            ): repo
            for repo in repos
        }
        
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            rows: List[Dict] = []
            ai_calls = 0
            ai_errors = 0
            gh_requests = 0
            
            try:
                rows, ai_calls, ai_errors, gh_requests = future.result()
            except Exception as exc:
                print(f"[error] {repo}: {exc}", file=sys.stderr)
                rows = []
            
            append_rows(args.output, rows)
            total_rows += len(rows)
            
            # Progress reporting
            print(f"[done] {repo}: wrote {len(rows)} rows | "
                  f"ai_calls={ai_calls} ai_errors={ai_errors} github_requests={gh_requests}")

    print(f"\n[finish] Total rows written: {total_rows}")
    print(f"[finish] Output: {args.output}")
    print(f"[finish] Total GitHub API requests: {GLOBAL_REQUEST_COUNTER[0]}")


if __name__ == "__main__":
    main()

