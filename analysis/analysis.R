#!/usr/bin/env Rscript
# ColorFrame statistical analysis (base R only; runs in the pinned Modal R container).
#
#   Rscript analysis/analysis.R <results_dir> <output_dir>
#
# Inputs  (results_dir): raw_runs.tsv, rq1_recovery.tsv, cross_language.tsv, agent_usage.csv
# Outputs (output_dir) : runtime_summary.tsv, speedup.tsv, rq1_replicate_stats.tsv, usage_summary.tsv,
#                        fig*.png (or .pdf if no PNG device), analysis_notes.txt
#
# Descriptive statistics only: medians and interquartile ranges over repeated runs. With three
# implementations and one development history per language, no inferential test of RQ4 is
# meaningful and none is attempted.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("usage: analysis.R <results_dir> <output_dir>")
res_dir <- args[1]; out_dir <- args[2]
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
notes <- character()
note <- function(...) notes <<- c(notes, paste0(...))

impl_cols <- c(python = "#3B6EA8", cpp = "#C2553A", rust = "#4C9A5F")
open_fig <- function(name, w = 7, h = 5) {
  ok <- tryCatch({ png(file.path(out_dir, paste0(name, ".png")), width = w, height = h,
                       units = "in", res = 150, type = "cairo"); TRUE },
                 error = function(e) FALSE, warning = function(w) FALSE)
  if (!ok) pdf(file.path(out_dir, paste0(name, ".pdf")), width = w, height = h)
}
q <- function(x, p) as.numeric(quantile(x, p, names = FALSE, type = 7))
write_tsv <- function(df, name) write.table(df, file.path(out_dir, name), sep = "\t",
                                            quote = FALSE, row.names = FALSE)

# ---------------------------------------------------------------- runtime / memory (RQ2, RQ3)
raw <- read.delim(file.path(res_dir, "raw_runs.tsv"), stringsAsFactors = FALSE)
raw$family <- sub("_.*", "", raw$workload)
raw$n_nodes <- suppressWarnings(as.integer(sub("^perf_n([0-9]+)_.*$", "\\1", raw$workload)))
raw$n_nodes[!grepl("^perf_n", raw$workload)] <- NA
raw$branching <- ifelse(grepl("_high$", raw$workload), "high (2.0)",
                        ifelse(grepl("_low$", raw$workload), "low (1.2)", NA))
raw$max_states <- suppressWarnings(as.numeric(sub("^stress_s([0-9]+)$", "\\1", raw$workload)))
raw$max_states[!grepl("^stress_s", raw$workload)] <- NA
raw$throughput <- raw$search_states / (raw$search_ms / 1000)   # search-only phase (spec v1.1)

keys <- unique(raw[, c("workload", "impl")])
summ <- do.call(rbind, lapply(seq_len(nrow(keys)), function(i) {
  d <- raw[raw$workload == keys$workload[i] & raw$impl == keys$impl[i], ]
  data.frame(workload = keys$workload[i], impl = keys$impl[i], runs = nrow(d),
             wall_ms_median = median(d$wall_ms), wall_ms_iqr = IQR(d$wall_ms),
             parse_ms_median = median(d$parse_ms), validate_ms_median = median(d$validate_ms),
             canonicalize_ms_median = if ("canonicalize_ms" %in% names(d)) median(d$canonicalize_ms) else NA,
             search_ms_median = median(d$search_ms), search_ms_q1 = q(d$search_ms, .25),
             search_ms_q3 = q(d$search_ms, .75), total_ms_median = median(d$total_ms),
             peak_rss_mb_median = median(d$peak_rss_mb), peak_rss_mb_iqr = IQR(d$peak_rss_mb),
             search_states = d$search_states[1],
             throughput_states_per_s_median = median(d$throughput),
             outputs_identical = length(unique(d$output_sha256_16)) == 1)
}))
summ <- summ[order(summ$workload, summ$impl), ]
write_tsv(summ, "runtime_summary.tsv")

