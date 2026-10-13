---
name: github-explorer
description: >
  Deep-dive analysis of GitHub projects. Use when the user mentions a GitHub repo/project name
  and wants to understand it — triggered by phrases like "help me look at this project", "learn about XXX",
  "what is this project like", "analyze this repo", or any request to explore/evaluate a GitHub project.
  Covers architecture, community health, competitive landscape, and cross-platform knowledge sources.
---

# GitHub Explorer — In-Depth Project Analysis

> **Philosophy**: The README is only the storefront; the real value lies in Issues, Commits, and community discussions.

## Workflow

```
[Project name] → [1. Locate Repo] → [2. Gather Multiple Sources] → [3. Analyze and Assess] → [4. Structured Output]
```

### Phase 1: Locate Repo

- Use `web_search` to search `site:github.com <project_name>` and confirm the full org/repo
- Use an available search tool to find additional community links and non-GitHub resources with queries such as `<project_name> review` and `<project_name> 评测 使用体验`.
- Use `web_fetch` to fetch the repo homepage for basic information (README, Stars, Forks, License, last update)

### Phase 2: Gather Multiple Sources (In Parallel)

Check the following sources **as needed**; collect what exists and skip what does not:

| Source | URL pattern | What to collect | Suggested tool |
|---|---|---|---|
| GitHub Repo | `github.com/{org}/{repo}` | README, About, Contributors | `web_fetch` |
| GitHub Issues | `github.com/{org}/{repo}/issues?q=sort:comments` | Top 3-5 high-quality Issues | `browser` |
| Chinese-language communities | WeChat / Zhihu / Xiaohongshu | In-depth reviews, usage experiences | Available platform tool or `browser` |
| Technical blogs | Medium / Dev.to | Technical architecture analyses | `web_fetch` / `browser` |
| Discussion forums | V2EX / Reddit | User feedback, complaints | Available search or platform tool |

#### Search Tools and Queries

This repository does not include the `search-layer` or `content-extract` skills or their scripts. `web_search`, `web_fetch`, and `browser` mean the corresponding capabilities in the current environment; use the tool names actually available. If enhancement skills are separately installed, read their own instructions and confirm dependencies and invocation paths first. Otherwise, run the following searches directly without those scripts.

| Scenario | Example queries | Notes |
|------|------|------|
| **Project research (default)** | `<project> review`, `<project> 评测` | Cross-check independent sources |
| **Latest developments** | `<project> latest release` | Check the official release page and dates |
| **Competitor comparison** | `<project> vs <competitor>`, `<project> alternatives` | Verify differences and applicable conditions |
| **Quick link lookup** | `<project> official docs` | Confirm the official domain |
| **Community discussion** | `<project> discussion experience`, restricted to community domains | Distinguish user experiences from verified facts |

If a source or enhancement tool fails, continue with available sources and state the coverage limitations in the report. Without search capability, analyze only the readable repository and user-provided material; do not claim that community research was completed.

---

### Extraction Fallback and Upgrade Protocol (Extraction Upgrade)

In these situations, switch to an available browser or platform reader, or use an installed content-extraction skill:
1. **Restricted domains**: `mp.weixin.qq.com`, `zhihu.com`, `xiaohongshu.com`.
2. **Complex structure**: The page contains many formulas (LaTeX), complex tables, or extremely messy Markdown returned by `web_fetch`.
3. **Missing content**: Anti-scraping defenses cause `web_fetch` to return empty content or a challenge page.

If reading still fails, retain the URL, mark it as "Could not read," and seek independent sources. Do not treat search snippets as full text that was read, or count inaccessible discussions as verified evidence.

### Phase 3: Analyze and Assess

Make judgments based on the collected data:

- **Project stage**: Early experiment / rapid growth / mature and stable / maintenance mode / stalled, based on commit frequency and content
- **Featured Issue criteria**: Many comments, maintainer participation, exposure of architectural problems, or valuable technical discussion
- **Competitor identification**: Extract from README "Comparison"/"Alternatives" sections, Issues discussions, and web searches

### Phase 4: Structured Output

Follow the template below strictly, translating its headings, labels, and status messages into the selected output language. **Every section must contain substantive content or explicitly say "Not found" in that language.**

#### Formatting Rules (Mandatory)

1. **The title must link to the GitHub repository** (format: `# [Project Name](https://github.com/org/repo)`, ensuring it is clickable)
2. **Put a blank line both before and after every heading** (end of previous section → blank line → heading → blank line → content, for clear visual separation)
3. **Telegram blank-line fix (mandatory)**: Telegram swallows blank lines after list items (lines starting with `-`). To fix this, insert a line containing a braille blank `⠀` (U+2800) between the end of the list and the next heading, as follows:
   ```
   - Last list item

   ⠀
   **Next heading**
   ```
   This ensures Telegram preserves the blank line before the heading when rendering.
