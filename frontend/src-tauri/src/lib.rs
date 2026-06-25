use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use url::Url;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CookieInfo {
    name: String,
    value: String,
    domain: String,
    path: String,
    secure: bool,
    #[serde(rename = "httpOnly")]
    http_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BindResult {
    success: bool,
    message: String,
    data: Option<serde_json::Value>,
}

struct BackendState {
    local_process: Arc<Mutex<Option<CommandChild>>>,
    server_process: Arc<Mutex<Option<CommandChild>>>,
}

fn cookies_to_dict(cookies: &[CookieInfo], domain_filter: &str) -> serde_json::Value {
    let mut map = serde_json::Map::new();
    for c in cookies {
        if c.domain.contains(domain_filter) || (domain_filter.is_empty() && c.domain.is_empty()) {
            map.entry(c.name.clone()).or_insert(serde_json::Value::String(c.value.clone()));
        }
    }
    serde_json::Value::Object(map)
}

fn cookies_to_dict_multi(cookies: &[CookieInfo], domain_filters: &[&str]) -> serde_json::Value {
    let mut map = serde_json::Map::new();
    for c in cookies {
        let matches = domain_filters.iter().any(|f| c.domain.contains(f));
        if matches || (domain_filters.is_empty() && c.domain.is_empty()) {
            map.entry(c.name.clone()).or_insert(serde_json::Value::String(c.value.clone()));
        }
    }
    serde_json::Value::Object(map)
}

fn make_reqwest_client() -> Result<reqwest::Client, String> {
    reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(120))
        .connect_timeout(std::time::Duration::from_secs(10))
        .no_proxy()
        .build()
        .map_err(|e| format!("创建HTTP客户端失败: {}", e))
}

async fn check_backend_health(backend_url: &str) -> Result<(), String> {
    let client = make_reqwest_client()?;
    let health_url = format!("{}/health", backend_url.trim_end_matches('/'));
    let resp = client.get(&health_url).send().await.map_err(|e| {
        format!(
            "后端不可达 ({}): {}。请确认后端服务已启动",
            health_url, e
        )
    })?;
    if !resp.status().is_success() {
        return Err(format!("后端健康检查失败 ({}): HTTP {}", health_url, resp.status()));
    }
    Ok(())
}

#[tauri::command]
async fn open_cas_login(app: tauri::AppHandle, platform: Option<String>) -> Result<(), String> {
    let label = match platform.as_deref() {
        Some("blackboard") => "cas-login-bb",
        _ => "cas-login",
    };

    if let Some(window) = app.get_webview_window(label) {
        window.set_focus().map_err(|e| format!("Failed to focus window: {}", e))?;
        return Ok(());
    }

    let cas_url = match platform.as_deref() {
        Some("blackboard") => {
            "https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Fbb.sustech.edu.cn%2Fwebapps%2Flogin%2F"
        }
        _ => {
            "https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Ftis.sustech.edu.cn%2Fauthentication%2Fmain"
        }
    };

    let _window = WebviewWindowBuilder::new(&app, label, WebviewUrl::External(cas_url.parse().unwrap()))
        .title("SUSTech 统一认证登录")
        .inner_size(960.0, 720.0)
        .center()
        .build()
        .map_err(|e| format!("Failed to create window: {}", e))?;

    Ok(())
}

#[tauri::command]
async fn close_cas_window(app: tauri::AppHandle, platform: Option<String>) -> Result<(), String> {
    let label = match platform.as_deref() {
        Some("blackboard") => "cas-login-bb",
        _ => "cas-login",
    };

    if let Some(window) = app.get_webview_window(label) {
        window.close().map_err(|e| format!("Failed to close window: {}", e))?;
    }

    Ok(())
}

#[tauri::command]
async fn navigate_cas_window(app: tauri::AppHandle, url: String) -> Result<(), String> {
    let window = app
        .get_webview_window("cas-login")
        .ok_or("请先打开 CAS 登录窗口")?;

    let target = Url::parse(&url).map_err(|e| format!("Invalid URL: {}", e))?;
    window
        .navigate(target)
        .map_err(|e| format!("Failed to navigate: {}", e))?;

    Ok(())
}

fn query_cookies(window: &tauri::WebviewWindow, url: &Url) -> Result<Vec<serde_json::Value>, String> {
    let cookies = window.cookies_for_url(url.clone())
        .map_err(|e| format!("Failed to extract cookies from {}: {}", url, e))?;
    let result = cookies.iter().map(|c| {
        serde_json::json!({
            "name": c.name(),
            "value": c.value(),
            "domain": c.domain().unwrap_or(""),
            "path": c.path().unwrap_or("/"),
            "secure": c.secure().unwrap_or(false),
            "httpOnly": c.http_only().unwrap_or(false),
        })
    }).collect();
    Ok(result)
}

