#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  // Initialize Sentry for crash reporting
  let _guard = sentry::init(("https://your-sentry-dsn@sentry.io/project-id", sentry::ClientOptions {
    release: sentry::release_name!(),
    ..Default::default()
  }));

  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_deep_link::init())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Register deep link handler for OAuth callback
      app.handle().plugin(tauri_plugin_deep_link::register(
        "soulsense",
        move |request| {
          // Handle the deep link, e.g., send to frontend
          println!("Deep link received: {:?}", request);
          // You can emit an event to the frontend here
        },
      )?)?;

      // Start the Python sidecar
      use tauri_plugin_shell::ShellExt;
      let sidecar_command = app.shell().sidecar("soul-sense-backend").unwrap();
      let (_rx, _child) = sidecar_command
          .spawn()
          .expect("Failed to spawn sidecar");
      
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
