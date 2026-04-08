# Set VSCode terminal environment (optional)
Sys.setenv(TERM_PROGRAM = "vscode")

# Safely detect whether we're in a tmux_R window
# Only query tmux if we're actually inside a tmux session ($TMUX is set by tmux)
tmux_info <- if (nzchar(Sys.getenv("TMUX"))) {
  tryCatch(system("tmux display -p", intern = TRUE, ignore.stderr = TRUE), error = function(e) "")
} else ""
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
  stopifnot(requireNamespace("httpgd", quietly = TRUE))
  url <- httpgd::hgd_url(); if (is.null(url)) { httpgd::hgd(silent = TRUE); url <- httpgd::hgd_url() }
  port  <- as.integer(sub(".*:(\\d+)/.*", "\\1", url))
  token <- sub(".*token=([^&]+).*", "\\1", url)
  compute <- system("hostname -f", intern = TRUE)
  user <- Sys.getenv("USER")
  login <- Sys.getenv("SLURM_SUBMIT_HOST")

  # If SLURM_SUBMIT_HOST is internal like *.rcc.local, fall back to alias "midway3"
  use_alias <- (login == "" || grepl("\\.rcc\\.local$", login))
  jump_arg <- if (use_alias) "midway3" else sprintf("%s@%s", user, login)

  cat("\nSSH ProxyJump:\n")
  cat(sprintf("ssh -vv -N -L %d:127.0.0.1:%d -J %s %s@%s\n", local_port, port, jump_arg, user, compute))
  cat("\nOpen:\n")
  cat(sprintf("http://localhost:%d/live?token=%s\n", local_port, token))
}

# Automatically launch httpgd with tunnel info for all interactive sessions
# Detect if on a Midway compute node by hostname pattern
is_midway_compute_node <- function() {
  hostname <- Sys.getenv("HOSTNAME")
  if (hostname == "") hostname <- system("hostname", intern = TRUE)
  grepl("^midway[0-9]+-\\d+$", hostname)
}
if (interactive() && requireNamespace("httpgd", quietly = TRUE) && is_midway_compute_node()) {
  library(httpgd)
  hgd(silent = TRUE)
  print_httpgd_tunnel_instructions()
}

# convenience functions for saving, loading and clearing R sessions
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

clear_session <- function() {
  rm(list = ls(envir = .GlobalEnv, all.names = TRUE), envir = .GlobalEnv)
  cat("All objects have been removed from the global environment.\n")
}

# Use ragg (headless-safe) as the default graphics device on HPC (no X11)
if (!isTRUE(capabilities("X11")) && requireNamespace("ragg", quietly = TRUE)) {
  options(device = function(...) ragg::agg_png(tempfile(fileext = ".png"), ...))
}

# Register this interactive R session with btw so Claude Code can drive it
if (interactive() && requireNamespace("btw", quietly = TRUE)) {
  btw::btw_mcp_session()
}

view_df_tsv <- function(df, name = "df_view", dir = "~/tmp", lines = 5000) {
  if (!dir.exists(dir)) dir.create(dir, recursive = TRUE)
  file <- normalizePath(file.path(dir, paste0(name, ".tsv")), mustWork = FALSE)

  write.table(head(df, lines), file = file, sep = "\t", quote = FALSE, row.names = FALSE)
  Sys.sleep(0.5)
}
