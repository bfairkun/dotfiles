Sys.setenv(TERM_PROGRAM="vscode")
Is_tmuxR_window <- grepl("tmux_R", system("tmux display -p", intern=T))
if (interactive() && Sys.getenv("RSTUDIO") == "" && Is_tmuxR_window) {
    source(file.path(Sys.getenv(if (.Platform$OS.type == "windows") "USERPROFILE" else "HOME"), ".vscode-R", "init.R"))
    options(vsc.plot = "Beside")
    options(vsc.dev.args = list(width = 800, height = 600))
    options(vsc.viewer = "Beside")
    # To show the original httpgd viewer in a webpage in VS Code
    if (requireNamespace("httpgd", quietly = TRUE)) {
    options(vsc.plot = FALSE)
    options(device = function(...) {
      httpgd::hgd(silent = TRUE)
      .vsc.browser(httpgd::hgd_url(history = FALSE), viewer = "Beside")
    })
  }
}

