// MSW Browser Setup
// This file configures MSW for browser environment

import { setupWorker } from 'msw/browser'
import { handlers } from './handlers.js'

export const worker = setupWorker(...handlers)
