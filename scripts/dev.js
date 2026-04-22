#!/usr/bin/env node
/**
 * Development server starter
 * Starts Vite frontend, Local Backend, and Server Backend concurrently
 * Handles errors and stops all processes if any fails
 */
import { spawn } from 'child_process'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'
import readline from 'readline'

const __dirname = dirname(fileURLToPath(import.meta.url))
const rootDir = resolve(__dirname, '..')

// 检测操作系统
const isWindows = process.platform === 'win32'

const services = [
  {
    name: 'VITE',
    color: '\x1b[34m', // Blue
    command: isWindows ? 'cmd' : 'npm',
    args: isWindows ? ['/c', 'npm', 'run', 'dev:frontend'] : ['run', 'dev:frontend'],
    cwd: resolve(rootDir, 'frontend')
  },
  {
    name: 'LOCAL',
    color: '\x1b[32m', // Green
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows 
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8002']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8002'],
    cwd: resolve(rootDir, 'local_backend')
  },
  {
    name: 'SERVER',
    color: '\x1b[33m', // Yellow
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8001']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8001'],
    cwd: resolve(rootDir, 'server_backend')
  }
]

const resetColor = '\x1b[0m'
const processes = []

function log(name, color, message) {
  const prefix = `${color}[${name}]${resetColor}`
  const lines = message.toString().trim().split('\n')
  lines.forEach(line => {
    if (line.trim()) {
      console.log(`${prefix} ${line}`)
    }
  })
}

function startService(service) {
  return new Promise((resolve, reject) => {
    // 使用 shell: true 来解决环境变量问题
    const proc = spawn(service.command, service.args, {
      cwd: service.cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true  // 关键：启用 shell 模式
    })

    proc.stdout.on('data', (data) => {
      log(service.name, service.color, data)
    })

    proc.stderr.on('data', (data) => {
      log(service.name, service.color, data)
    })

    proc.on('error', (err) => {
      log(service.name, service.color, `Failed to start: ${err.message}`)
      reject(err)
    })

    proc.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        log(service.name, service.color, `Exited with code ${code}`)
        reject(new Error(`${service.name} exited with code ${code}`))
      }
    })

    processes.push(proc)
    
    // Give it a moment to start
    setTimeout(() => resolve(proc), 1000)
  })
}

async function startAll() {
  console.log('🚀 Starting ProAgent development servers...\n')

  try {
    // Start all services
    await Promise.all(services.map(startService))
    
    console.log('\n✅ All services started successfully!')
    console.log('   Frontend: http://localhost:5173')
    console.log('   Local:    http://localhost:8002')
    console.log('   Server:   http://localhost:8001')
    console.log('\nPress Ctrl+C to stop all services\n')

  } catch (err) {
    console.error('\n❌ Failed to start services:', err.message)
    stopAll()
    process.exit(1)
  }
}

function stopAll() {
  console.log('\n\n🛑 Stopping all services...')
  processes.forEach(proc => {
    if (proc && !proc.killed) {
      proc.kill('SIGTERM')
    }
  })
}

// Handle exit
process.on('SIGINT', () => {
  stopAll()
  setTimeout(() => process.exit(0), 500)
})

process.on('SIGTERM', () => {
  stopAll()
  setTimeout(() => process.exit(0), 500)
})

// Start
startAll()