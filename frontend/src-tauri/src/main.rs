#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct BackendState {
    local_process: Arc<Mutex<Option<CommandChild>>>,
    server_process: Arc<Mutex<Option<CommandChild>>>,
}

async fn wait_for_backend(url: &str, timeout_secs: u64) -> Result<(), String> {
    let start = std::time::Instant::now();
    let client = reqwest::Client::new();
    
    while start.elapsed().as_secs() < timeout_secs {
        match client.get(url).timeout(Duration::from_secs(2)).send().await {
            Ok(resp) if resp.status().is_success() => {
                println!("Backend ready at {}", url);
                return Ok(());
            }
            _ => {
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        }
    }
    
    Err(format!("Backend at {} failed to start within {} seconds", url, timeout_secs))
}

fn spawn_backend(
    app: &tauri::AppHandle,
    name: &str,
    process_state: Arc<Mutex<Option<CommandChild>>>,
) -> Result<(), String> {
    let sidecar_name = format!("binaries/{}", name);
    let sidecar = app.shell()
        .sidecar(&sidecar_name)
        .map_err(|e| format!("Failed to create {} sidecar: {}", name, e))?;
    
    let (mut rx, child) = sidecar.spawn()
        .map_err(|e| format!("Failed to spawn {}: {}", name, e))?;
    
    *process_state.lock().unwrap() = Some(child);
    
    let name_clone = name.to_string();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    println!("[{}] {}", name_clone, String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    eprintln!("[{} err] {}", name_clone, String::from_utf8_lossy(&line));
                }
                _ => {}
            }
        }
    });
    
    Ok(())
}

#[tauri::command]
fn restart_backends(app: tauri::AppHandle) -> Result<String, String> {
    if cfg!(debug_assertions) {
        return Ok("Dev mode: backends managed by dev.js, restart manually".to_string());
    }
    
    let state = app.state::<BackendState>();
    
    if let Ok(mut process) = state.local_process.lock() {
        if let Some(mut child) = process.take() {
            let _ = child.write(b"sidecar shutdown\n");
        }
    }
    
    if let Ok(mut process) = state.server_process.lock() {
        if let Some(mut child) = process.take() {
            let _ = child.write(b"sidecar shutdown\n");
        }
    }
    
    std::thread::sleep(Duration::from_millis(500));
    
    let local_state = state.local_process.clone();
    spawn_backend(&app, "python-backend", local_state)?;
    
    let server_state = state.server_process.clone();
    spawn_backend(&app, "server-backend", server_state)?;
    
    Ok("Backends restarted".to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .manage(BackendState {
            local_process: Arc::new(Mutex::new(None)),
            server_process: Arc::new(Mutex::new(None)),
        })
        .setup(|app| {
            let app_handle = app.handle().clone();
            
            // In dev mode, backends are started by scripts/dev.js (beforeDevCommand)
            // Only spawn sidecars in production (release) builds
            if cfg!(debug_assertions) {
                println!("[ProAgent] Dev mode: backends started by dev.js, skipping sidecar spawn");
            } else {
                tauri::async_runtime::spawn(async move {
                    let state = app_handle.state::<BackendState>();
                    
                    match spawn_backend(&app_handle, "python-backend", state.local_process.clone()) {
                        Ok(_) => {
                            if let Err(e) = wait_for_backend("http://localhost:8002/health", 10).await {
                                eprintln!("Local backend failed to start: {}", e);
                            }
                        }
                        Err(e) => {
                            eprintln!("Local backend error: {}", e);
                        }
                    }
                    
                    match spawn_backend(&app_handle, "server-backend", state.server_process.clone()) {
                        Ok(_) => {
                            if let Err(e) = wait_for_backend("http://localhost:8001/health", 10).await {
                                eprintln!("Server backend failed to start: {}", e);
                            }
                        }
                        Err(e) => {
                            eprintln!("Server backend error: {}", e);
                        }
                    }
                });
            }
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![restart_backends])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
