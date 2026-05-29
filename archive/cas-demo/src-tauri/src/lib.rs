use serde::{Deserialize, Serialize};
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use url::Url;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CookieInfo {
    name: String,
    value: String,
    domain: String,
    path: String,
    secure: bool,
    http_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BindResult {
    success: bool,
    message: String,
    data: Option<serde_json::Value>,
}

#[tauri::command]
async fn open_cas_login(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("cas-login") {
        window.set_focus().map_err(|e| e.to_string())?;
        return Ok(());
    }

    let cas_url = Url::parse(
        "https://cas.sustech.edu.cn/cas/login?service=https://tis.sustech.edu.cn/authentication/main",
    )
    .map_err(|e| format!("Invalid URL: {}", e))?;

    WebviewWindowBuilder::new(&app, "cas-login", WebviewUrl::External(cas_url))
        .title("SUSTech 统一认证登录")
        .inner_size(960.0, 720.0)
        .center()
        .build()
        .map_err(|e| format!("Failed to create window: {}", e))?;

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

#[tauri::command]
async fn extract_cookies(app: tauri::AppHandle) -> Result<Vec<CookieInfo>, String> {
    let window = app
        .get_webview_window("cas-login")
        .ok_or("请先打开 CAS 登录窗口")?;

    let domains = [
        "https://cas.sustech.edu.cn",
        "https://tis.sustech.edu.cn",
        "https://bb.sustech.edu.cn",
    ];

    let mut all_cookies: Vec<CookieInfo> = Vec::new();
    let mut seen = std::collections::HashSet::new();

    for domain in &domains {
        if let Ok(url) = Url::parse(domain) {
            match window.cookies_for_url(url) {
                Ok(cookies) => {
                    for cookie in cookies {
                        let key = format!(
                            "{}:{}:{}",
                            cookie.domain().unwrap_or(""),
                            cookie.path().unwrap_or("/"),
                            cookie.name()
                        );
                        if seen.insert(key) {
                            all_cookies.push(CookieInfo {
                                name: cookie.name().to_string(),
                                value: cookie.value().to_string(),
                                domain: cookie.domain().map(|d| d.to_string()).unwrap_or_default(),
                                path: cookie
                                    .path()
                                    .map(|p| p.to_string())
                                    .unwrap_or_else(|| "/".to_string()),
                                secure: cookie.secure().unwrap_or(false),
                                http_only: cookie.http_only().unwrap_or(false),
                            });
                        }
                    }
                }
                Err(e) => {
                    eprintln!("[CAS] cookies_for_url({}) failed: {}", domain, e);
                }
            }
        }
    }

    Ok(all_cookies)
}

#[tauri::command]
async fn extract_all_cookies(app: tauri::AppHandle) -> Result<Vec<CookieInfo>, String> {
    let window = app
        .get_webview_window("cas-login")
        .ok_or("请先打开 CAS 登录窗口")?;

    let mut all_cookies: Vec<CookieInfo> = Vec::new();

    match window.cookies() {
        Ok(cookies) => {
            for cookie in cookies {
                let domain = cookie.domain().unwrap_or("").to_string();
                if domain.contains("sustech.edu.cn") || domain.is_empty() {
                    all_cookies.push(CookieInfo {
                        name: cookie.name().to_string(),
                        value: cookie.value().to_string(),
                        domain: domain,
                        path: cookie
                            .path()
                            .map(|p| p.to_string())
                            .unwrap_or_else(|| "/".to_string()),
                        secure: cookie.secure().unwrap_or(false),
                        http_only: cookie.http_only().unwrap_or(false),
                    });
                }
            }
        }
        Err(e) => {
            return Err(format!("Failed to get cookies: {}", e));
        }
    }

    Ok(all_cookies)
}

#[tauri::command]
async fn save_cookies(cookies: Vec<CookieInfo>) -> Result<String, String> {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let dir = format!("{}/.proagent", home);
    std::fs::create_dir_all(&dir).map_err(|e| format!("Failed to create directory: {}", e))?;

    let path = format!("{}/cas-cookies.json", dir);
    let json = serde_json::to_string_pretty(&cookies)
        .map_err(|e| format!("Failed to serialize: {}", e))?;

    std::fs::write(&path, json).map_err(|e| format!("Failed to write file: {}", e))?;

    Ok(path)
}

#[tauri::command]
async fn close_cas_window(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("cas-login") {
        window.close().map_err(|e| e.to_string())?;
    }
    Ok(())
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

#[allow(dead_code)]
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
            "后端不可达 ({}): {}。请确认后端服务已启动 (cd local_backend && uvicorn main:app --port 8002)",
            health_url, e
        )
    })?;
    if !resp.status().is_success() {
        return Err(format!("后端健康检查失败 ({}): HTTP {}", health_url, resp.status()));
    }
    Ok(())
}

#[tauri::command]
async fn bind_tis(cookies: Vec<CookieInfo>, backend_url: String, token: String) -> Result<BindResult, String> {
    // Check backend connectivity first
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
        Ok(BindResult {
            success: false,
            message: detail,
            data,
        })
    }
}

#[tauri::command]
async fn bind_blackboard(cookies: Vec<CookieInfo>, backend_url: String, token: String) -> Result<BindResult, String> {
    // Check backend connectivity first
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

    let mut req = client
        .post(&url)
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({
            "cookies": bb_cookies.to_string()
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
        Ok(BindResult {
            success: false,
            message: detail,
            data,
        })
    }
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            open_cas_login,
            navigate_cas_window,
            extract_cookies,
            extract_all_cookies,
            save_cookies,
            close_cas_window,
            bind_tis,
            bind_blackboard,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}