# speed-up of compiled implementations relative to Python (median search time ratio)
sp <- do.call(rbind, lapply(unique(summ$workload), function(w) {
  s <- summ[summ$workload == w, ]
  py <- s$search_ms_median[s$impl == "python"]
  if (length(py) == 0) return(NULL)
  data.frame(workload = w,
             cpp_vs_python_search = if (any(s$impl == "cpp")) py / s$search_ms_median[s$impl == "cpp"] else NA,
             rust_vs_python_search = if (any(s$impl == "rust")) py / s$search_ms_median[s$impl == "rust"] else NA,
             rust_vs_cpp_search = if (all(c("cpp", "rust") %in% s$impl))
               s$search_ms_median[s$impl == "cpp"] / s$search_ms_median[s$impl == "rust"] else NA,
             cpp_vs_python_total = if (any(s$impl == "cpp")) s$total_ms_median[s$impl == "python"] / s$total_ms_median[s$impl == "cpp"] else NA,
             rust_vs_python_total = if (any(s$impl == "rust")) s$total_ms_median[s$impl == "python"] / s$total_ms_median[s$impl == "rust"] else NA)
}))
write_tsv(sp, "speedup.tsv")
note("Speed-up = ratio of medians: search_ms (search phase only, spec v1.1) and total_ms (all in-process phases).")

impls <- intersect(names(impl_cols), unique(raw$impl))

# Fig 1: search time vs graph size (perf family)
perf <- summ[grepl("^perf_n", summ$workload), ]
perf$n_nodes <- as.integer(sub("^perf_n([0-9]+)_.*$", "\\1", perf$workload))
perf$high <- grepl("_high$", perf$workload)
if (nrow(perf) > 0) {
  open_fig("fig1_scaling_search_time", 9, 4.5)
  par(mfrow = c(1, 2), mar = c(4.5, 4.5, 2.5, 1))
  for (hb in c(FALSE, TRUE)) {
    d <- perf[perf$high == hb, ]
    plot(NA, log = "xy", xlim = range(d$n_nodes), ylim = range(pmax(d$search_ms_q1, 1e-3), d$search_ms_q3),
         xlab = "nodes", ylab = "search time, ms (median, IQR)",
         main = if (hb) "high branching (2.0)" else "low branching (1.2)")
    for (im in impls) {
      e <- d[d$impl == im, ]; e <- e[order(e$n_nodes), ]
      lines(e$n_nodes, e$search_ms_median, type = "b", pch = 19, col = impl_cols[im])
      arrows(e$n_nodes, pmax(e$search_ms_q1, 1e-3), e$n_nodes, e$search_ms_q3, angle = 90, code = 3,
             length = 0.03, col = impl_cols[im])
    }
    legend("topleft", legend = impls, col = impl_cols[impls], pch = 19, bty = "n")
  }
  dev.off()
}

# Fig 2: stress — search time and throughput vs state limit
st <- summ[grepl("^stress_s", summ$workload), ]
st$max_states <- as.numeric(sub("^stress_s([0-9]+)$", "\\1", st$workload))
if (nrow(st) > 0) {
  open_fig("fig2_stress_state_limit", 9, 4.5)
  par(mfrow = c(1, 2), mar = c(4.5, 4.5, 2.5, 1))
  plot(NA, log = "xy", xlim = range(st$max_states), ylim = range(pmax(st$search_ms_q1, 1e-3), st$search_ms_q3),
       xlab = "max search states", ylab = "search time, ms", main = "cycle-heavy stress workload")
  for (im in impls) { e <- st[st$impl == im, ]; e <- e[order(e$max_states), ]
    lines(e$max_states, e$search_ms_median, type = "b", pch = 19, col = impl_cols[im]) }
  legend("topleft", legend = impls, col = impl_cols[impls], pch = 19, bty = "n")
  plot(NA, log = "x", xlim = range(st$max_states), ylim = c(0, max(st$throughput_states_per_s_median) * 1.1),
       xlab = "max search states", ylab = "states / second (median)", main = "search throughput")
  for (im in impls) { e <- st[st$impl == im, ]; e <- e[order(e$max_states), ]
    lines(e$max_states, e$throughput_states_per_s_median, type = "b", pch = 19, col = impl_cols[im]) }
  dev.off()
}

