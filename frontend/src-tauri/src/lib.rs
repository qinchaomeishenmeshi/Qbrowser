use tauri_plugin_shell::ShellExt; // 引入 Shell 扩展
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init()) // 1. 注册 Shell 插件
    .setup(|app| {
        // 2. 启动 Sidecar (Python 后端)
        let sidecar = app.shell().sidecar("api-server").unwrap();
        let (mut _rx, mut _child) = sidecar.spawn().expect("Failed to spawn sidecar");
        
        Ok(())
    })
    .plugin(tauri_plugin_opener::init())
    .invoke_handler(tauri::generate_handler![])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}