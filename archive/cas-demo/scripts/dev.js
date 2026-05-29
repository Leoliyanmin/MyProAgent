#!/usr/bin/env node
import { spawn } from 'child_process'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(__dirname, '../..')

const isWindows = process.platform === 'win32'

const services = [
  {
    name: 'LOCAL',
    color: '\x1b[32m',
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8002']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8002'],
    cwd: resolve(projectRoot, 'local_backend')
  },
  {
    name: 'SERVER',
    color: '\x1b[33m',
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8001']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8001'],
    cwd: resolve(projectRoot, 'server_backend')
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
    const proc = spawn(service.command, service.args, {
      cwd: service.cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true
    })

    proc.stdout.on('data', (data) => log(service.name, service.color, data))
    proc.stderr.on('data', (data) => log(service.name, service.color, data))

    proc.on('error', (err) => {
      log(service.name, service.color, `Failed to start: ${err.message}`)
      reject(err)
    })

    proc.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        log(service.name, service.color, `Exited with code ${code}`)
      }
    })

    processes.push(proc)
    setTimeout(() => resolve(proc), 1000)
  })
}

async function startAll() {
  console.log('🚀 Starting backends...\n')

  try {
    await Promise.all(services.map(startService))
    console.log('\n✅ Backends started!')
    console.log('   Local:    http://localhost:8002')
    console.log('   Server:   http://localhost:8001')
    console.log('\nPress Ctrl+C to stop\n')
  } catch (err) {
    console.error('\n❌ Failed to start backends:', err.message)
    stopAll()
    process.exit(1)
  }
}

function stopAll() {
  console.log('\n🛑 Stopping backends...')
  processes.forEach(proc => {
    if (proc && !proc.killed) proc.kill('SIGTERM')
  })
}

process.on('SIGINT', () => { stopAll(); setTimeout(() => process.exit(0), 500) })
process.on('SIGTERM', () => { stopAll(); setTimeout(() => process.exit(0), 500) })

startAll()