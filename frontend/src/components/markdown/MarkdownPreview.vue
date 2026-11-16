<script setup lang="ts">
import hljs from 'highlight.js/lib/common'
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

/**
 * 唯一渲染管线：markdown-it + highlight.js + 逐行行号。
 * 不注册公式与图表插件，正文中的 $$ / ```mermaid 按普通文本渲染。
 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code: string, lang: string): string {
    const language = lang && hljs.getLanguage(lang) ? lang : ''
    const highlighted = language
      ? hljs.highlight(code, { language, ignoreIllegals: true }).value
      : escapeHtml(code)

    const rows = highlighted.replace(/\n$/, '').split('\n')
    const body = rows
      .map((line, index) => `<span class="code-row" data-line="${index + 1}">${line || ' '}</span>`)
      .join('\n')

    return `<pre class="hljs"><code>${body}</code></pre>`
  },
})

md.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return self.renderToken(tokens, idx, options)
}

const html = computed(() => md.render(props.content || ''))
</script>

<template>
  <div class="md-body" v-html="html" />
</template>
