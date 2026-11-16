<script setup lang="ts">
import { markdown } from '@codemirror/lang-markdown'
import { languages } from '@codemirror/language-data'
import { EditorState } from '@codemirror/state'
import { EditorView } from '@codemirror/view'
import { basicSetup } from 'codemirror'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ modelValue: string; placeholder?: string }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const host = ref<HTMLDivElement | null>(null)
let view: EditorView | null = null

const theme = EditorView.theme({
  '&': {
    fontSize: '13.5px',
    backgroundColor: 'transparent',
    height: '100%',
  },
  '.cm-scroller': {
    fontFamily: '"JetBrains Mono", Consolas, monospace',
    lineHeight: '1.85',
    padding: '12px 4px',
  },
  '.cm-content': { caretColor: '#7F5539' },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    color: '#B4A99A',
    border: 'none',
  },
  '.cm-activeLine': { backgroundColor: 'rgba(176,137,104,0.06)' },
  '.cm-activeLineGutter': { backgroundColor: 'transparent' },
  '&.cm-focused': { outline: 'none' },
})

onMounted(() => {
  if (!host.value) return
  view = new EditorView({
    parent: host.value,
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [
        basicSetup,
        markdown({ codeLanguages: languages }),
        theme,
        EditorView.lineWrapping,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            emit('update:modelValue', update.state.doc.toString())
          }
        }),
      ],
    }),
  })
})

watch(
  () => props.modelValue,
  (value) => {
    if (!view) return
    if (value !== view.state.doc.toString()) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } })
    }
  },
)

onBeforeUnmount(() => {
  view?.destroy()
  view = null
})
</script>

<template>
  <div ref="host" class="h-full min-h-[320px] overflow-auto" />
</template>
