#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;

struct BackendState {
    local_process: Arc<Mutex<Option<CommandChild>>>,
    server_process: Arc<Mutex<Option<CommandChild>>>,
}

fn spawn_backend(
    app: &tauri::AppHandle,
    name: &str,
    process_state: Arc<Mutex<Option<CommandChild>>>,
) -> Result<(), String> {
    use tauri_plugin_shell::ShellExt;
    
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
    
    std::thread::sleep(std::time::Duration::from_secs(1));
    
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
            let state = app.state::<BackendState>();
            
            match spawn_backend(&app.handle(), "python-backend", state.local_process.clone()) {
                Ok(_) => println!("Local backend started"),
                Err(e) => {
                    eprintln!("Local backend error: {}", e);
                    eprintln!("Run manually: cd local_backend && uvicorn main:app --host 0.0.0.0 --port 8002");
                }
            }
            
            std::thread::sleep(std::time::Duration::from_secs(1));
            
            match spawn_backend(&app.handle(), "server-backend", state.server_process.clone()) {
                Ok(_) => println!("Server backend started"),
                Err(e) => {
                    eprintln!("Server backend error: {}", e);
                    eprintln!("Run manually: cd server_backend && uvicorn main:app --host 0.0.0.0 --port 8001");
                }
            }
            
            std::thread::sleep(std::time::Duration::from_secs(2));
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![restart_backends])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
