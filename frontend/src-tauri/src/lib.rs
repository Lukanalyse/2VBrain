use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<CommandChild>>);

impl BackendProcess {
    fn stop(&self) {
        if let Ok(mut process) = self.0.lock() {
            if let Some(child) = process.take() {
                let _ = child.kill();
            }
        }
    }
}

fn backend_ready() -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], 8000));
    let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(250)) else {
        return false;
    };

    let timeout = Some(Duration::from_millis(250));
    let _ = stream.set_read_timeout(timeout);
    let _ = stream.set_write_timeout(timeout);

    if stream
        .write_all(
            b"GET /api/v1/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n",
        )
        .is_err()
    {
        return false;
    }

    let mut response = String::new();
    stream.read_to_string(&mut response).is_ok()
        && response.starts_with("HTTP/1.1 200")
        && response.contains("\"status\":\"ok\"")
}

fn reveal_window_when_ready(app: tauri::AppHandle) {
    std::thread::spawn(move || {
        for _ in 0..100 {
            if backend_ready() {
                break;
            }
            std::thread::sleep(Duration::from_millis(100));
        }

        if let Some(window) = app.get_webview_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
        }
    });
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;

            let child = if backend_ready() {
                None
            } else {
                let data_dir_arg = data_dir.to_string_lossy().into_owned();
                let parent_pid = std::process::id().to_string();
                let command = app
                    .shell()
                    .sidecar("research-os-backend")?
                    .args([
                        "--data-dir",
                        data_dir_arg.as_str(),
                        "--parent-pid",
                        parent_pid.as_str(),
                    ]);
                let (mut events, child) = command.spawn()?;

                tauri::async_runtime::spawn(async move {
                    while events.recv().await.is_some() {}
                });

                Some(child)
            };

            app.manage(BackendProcess(Mutex::new(child)));
            reveal_window_when_ready(app.handle().clone());
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build Research OS desktop application");

    app.run(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            app_handle.state::<BackendProcess>().stop();
        }
    });
}
