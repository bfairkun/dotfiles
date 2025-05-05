# Set VSCode terminal environment (optional)
Sys.setenv(TERM_PROGRAM = "vscode")

# Safely detect whether we're in a tmux_R window
tmux_info <- tryCatch(system("tmux display -p", intern = TRUE, ignore.stderr = TRUE), error = function(e) "")
Is_tmuxR_window <- length(tmux_info) > 0 && grepl("tmux_R", tmux_info)

# VS Code viewer setup if in tmux_R session
if (interactive() && Sys.getenv("RSTUDIO") == "" && Is_tmuxR_window) {
  source(file.path(Sys.getenv(if (.Platform$OS.type == "windows") "USERPROFILE" else "HOME"), ".vscode-R", "init.R"))
  options(vsc.plot = "Beside")
  options(vsc.dev.args = list(width = 800, height = 600))
  options(vsc.viewer = "Beside")

  if (requireNamespace("httpgd", quietly = TRUE)) {
    options(vsc.plot = FALSE)
    options(device = function(...) {
      httpgd::hgd(silent = TRUE)
      .vsc.browser(httpgd::hgd_url(history = FALSE), viewer = "Beside")
    })
  }
}

# Always define this function, even outside tmux
print_httpgd_tunnel_instructions <- function(local_port = 9999) {
  if (!requireNamespace("httpgd", quietly = TRUE)) {
    stop("The 'httpgd' package is not installed.")
  }

  url <- httpgd::hgd_url()
  if (is.null(url)) stop("No httpgd server found. Run hgd() first.")

  # Extract port and token from URL
  port <- as.integer(gsub(".*:(\\d+)/.*", "\\1", url))
  token <- sub(".+token=([^&]+).*", "\\1", url)
  compute_host <- system("hostname", intern = TRUE)
  user <- Sys.getenv("USER")
  login_host <- "your.login.node"

  cat("\n=== httpgd Remote Tunnel Setup without Jump ===\n")
  cat("1. On the LOGIN NODE (after you ssh in), run:\n\n")
  cat(paste0("ssh -L ", port, ":localhost:", port, " ", compute_host, "\n\n"))

  cat("2. On your LOCAL machine, run:\n\n")
  cat(paste0("ssh -L ", local_port, ":localhost:", port, " ", user, "@", login_host, "\n\n"))

  cat("3. Then open in browser or VS Code viewer:\n\n")
  cat(paste0("http://localhost:", local_port, "/live?token=", token, "\n"))

  cat("\n=== httpgd Remote Tunnel Setup with Jump ===\n")

  cat("\n1. One-line SSH tunnel (preferred):\n\n")
  cat(paste0(
    "ssh -L ", local_port, ":localhost:", port, 
    " -J ", user, "@", login_host, " ", user, "@", compute_host, "\n"
  ))

  cat("\n2. Then open this in your browser or VS Code viewer:\n\n")
  cat(paste0("http://localhost:", local_port, "/live?token=", token, "\n"))
}

# Automatically launch httpgd with tunnel info for all interactive sessions
if (interactive() && requireNamespace("httpgd", quietly = TRUE)) {
  options(device = function(...) {
    httpgd::hgd(silent = TRUE)
    print_httpgd_tunnel_instructions()
    .vsc.browser(httpgd::hgd_url(history = FALSE), viewer = "Beside")
  })
}

# convenience functions for saving and loading R sessions
load_session <- function(file = "session.RData") {
  if (file.exists(file)) {
    load(file, envir = .GlobalEnv)
    cat("Session loaded from", file, "\n")
  } else {
    cat("No session file found at", file, "\n")
  }
}

save_session <- function(file = "session.RData") {
  vars <- ls(envir = .GlobalEnv, all.names = TRUE)
  cat("Saving variables:\n")
  print(vars)
  for (v in vars) try(get(v, envir = .GlobalEnv), silent = TRUE)
  save(list = vars, file = file, envir = .GlobalEnv)
  cat("Session saved to", file, "\n")
}
