import { ref } from 'vue'

import { http } from '@/api/client'

const ALLOWED = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_BYTES = 10 * 1024 * 1024

export interface UploadResult {
  url: string
  thumb_url: string
}

/** 图片上传：前端先做一次类型与体积校验，服务端仍会二次校验魔数。 */
export function useUpload() {
  const uploading = ref(false)
  const error = ref('')

  async function upload(file: File): Promise<UploadResult | null> {
    error.value = ''
    if (!ALLOWED.includes(file.type)) {
      error.value = '仅支持 JPG、PNG、GIF、WebP 图片'
      return null
    }
    if (file.size > MAX_BYTES) {
      error.value = '图片大小不能超过 10MB'
      return null
    }

    uploading.value = true
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await http.post<UploadResult>('/upload', form)
      return data
    } catch (err) {
      error.value = (err as Error).message
      return null
    } finally {
      uploading.value = false
    }
  }

  return { uploading, error, upload }
}
