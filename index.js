/**
 * dsh-search-pull — raise the agent's tendency to call the built-in `web_search`.
 *
 * One static prompt section, plus an optional audit trail. That is the whole
 * plugin, and it is deliberate:
 *
 *   - The section text never changes, so it never invalidates the cached
 *     prompt prefix. A per-turn dynamic contribution (a changing context line,
 *     or a fabricated user message) would toggle the prefix on every turn and
 *     re-bill the entire history as uncached input.
 *   - The wording carries the per-turn condition in prose instead ("若本轮尚未
 *     做任何检索…"), which costs a fixed ~100 characters and behaves the same
 *     for the model: it can see from the conversation whether it searched.
 *
 * `tools/execute` is observed only to write an audit line, so you can tell
 * whether the plugin is actually changing behaviour.
 */

import { appendFileSync } from 'node:fs'

export const name = 'dsh-search-pull'

export const inject = ['systemPrompt']

const DEFAULTS = {
  /** 'always' — install the section; 'off' — install nothing. */
  mode: 'always',
  /** Prompt-section sort order; higher lands later in the prompt. */
  order: 108,
  /** Ask for an explicit "未联网核对" label when nothing was searched. */
  requireUnverifiedLabel: true,
  /** Tool names counted as a search by the audit trail. */
  searchTools: ['web_search'],
  /** Replace the whole section text; null uses the generated one. */
  sectionText: null,
  /** Append a JSONL audit trail here; null disables it. */
  debugFile: null,
}

function buildSection(cfg) {
  const lines = [
    '## 调研优先（search-pull）',
    '',
    '- 遇到「怎么做 / 哪个更好 / 有没有现成方案 / 这个报错怎么修 / 某个库或 API 怎么用 / 现在是什么版本」这类问题，先调用 `web_search` 再动手。已有的开源实现优先复用，不要凭记忆重新推导。',
    '- 若本轮尚未做任何检索，回答这类问题前先搜一轮（1-3 次查询即可）。只涉及本工作区文件的读取、运行与修改时，不必联网。',
  ]
  if (cfg.requireUnverifiedLabel) {
    lines.push(
      '- 如果最终回答没有做任何联网核对，请在结论开头显式标注「未联网核对」，让用户知道这部分是凭记忆写的。',
    )
  }
  return lines.join('\n')
}

export function apply(ctx, config = {}) {
  const cfg = { ...DEFAULTS, ...(config ?? {}) }

  const trace = (event, data = {}) => {
    if (!cfg.debugFile) return
    try {
      appendFileSync(cfg.debugFile, `${JSON.stringify({ at: new Date().toISOString(), event, ...data })}\n`)
    } catch {
      // Auditing must never affect behaviour.
    }
  }

  if (cfg.mode === 'off') {
    trace('mount', { mode: 'off' })
    return
  }

  const sectionText = cfg.sectionText ?? buildSection(cfg)

  ctx.systemPrompt.section({
    name: 'dsh-search-pull:rule',
    order: cfg.order,
    text: sectionText,
  })

  // Audit only: never touches the prompt, so it cannot affect caching.
  ctx.on('tools/execute', (exec, next) => {
    try {
      if (cfg.searchTools.includes(exec?.name)) {
        trace('search-observed', { tool: exec.name, agent: String(exec.agent?.id ?? '') })
      }
    } catch (error) {
      trace('observe-failed', { error: String(error) })
    }
    return next()
  })

  trace('mount', { mode: cfg.mode, order: cfg.order, sectionChars: sectionText.length })
}