2. **Make all headings bold** (emoji + bold text)
3. **Competitor comparisons must include links** (at least one of GitHub / official website / documentation)
4. **Community discussion must be specific**: Summarize concrete posts, tweets, or discussions and link to the originals. Do not write generalities such as "highly rated" or "very popular"; state who said what or which specific problem a post discussed
5. **Source traceability**: All external information cited should include the original link so readers can trace it to the source

```markdown
# [{Project Name}]({GitHub Repo URL})

**🎯 One-Sentence Positioning**

{What it is and what problem it solves}

**⚙️ Core Mechanism**

{Explain the technical principles / architecture in plain language, without copying the README. Include the key technology stack.}

**📊 Project Health**

- **Stars**: {Count}  |  **Forks**: {Count}  |  **License**: {Type}
- **Team / Author**: {Background}
- **Commit trend**: {Recent activity + assessment of project stage}
- **Latest developments**: {Summary of the latest important commits}

**🔥 Featured Issues**

{Top 3-5 high-quality Issues, each with a title, link, and key discussion points. State explicitly if there are no high-quality Issues.}

**✅ Suitable Use Cases**

{When to use it and which specific problems it solves}

**⚠️ Limitations**

{When to avoid it; known problems}

**🆚 Competitor Comparison**

{Compare projects in the same space and their differences. Every competitor must have a GitHub or official website link. Example format:}
- **vs [GraphRAG](https://github.com/microsoft/graphrag)** — Description of differences
- **vs [RAGFlow](https://github.com/infiniflow/ragflow)** — Description of differences

**🌐 Knowledge Graph**

- **DeepWiki**: {Link or "Not indexed"}
- **Zread.ai**: {Link or "Not indexed"}

**🎬 Demo**

{Live demo link or "None"}

**📄 Related Papers**

{arXiv link or "None"}

**📰 Community Discussion**

**X/Twitter**

{Summaries of specific tweets + links. Example format:}
- [@user](link): "What they specifically said..."
- [Discussion thread](link): The specific problem discussed...
{If nothing is found, state "No relevant discussion found"}

**Chinese-Language Communities**

{Specific post titles / content summaries + links. Example format:}
- [Zhihu: Post title](link) — What was discussed
- [V2EX: Post title](link) — What was discussed
{If nothing is found, state "No relevant discussion found"}

**💬 My Assessment**

{Subjective evaluation: whether it is worth the time, what experience level it suits, and how to use it}
```

## Execution Notes

- Prefer `web_search` + `web_fetch`, with browser as a fallback
- **Search enhancement**: Use available search sources; use extra skills only after confirming their installation and reading their instructions. One source failing must not block the main workflow; disclose insufficient coverage
- **Extraction fallback**: If `web_fetch` fails or returns incomplete content, switch to an available browser, platform reader, or installed extraction skill. If the content remains unreadable, mark it and seek other sources
- Collect different sources in parallel for efficiency
- All links must be real and accessible; do not invent URLs
- Follow the runtime product `Language` instruction for the report throughout the current product, including pauses and restarts. A requested language change applies to the next product. If no product language is assigned, follow explicit human language instructions or the user's language. Keep technical terms in English. The English skill source and template do not set the output language
- Leave language preference changes to the human-operated settings interface; do not edit saved language configuration or the current product's language state

## ⚠️ Output Self-Check (Mandatory Before Every Response)

Before sending a report, you **must check every item below**, and send it only when all pass:

- [ ] **Title link**: Uses `# [Project Name](GitHub URL)` and is clickable
- [ ] **Heading spacing**: A blank line before and after every bold heading (`**🎯 ...**`)
- [ ] **Telegram blank lines**: A braille blank `⠀` line between the end of each list block and the next heading, preventing Telegram from swallowing blank lines
- [ ] **Issue links**: Every featured Issue uses the full `[#number Title](full URL)` format
- [ ] **Competitor links**: Every competitor has `[Name](GitHub / official website URL)`
- [ ] **Community discussion links**: Every citation uses `[Source: Title](URL)`
- [ ] **No vague descriptions**: The community section contains no generalities such as "highly rated" or "very popular"
- [ ] **Source traceability**: All external citations include original links

## Dependencies

These names describe required capabilities and optional enhancements; they do not mean Autonomous-Company has installed or configured these tools:

| Dependency | Type | Purpose |
|------|------|------|
| `web_search` | Environment-provided tool | Search queries |
| `web_fetch` | Environment-provided tool | Web content retrieval |
| `browser` | Environment-provided tool | Dynamic page rendering (fallback) |
| `search-layer` | Optional skill, not bundled | Use for search enhancement only after separate installation and checking its instructions; otherwise use available search tools |
| `content-extract` | Optional skill, not bundled | Use for extraction only after separate installation and checking its instructions; otherwise use a browser or platform tool |