# Fig 3: peak RSS per workload
if (nrow(summ) > 0) {
  wl <- unique(summ$workload)
  m <- sapply(impls, function(im) sapply(wl, function(w) {
    v <- summ$peak_rss_mb_median[summ$workload == w & summ$impl == im]; if (length(v)) v else NA }))
  m <- matrix(m, nrow = length(wl), dimnames = list(wl, impls))
  open_fig("fig3_peak_rss", 10, 5)
  par(mar = c(9, 4.5, 2.5, 1))
  barplot(t(m), beside = TRUE, col = impl_cols[impls], las = 2, cex.names = 0.7,
          ylab = "peak RSS, MB (median)", main = "peak resident memory (whole process)")
  legend("topleft", legend = impls, fill = impl_cols[impls], bty = "n")
  dev.off()
  note("Peak RSS is for the whole process: it includes the Python interpreter itself.")
  floor_mb <- min(raw$peak_rss_mb)
  share <- mean(abs(raw$peak_rss_mb - floor_mb) < 0.01)
  if (share > 0.5) note(sprintf(paste0("WARNING: %.0f%% of runs report the same peak RSS (%.2f MB): the environment ",
                                       "reports a floor, so peak RSS below it is not measurable here."), 100 * share, floor_mb))
}

# ---------------------------------------------------------------- RQ1: support policies (v1.0.1)
# Replicate-level statistics per (condition, policy, p): mean, SD, median, IQR and an exploratory
# 95% t-interval for the mean across the independent structural replicates. Clean and noisy
# conditions are reported separately. No hypothesis tests.
rq1_file <- file.path(res_dir, "rq1_recovery.tsv")
if (file.exists(rq1_file)) {
  r1 <- read.delim(rq1_file, stringsAsFactors = FALSE)
  metrics <- c("true_ceiling", "recovered", "recovered_within_true_ceiling", "recovered_via_spurious_only",
               "true_local_support", "true_shared_support", "spurious_local_only", "spurious_shared_only",
               "candidates", "extra_candidates", "fragmented")
  keys <- unique(r1[, c("condition", "policy", "p_true_observation")])
  keys <- keys[order(keys$condition, keys$policy, keys$p_true_observation), ]
  stat_rows <- list()
  for (k in seq_len(nrow(keys))) {
    d <- r1[r1$condition == keys$condition[k] & r1$policy == keys$policy[k] &
              r1$p_true_observation == keys$p_true_observation[k], ]
    for (m in metrics) {
      x <- d[[m]]; n <- length(x); sdv <- if (n > 1) sd(x) else NA
      h <- if (n > 1) qt(0.975, n - 1) * sdv / sqrt(n) else NA
      stat_rows[[length(stat_rows) + 1]] <- data.frame(
        condition = keys$condition[k], policy = keys$policy[k], p_true_observation = keys$p_true_observation[k],
        metric = m, n_replicates = n, mean = mean(x), sd = sdv, median = median(x),
        q1 = q(x, .25), q3 = q(x, .75), ci95_low = mean(x) - h, ci95_high = mean(x) + h)
    }
  }
  rs <- do.call(rbind, stat_rows)
  write_tsv(rs, "rq1_replicate_stats.tsv")
  note(sprintf("RQ1: %d replicates per setting; 95%% intervals are exploratory t-intervals across replicates.",
               max(rs$n_replicates)))
  note(sprintf("RQ1 search completeness: recovered_within_true_ceiling == true_ceiling in %d of %d runs.",
               sum(r1$recovered_within_true_ceiling == r1$true_ceiling), nrow(r1)))
  pc <- c(strict = "#7A4EA3", permissive = "#D9932B")
  get <- function(cond, pol, m) { e <- rs[rs$condition == cond & rs$policy == pol & rs$metric == m, ]
    e[order(e$p_true_observation), ] }
  band <- function(e, col) {
    lines(e$p_true_observation, e$mean, type = "b", pch = 19, col = col)
    arrows(e$p_true_observation, e$ci95_low, e$p_true_observation, e$ci95_high, angle = 90, code = 3,
           length = 0.03, col = col)
  }
  open_fig("fig4_rq1_policies", 13, 4.5)
  par(mfrow = c(1, 3), mar = c(4.5, 4.5, 2.5, 1))
  plot(NA, xlim = c(0, 1), ylim = c(0, 100), xlab = "p_true_observation",
       ylab = "planted ORFs (of 100), mean and 95% CI", main = "clean: true-support ceilings")
  band(get("clean", "strict", "true_ceiling"), pc["strict"])
  band(get("clean", "permissive", "true_ceiling"), pc["permissive"])
  legend("topleft", c("strict: true shared support", "permissive: true local support"), col = pc, pch = 19, bty = "n")
  ymax <- max(rs$ci95_high[rs$metric == "recovered_via_spurious_only"], 1, na.rm = TRUE)
  plot(NA, xlim = c(0, 1), ylim = c(0, ymax * 1.1), xlab = "p_true_observation",
       ylab = "planted ORFs recovered without true support", main = "noisy: recovery via spurious colours only")
  band(get("noisy", "strict", "recovered_via_spurious_only"), pc["strict"])
  band(get("noisy", "permissive", "recovered_via_spurious_only"), pc["permissive"])
  plot(NA, xlim = c(0, 1), ylim = c(0, max(rs$ci95_high[rs$metric == "candidates"], na.rm = TRUE) * 1.05),
       xlab = "p_true_observation", ylab = "candidates per workload", main = "candidate volume (solid clean, dashed noisy)")
  for (pol in names(pc)) for (cond in c("clean", "noisy")) {
    e <- get(cond, pol, "candidates")
    lines(e$p_true_observation, e$mean, type = "b", pch = 19, col = pc[pol], lty = if (cond == "clean") 1 else 2)
  }
  dev.off()
  note("RQ1 recovery is synthetic ground-truth recovery in a simplified model; extra candidates are real ORFs in synthetic background sequence.")
}

