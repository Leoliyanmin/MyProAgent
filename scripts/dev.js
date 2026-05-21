#!/usr/bin/env node
/**
 * Development server starter
 * Starts Vite frontend, Local Backend, and Server Backend concurrently
 */
import { spawn } from 'child_process'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const rootDir = resolve(__dirname, '..')

const isWindows = process.platform === 'win32'

const services = [
  {
    name: 'VITE',
    color: '\x1b[34m',
    command: isWindows ? 'cmd' : 'npm',
    args: isWindows ? ['/c', 'npm', 'run', 'dev:frontend'] : ['run', 'dev:frontend'],
    cwd: resolve(rootDir, 'frontend')
  },
  {
    name: 'LOCAL',
    color: '\x1b[32m',
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8002']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8002'],
    cwd: resolve(rootDir, 'local_backend')
  },
  {
    name: 'SERVER',
    color: '\x1b[33m',
    command: isWindows ? 'cmd' : 'uvicorn',
    args: isWindows
      ? ['/c', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8001']
      : ['main:app', '--reload', '--host', '0.0.0.0', '--port', '8001'],
    cwd: resolve(rootDir, 'server_backend')
  }
]

const resetColor = '\x1b[0m'
const processes = []
let isShuttingDown = false

function log(name, color, message) {
  const prefix = `${color}[${name}]${resetColor}`
  const lines = message.toString().trim().split('\n')
  lines.forEach(line => {
    if (line.trim()) {
      console.log(`${prefix} ${line}`)
    }
  })
}

function killProcessTree(proc, signal) {
  if (!proc || proc.killed) return
  const pid = proc.pid
  if (!pid) return

  try {
    // Negative PID kills the entire process group (Unix only).
    // This is critical: uvicorn --reload spawns a watcher child process
    // that would otherwise become orphaned and hang the terminal.
    process.kill(-pid, signal)
  } catch (err) {
    if (err.code === 'ESRCH') return // already dead
    try { proc.kill(signal) } catch (_) { /* already dead */ }
  }
}

function startService(service) {
  return new Promise((resolve, reject) => {
    // detached: true on Unix creates a new process group via setsid(),
    // so killProcessTree(-pid) can clean up the entire subtree.
    // On Windows we fall back to shell: true for cmd.exe.
    const spawnOpts = {
      cwd: service.cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
      ...(isWindows ? { shell: true } : { detached: true })
    }

    const proc = spawn(service.command, service.args, spawnOpts)

    proc.stdout.on('data', (data) => { log(service.name, service.color, data) })
    proc.stderr.on('data', (data) => { log(service.name, service.color, data) })

    proc.on('error', (err) => {
      log(service.name, service.color, `Failed to start: ${err.message}`)
      reject(err)
    })

    proc.on('exit', (code) => {
      if (!isShuttingDown && code !== 0 && code !== null) {
        log(service.name, service.color, `Exited with code ${code}`)
        reject(new Error(`${service.name} exited with code ${code}`))
      }
    })

    processes.push(proc)
    setTimeout(() => resolve(proc), 1000)
  })
}

async function startAll() {
  console.log('🚀 Starting ProAgent development servers...\n')
  try {
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
  if (isShuttingDown) return
  isShuttingDown = true

  console.log('\n\n🛑 Stopping all services...')

  processes.forEach(p => killProcessTree(p, 'SIGTERM'))

  let exitedCount = 0
  processes.forEach(proc => {
    if (!proc || proc.killed) {
      exitedCount++
      return
    }
    proc.on('exit', () => {
      exitedCount++
      if (exitedCount >= processes.length) process.exit(0)
    })
  })

  const forceTimer = setTimeout(() => {
    console.log('⚠️  Force-killing remaining processes...')
    processes.forEach(p => killProcessTree(p, 'SIGKILL'))
    setTimeout(() => process.exit(0), 500)
  }, 3000)

  // Don't let timer keep event loop alive if all exited cleanly
  forceTimer.unref()

  if (exitedCount >= processes.length) process.exit(0)
}

process.on('SIGINT', stopAll)
process.on('SIGTERM', stopAll)

startAll()