#[tauri::command]
async fn extract_cookies(app: tauri::AppHandle, platform: Option<String>) -> Result<Vec<serde_json::Value>, String> {
    let cas_url_str = "https://cas.sustech.edu.cn";
    let target_url_str = match platform.as_deref() {
        Some("blackboard") => "https://bb.sustech.edu.cn",
        _ => "https://tis.sustech.edu.cn",
    };

    let window_label = match platform.as_deref() {
        Some("blackboard") => "cas-login-bb",
        _ => "cas-login",
    };

    let window = app.get_webview_window(window_label)
        .ok_or_else(|| format!("CAS login window '{}' not found", window_label))?;

    let mut seen = std::collections::HashSet::new();
    let mut all_cookies = Vec::new();

    // Navigate to each domain so cookies_for_url can read them reliably on macOS.
    for url_str in &[cas_url_str, target_url_str] {
        let nav_url = Url::parse(url_str).map_err(|e| format!("Invalid URL: {}", e))?;
        // Navigate to the target domain first
        if let Err(e) = window.navigate(nav_url) {
            eprintln!("[extract_cookies] navigate to {} failed: {}", url_str, e);
        }
        // Wait for navigation to settle and cookies to become accessible
        tokio::time::sleep(std::time::Duration::from_millis(500)).await;

        let url = Url::parse(url_str).map_err(|e| format!("Invalid URL: {}", e))?;
        match query_cookies(&window, &url) {
            Ok(cookies) => {
                eprintln!("[extract_cookies] {} returned {} cookies", url_str, cookies.len());
                for cookie in &cookies {
                    let name = cookie.get("name").and_then(|v| v.as_str()).unwrap_or("");
                    let domain = cookie.get("domain").and_then(|v| v.as_str()).unwrap_or("");
                    eprintln!("[extract_cookies]   cookie: {} domain={}", name, domain);
                    let key = format!("{}:{}", name, domain);
                    if seen.insert(key) {
                        all_cookies.push(cookie.clone());
                    }
                }
            }
            Err(e) => {
                eprintln!("[extract_cookies] Warning for {}: {}", url_str, e);
            }
        }
    }

    eprintln!("[extract_cookies] total unique cookies: {}", all_cookies.len());
    Ok(all_cookies)
}

