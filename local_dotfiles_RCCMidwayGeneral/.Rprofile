Sys.setenv(TERM_PROGRAM="vscode")
if (interactive() && Sys.getenv("RSTUDIO") == "") {
    source(file.path(Sys.getenv(if (.Platform$OS.type == "windows") "USERPROFILE" else "HOME"), ".vscode-R", "init.R"))
    options(vsc.plot = "Beside")
    options(vsc.dev.args = list(width = 800, height = 600))
    options(vsc.viewer = "Beside")
}

