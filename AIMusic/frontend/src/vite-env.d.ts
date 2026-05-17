/// <reference types="vite/client" />

interface ElectronApi {
  isElectron: boolean
  platform: string
}

interface Window {
  electronAPI?: ElectronApi
}
