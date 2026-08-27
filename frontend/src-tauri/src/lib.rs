use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<CommandChild>>);

fn filesystem_path(value: &str) -> Result<PathBuf, String> {
    let value = value.trim();
    if value.is_empty() {
        return Err("No path was provided.".to_string());
    }

    let value = value.strip_prefix("sqlite:///").unwrap_or(value);
    let value = value.strip_prefix("file://").unwrap_or(value);
    Ok(PathBuf::from(value))
}

fn existing_path(value: &str) -> Result<PathBuf, String> {
    let path = filesystem_path(value)?;
    if path.exists() {
        Ok(path)
    } else {
        Err(format!("Path does not exist: {}", path.display()))
    }
}

fn run_system_command(mut command: Command, action: &str) -> Result<(), String> {
    command
        .spawn()
        .map(|_| ())
        .map_err(|error| format!("Unable to {action}: {error}"))
}

#[tauri::command]
fn select_vault_folder() -> Result<Option<String>, String> {
    #[cfg(target_os = "macos")]
    {
        let output = Command::new("osascript")
            .args([
                "-e",
                "POSIX path of (choose folder with prompt \"Select an Obsidian vault\")",
            ])
            .output()
            .map_err(|error| format!("Unable to show the folder picker: {error}"))?;
        if !output.status.success() {
            return Ok(None);
        }
        let path = String::from_utf8_lossy(&output.stdout)
            .trim()
            .trim_end_matches('/')
            .to_string();
        return Ok((!path.is_empty()).then_some(path));
    }

    #[cfg(target_os = "windows")]
    {
        let script = "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog; if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath }";
        let output = Command::new("powershell")
            .args(["-NoProfile", "-Command", script])
            .output()
            .map_err(|error| format!("Unable to show the folder picker: {error}"))?;
        let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
        return Ok((!path.is_empty()).then_some(path));
    }

    #[cfg(all(not(target_os = "macos"), not(target_os = "windows")))]
    {
        let output = Command::new("zenity")
            .args(["--file-selection", "--directory", "--title=Select an Obsidian vault"])
            .output()
            .map_err(|error| format!("Unable to show the folder picker: {error}"))?;
        if !output.status.success() {
            return Ok(None);
        }
        let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
        Ok((!path.is_empty()).then_some(path))
    }
}

#[tauri::command]
fn open_path(path: String) -> Result<(), String> {
    let path = existing_path(&path)?;
    let target = if path.is_file() {
        path.parent().unwrap_or(Path::new(".")).to_path_buf()
    } else {
        path
    };

    #[cfg(target_os = "macos")]
    return run_system_command({
        let mut command = Command::new("open");
        command.arg(&target);
        command
    }, "open the folder");

    #[cfg(target_os = "windows")]
    return run_system_command({
        let mut command = Command::new("explorer");
        command.arg(&target);
        command
    }, "open the folder");

    #[cfg(all(not(target_os = "macos"), not(target_os = "windows")))]
    run_system_command({
        let mut command = Command::new("xdg-open");
        command.arg(&target);
        command
    }, "open the folder")
}

#[tauri::command]
fn reveal_path(path: String) -> Result<(), String> {
    let path = existing_path(&path)?;

    #[cfg(target_os = "macos")]
    return run_system_command({
        let mut command = Command::new("open");
        command.arg("-R").arg(&path);
        command
    }, "reveal the path in Finder");

    #[cfg(target_os = "windows")]
    return run_system_command({
        let mut command = Command::new("explorer");
        if path.is_file() {
            command.arg(format!("/select,{}", path.display()));
        } else {
            command.arg(&path);
        }
        command
    }, "reveal the path in Explorer");

    #[cfg(all(not(target_os = "macos"), not(target_os = "windows")))]
    run_system_command({
        let target = if path.is_file() {
            path.parent().unwrap_or(Path::new("."))
        } else {
            path.as_path()
        };
        let mut command = Command::new("xdg-open");
        command.arg(target);
        command
    }, "reveal the path in the file manager")
}

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
        .invoke_handler(tauri::generate_handler![
            select_vault_folder,
            open_path,
            reveal_path
        ])
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

#[cfg(test)]
mod tests {
    use super::filesystem_path;
    use std::path::PathBuf;

    #[test]
    fn converts_absolute_sqlite_url_to_a_filesystem_path() {
        assert_eq!(
            filesystem_path("sqlite:////Users/research/Research OS/research_os.db").unwrap(),
            PathBuf::from("/Users/research/Research OS/research_os.db")
        );
    }

    #[test]
    fn keeps_regular_paths_unchanged() {
        assert_eq!(
            filesystem_path("/Users/research/Research OS/library").unwrap(),
            PathBuf::from("/Users/research/Research OS/library")
        );
    }
}