# ---------------------------------------------------------------- RQ4: AI-assisted development
uf <- file.path(res_dir, "agent_usage.csv")
if (file.exists(uf)) {
  u <- read.csv(uf, stringsAsFactors = FALSE, na.strings = c("NOT_EXPOSED", ""))
  u$total_tokens <- suppressWarnings(as.numeric(u$total_tokens))
  nsum <- function(x) if (all(is.na(x))) NA else sum(x, na.rm = TRUE)  # NOT_EXPOSED stays NA
  agg <- aggregate(cbind(total_tokens = u$total_tokens, tool_calls = suppressWarnings(as.numeric(u$tool_calls)),
                         duration_seconds = suppressWarnings(as.numeric(u$duration_seconds)),
                         retries = suppressWarnings(as.numeric(u$retries))) ~ language + agent,
                   data = u, FUN = nsum, na.action = na.pass)
  write_tsv(agg, "usage_summary.tsv")
  lang <- aggregate(total_tokens ~ language, data = u, FUN = nsum, na.action = na.pass)
  lang <- lang[!is.na(lang$total_tokens), ]
  open_fig("fig5_agent_tokens", 7, 4.5)
  par(mar = c(5, 5, 2.5, 1))
  barplot(lang$total_tokens / 1000, names.arg = lang$language, las = 2, col = "#8C8C8C",
          ylab = "recorded agent tokens (thousands)", main = "recorded AI usage by work category")
  dev.off()
  st8 <- summ[summ$workload == "stress_s800000", ]
  if (nrow(st8) > 0) {
    cmp <- merge(lang, data.frame(language = st8$impl, search_ms = st8$search_ms_median,
                                  rss_mb = st8$peak_rss_mb_median), by = "language")
    write_tsv(cmp, "rq4_effort_vs_performance.tsv")
    note("RQ4 table pairs recorded implementation-agent tokens with stress_s800000 performance; n = 3, descriptive only.")
  }
  note("Token totals include only legs whose usage the harness exposed; legs cut off by API errors are NOT_EXPOSED.")
}

writeLines(c(paste("R", R.version$major, R.version$minor, sep = "."), notes), file.path(out_dir, "analysis_notes.txt"))
cat("analysis complete\n")