#[tauri::command]
async fn extract_all_cookies(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    let domains = [
        Url::parse("https://cas.sustech.edu.cn").unwrap(),
        Url::parse("https://tis.sustech.edu.cn").unwrap(),
        Url::parse("https://bb.sustech.edu.cn").unwrap(),
    ];

    let mut all_cookies: Vec<serde_json::Value> = Vec::new();
    let mut seen = std::collections::HashSet::new();

    for label in &["cas-login", "cas-login-bb"] {
        if let Some(window) = app.get_webview_window(label) {
            for url in &domains {
                match query_cookies(&window, url) {
                    Ok(cookies) => {
                        for cookie in cookies {
                            let name = cookie.get("name").and_then(|v| v.as_str()).unwrap_or("");
                            let domain = cookie.get("domain").and_then(|v| v.as_str()).unwrap_or("");
                            let key = format!("{}:{}", name, domain);
                            if seen.insert(key) {
                                all_cookies.push(cookie);
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("[extract_all_cookies] Warning: {}", e);
                    }
                }
            }
        }
    }

    Ok(serde_json::json!({ "cookies": all_cookies }))
}

#[tauri::command]
async fn bind_tis(cookies: Vec<CookieInfo>, backend_url: String, token: String) -> Result<BindResult, String> {
    if let Err(e) = check_backend_health(&backend_url).await {
        return Ok(BindResult { success: false, message: e, data: None });
    }

    let tis_cookies = cookies_to_dict_multi(&cookies, &["tis.sustech.edu.cn", "cas.sustech.edu.cn"]);

    let has_jsessionid = tis_cookies.get("JSESSIONID").is_some();
    if !has_jsessionid {
        return Ok(BindResult {
            success: false,
            message: "缺少 TIS 的 JSESSIONID Cookie，请确保登录后跳转到了 tis.sustech.edu.cn".to_string(),
            data: Some(tis_cookies),
        });
    }

    let client = make_reqwest_client()?;
    let url = format!("{}/api/v1/tis/bind", backend_url.trim_end_matches('/'));

    let mut req = client
        .post(&url)
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({
            "cookies": tis_cookies.to_string()
        }));

    if !token.is_empty() {
        req = req.header("Authorization", format!("Bearer {}", token));
    }

    let response = req.send().await.map_err(|e| format!("请求失败: {}", e))?;

    let status = response.status().as_u16();
    let body = response.text().await.map_err(|e| format!("读取响应失败: {}", e))?;
    let data: Option<serde_json::Value> = serde_json::from_str(&body).ok();

    if (200..300).contains(&status) {
        let success = data.as_ref()
            .and_then(|d| d.get("success").and_then(|v| v.as_bool()))
            .unwrap_or(true);
        let message = data.as_ref()
            .and_then(|d| d.get("message").and_then(|v| v.as_str()))
            .unwrap_or("绑定成功");
        Ok(BindResult { success, message: message.to_string(), data })
    } else {
        let detail = if status == 502 {
            format!("后端重启中 (502)，请稍后重试。详情: {}", &body[..body.len().min(500)])
        } else {
            format!("HTTP {}: {}", status, &body[..body.len().min(500)])
        };
        Ok(BindResult { success: false, message: detail, data })
    }
}

#[tauri::command]
async fn bind_blackboard(cookies: Vec<CookieInfo>, backend_url: String, token: String, ics_url: Option<String>) -> Result<BindResult, String> {
    if let Err(e) = check_backend_health(&backend_url).await {
        return Ok(BindResult { success: false, message: e, data: None });
    }

    let bb_cookies = cookies_to_dict(&cookies, "bb.sustech.edu.cn");

    if bb_cookies.as_object().map(|m| m.is_empty()).unwrap_or(true) {
        return Ok(BindResult {
            success: false,
            message: "缺少 BB 的 Cookie，请确保登录后访问了 bb.sustech.edu.cn".to_string(),
            data: Some(bb_cookies),
        });
    }

    let client = make_reqwest_client()?;
    let url = format!("{}/api/v1/blackboard/bind", backend_url.trim_end_matches('/'));

    let mut body = serde_json::json!({
        "cookies": bb_cookies.to_string()
    });
    if let Some(ref url) = ics_url {
        body["ics_url"] = serde_json::Value::String(url.clone());
    }

    let mut req = client
        .post(&url)
        .header("Content-Type", "application/json")
        .json(&body);

    if !token.is_empty() {
        req = req.header("Authorization", format!("Bearer {}", token));
    }

    let response = req.send().await.map_err(|e| format!("请求失败: {}", e))?;

    let status = response.status().as_u16();
    let body = response.text().await.map_err(|e| format!("读取响应失败: {}", e))?;
    let data: Option<serde_json::Value> = serde_json::from_str(&body).ok();

    if (200..300).contains(&status) {
        let success = data.as_ref()
            .and_then(|d| d.get("success").and_then(|v| v.as_bool()))
            .unwrap_or(true);
        let message = data.as_ref()
            .and_then(|d| d.get("message").and_then(|v| v.as_str()))
            .unwrap_or("绑定成功");
        Ok(BindResult { success, message: message.to_string(), data })
    } else {
        let detail = if status == 502 {
            format!("后端重启中 (502)，请稍后重试。详情: {}", &body[..body.len().min(500)])
        } else {
            format!("HTTP {}: {}", status, &body[..body.len().min(500)])
        };
        Ok(BindResult { success: false, message: detail, data })
    }
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

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .manage(BackendState {
            local_process: Arc::new(Mutex::new(None)),
            server_process: Arc::new(Mutex::new(None)),
        })
        .setup(|app| {
            let app_handle = app.handle().clone();

            if cfg!(debug_assertions) {
                println!("[ProAgent] Dev mode: backends started by dev.js, skipping sidecar spawn");
            } else {
                tauri::async_runtime::spawn(async move {
                    let state = app_handle.state::<BackendState>();

                    match spawn_backend(&app_handle, "python-backend", state.local_process.clone()) {
                        Ok(_) => {
                            if let Err(e) = wait_for_backend("http://127.0.0.1:8002/health", 60).await {
                                eprintln!("Local backend failed to start: {}", e);
                            }
                        }
                        Err(e) => {
                            eprintln!("Local backend error: {}", e);
                        }
                    }

                    match spawn_backend(&app_handle, "server-backend", state.server_process.clone()) {
                        Ok(_) => {
                            if let Err(e) = wait_for_backend("http://127.0.0.1:8001/health", 60).await {
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
        .invoke_handler(tauri::generate_handler![
            open_cas_login,
            close_cas_window,
            navigate_cas_window,
            extract_cookies,
            extract_all_cookies,
            bind_tis,
            bind_blackboard,
            restart_backends,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
