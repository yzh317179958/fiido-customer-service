import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { deepClone } from '@/utils/deepClone'

type ThemeOption = 'light' | 'dark' | 'system'
type FontSizeOption = 'small' | 'medium' | 'large'
type DensityOption = 'compact' | 'standard' | 'comfortable'
type BubbleStyleOption = 'rounded' | 'flat'
type SendShortcut = 'enter' | 'ctrlenter'

export interface PersonalSettings {
  appearance: {
    theme: ThemeOption
    fontSize: FontSizeOption
    listDensity: DensityOption
    bubbleStyle: BubbleStyleOption
  }
  behavior: {
    sendShortcut: SendShortcut
    autoTakeover: boolean
    showMessagePreview: boolean
    autoLoadHistory: boolean
    sessionRefreshInterval: 10 | 30 | 60
  }
}

const STORAGE_KEY = 'fiido_agent_personal_settings_v1'

const defaultSettings: PersonalSettings = {
  appearance: {
    theme: 'system',
    fontSize: 'medium',
    listDensity: 'standard',
    bubbleStyle: 'rounded'
  },
  behavior: {
    sendShortcut: 'enter',
    autoTakeover: false,
    showMessagePreview: true,
    autoLoadHistory: true,
    sessionRefreshInterval: 30
  }
}

function mergeSettings(stored?: Partial<PersonalSettings>): PersonalSettings {
  if (!stored) {
    return deepClone(defaultSettings)
  }
  return {
    appearance: {
      ...defaultSettings.appearance,
      ...(stored.appearance || {})
    },
    behavior: {
      ...defaultSettings.behavior,
      ...(stored.behavior || {})
    }
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<PersonalSettings>(deepClone(defaultSettings))
  const initialized = ref(false)
  const systemTheme = ref<'light' | 'dark'>('light')
  let mediaQuery: MediaQueryList | null = null

  const resolvedTheme = computed(() => {
    const customTheme = settings.value.appearance.theme
    if (customTheme === 'system') {
      return systemTheme.value
    }
    return customTheme
  })

  function loadFromStorage(): PersonalSettings {
    if (typeof localStorage === 'undefined') {
      return deepClone(defaultSettings)
    }
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        return deepClone(defaultSettings)
      }
      const parsed = JSON.parse(raw) as Partial<PersonalSettings>
      return mergeSettings(parsed)
    } catch (error) {
      console.warn('⚠️ 读取个性化设置失败，已使用默认值', error)
      return deepClone(defaultSettings)
    }
  }

  function persistSettings() {
    if (typeof localStorage === 'undefined') {
      return
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings.value))
  }

  function applyTheme() {
    if (typeof document === 'undefined') return
    document.documentElement.dataset.agentTheme = resolvedTheme.value
  }

  function applyFontScale() {
    if (typeof document === 'undefined') return
    const map: Record<FontSizeOption, string> = {
      small: '0.95',
      medium: '1',
      large: '1.1'
    }
    document.documentElement.style.setProperty('--agent-font-scale', map[settings.value.appearance.fontSize])
  }

  function applyAppearance() {
    applyTheme()
    applyFontScale()
  }

  function init() {
    if (initialized.value) return
    settings.value = loadFromStorage()

    if (typeof window !== 'undefined') {
      mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      systemTheme.value = mediaQuery.matches ? 'dark' : 'light'
      mediaQuery.addEventListener('change', (event) => {
        systemTheme.value = event.matches ? 'dark' : 'light'
        applyTheme()
      })
    }

    watch(settings, () => {
      persistSettings()
      applyAppearance()
    }, { deep: true })

    applyAppearance()
    initialized.value = true
  }

  return {
    settings,
    resolvedTheme,
    init
  }
})
