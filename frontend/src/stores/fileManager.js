import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { agentAPI } from '../services/api.js'

export const useFileManagerStore = defineStore('fileManager', () => {
  const workingDirectory = ref(localStorage.getItem('file_manager_working_directory') || '')
  const currentRelativePath = ref('')
  const entries = ref([])
  const isLoading = ref(false)
  const error = ref('')

  const previewFile = ref(null)
  const previewContent = ref('')
  const previewLoading = ref(false)

  const isDirectorySet = computed(() => !!workingDirectory.value.trim())

  const breadcrumbs = computed(() => {
    const parts = currentRelativePath.value
      ? currentRelativePath.value.split('/').filter(Boolean)
      : []
    return [
      { name: '根目录', relativePath: '' },
      ...parts.map((name, i) => ({
        name,
        relativePath: parts.slice(0, i + 1).join('/'),
      })),
    ]
  })

  const directories = computed(() => entries.value.filter((e) => e.is_directory))
  const files = computed(() => entries.value.filter((e) => !e.is_directory))

  function _saveWorkingDirectory() {
    localStorage.setItem('file_manager_working_directory', workingDirectory.value)
  }

  async function setDirectory(path) {
    const trimmed = path.trim()
    if (!trimmed) {
      error.value = '请输入工作目录'
      return false
    }
    workingDirectory.value = trimmed
    currentRelativePath.value = ''
    _saveWorkingDirectory()
    return listFiles()
  }

  async function listFiles(relativePath) {
    if (!isDirectorySet.value) return
    isLoading.value = true
    error.value = ''
    try {
      const res = await agentAPI.listWorkingDirectory(
        workingDirectory.value,
        relativePath ?? currentRelativePath.value,
      )
      entries.value = res.entries || []
      currentRelativePath.value = res.relative_path || ''
      return res
    } catch (err) {
      error.value = err.message || '加载失败'
      entries.value = []
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function navigateToFolder(relativePath) {
    currentRelativePath.value = relativePath
    return listFiles(relativePath)
  }

  async function navigateUp() {
    if (!currentRelativePath.value) return
    const parts = currentRelativePath.value.split('/')
    parts.pop()
    const parent = parts.join('/')
    return navigateToFolder(parent)
  }

  async function createFile(filename) {
    if (!filename.trim()) throw new Error('文件名不能为空')
    const res = await agentAPI.createFileByName(
      workingDirectory.value,
      filename.trim(),
      currentRelativePath.value,
    )
    await listFiles()
    return res
  }

  async function renameFile(oldName, newName) {
    if (!oldName.trim() || !newName.trim()) throw new Error('文件名不能为空')
    const res = await agentAPI.renameFileByName(
      workingDirectory.value,
      oldName.trim(),
      newName.trim(),
      currentRelativePath.value,
    )
    await listFiles()
    return res
  }

  async function deleteFile(filename) {
    if (!filename.trim()) throw new Error('文件名不能为空')
    const res = await agentAPI.deleteFileByName(
      workingDirectory.value,
      filename.trim(),
      currentRelativePath.value,
    )
    await listFiles()
    return res
  }

  async function updateFile(filename, content) {
    if (!filename.trim()) throw new Error('文件名不能为空')
    const res = await agentAPI.updateFileByName(
      workingDirectory.value,
      filename.trim(),
      content,
      currentRelativePath.value,
    )
    if (previewFile.value && previewFile.value.name === filename.trim()) {
      previewContent.value = content
    }
    await listFiles()
    return res
  }

  async function openPreview(entry) {
    previewFile.value = entry
    previewContent.value = ''
    previewLoading.value = true
    try {
      const res = await agentAPI.readFileByName(
        workingDirectory.value,
        entry.name,
        currentRelativePath.value,
      )
      previewContent.value = res.content || ''
    } catch (err) {
      previewContent.value = `读取失败: ${err.message || '未知错误'}`
    } finally {
      previewLoading.value = false
    }
  }

  function closePreview() {
    previewFile.value = null
    previewContent.value = ''
  }

  async function init() {
    if (isDirectorySet.value) {
      await listFiles()
    }
  }

  return {
    workingDirectory,
    currentRelativePath,
    entries,
    isLoading,
    error,
    isDirectorySet,
    breadcrumbs,
    directories,
    files,
    previewFile,
    previewContent,
    previewLoading,
    setDirectory,
    listFiles,
    navigateToFolder,
    navigateUp,
    createFile,
    renameFile,
    deleteFile,
    updateFile,
    openPreview,
    closePreview,
    init,
  }
})