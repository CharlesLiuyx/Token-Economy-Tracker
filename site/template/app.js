// 前端渲染：主题切换（light/dark，localStorage 覆盖系统偏好，head 内联脚本已设初值）
// + 语言切换（zh/en，同一套 localStorage/初值机制，文案目录内联在 #i18n-data）
// + renderPanel（Chart.js 薄封装，约束 line/bar/scatter 子集）+ ARR 跳动计数器。
// 图表 spec 由 build.py 生成（见 docs/frontend.md），本文件做主题/语言注入与占位替换：
//   "__surface"                      -> 当前主题面板底色（锚点描边 / 空心点填充）
//   "__i18n:<key>"（可嵌在长串中）    -> 当前语言文案（目录 key，见 site/template/i18n.yml）
//   ticks.__epochDays                -> x 轴天数 → 日期字符串
//   legend.labels.__filterUnderscore -> 隐藏下划线开头的图例项（置信带/外推段等）
// 主题/语言切换时全部图表销毁重建（spec 每次从 D.charts 深拷贝，原件不可变）。
// 静态 DOM 文案切换：data-i18n（textContent）/ data-i18n-html（受信 innerHTML）/
// data-i18n-title / data-i18n-aria-label；参数化文案用 data-i18n-args（JSON，{name} 占位）。
(function () {
  var root = document.documentElement;
  var MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,'Roboto Mono',monospace";

  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // ---- i18n ----
  var I18N = JSON.parse(document.getElementById("i18n-data").textContent);
  var lang = root.dataset.lang === "en" ? "en" : "zh";

  function msg(key) {
    var entry = I18N[key];
    return (entry && entry[lang]) || key;
  }

  function msgFor(el, key) {
    var s = msg(key);
    var raw = el.getAttribute("data-i18n-args");
    if (raw) {
      var args = JSON.parse(raw);
      Object.keys(args).forEach(function (k) {
        s = s.split("{" + k + "}").join(args[k]);
      });
    }
    return s;
  }

  function applyI18n() {
    root.lang = lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = msgFor(el, el.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      el.innerHTML = msgFor(el, el.getAttribute("data-i18n-html"));
    });
    ["title", "aria-label"].forEach(function (attr) {
      document.querySelectorAll("[data-i18n-" + attr + "]").forEach(function (el) {
        el.setAttribute(attr, msgFor(el, el.getAttribute("data-i18n-" + attr)));
      });
    });
  }

  // ---- 图表 ----
  var el = document.getElementById("dashboard-data");
  var D = el && typeof Chart !== "undefined"
    ? (window.DASHBOARD = JSON.parse(el.textContent))
    : null;
  var charts = {};

  function applyChartDefaults() {
    Chart.defaults.font.family = MONO;
    Chart.defaults.font.size = 10.5;
    Chart.defaults.color = cssVar("--text-2");
    Chart.defaults.borderColor = cssVar("--chart-grid");
    Chart.defaults.animation = false;
    var labels = Chart.defaults.plugins.legend.labels;
    labels.boxWidth = 10;
    labels.boxHeight = 10;
    var tt = Chart.defaults.plugins.tooltip;
    tt.backgroundColor = cssVar("--surface");
    tt.titleColor = cssVar("--text");
    tt.bodyColor = cssVar("--text-2");
    tt.borderColor = cssVar("--border-strong");
    tt.borderWidth = 1;
    tt.cornerRadius = 6;
    tt.padding = 10;
    tt.titleFont = { family: MONO, weight: "bold" };
    tt.bodyFont = { family: MONO };
  }

  function dayToDate(epochISO, days) {
    var d = new Date(epochISO + "T00:00:00Z");
    d.setUTCDate(d.getUTCDate() + Math.round(days));
    return d.toISOString().slice(0, 10);
  }

  // spec 占位替换：__surface -> 当前主题底色；__i18n:<key> -> 当前语言文案
  function resolveSpec(id) {
    var json = JSON.stringify(D.charts[id]);
    json = json.split('"__surface"').join(JSON.stringify(cssVar("--surface")));
    json = json.replace(/__i18n:[a-z0-9_]+(?:\.[a-z0-9_]+)*/g, function (tok) {
      return JSON.stringify(msg(tok.slice(7))).slice(1, -1);
    });
    return JSON.parse(json);
  }

  function renderPanel(id, spec) {
    var canvas = document.getElementById("chart-" + id);
    if (!canvas) return null;
    var opts = spec.options || {};
    opts.responsive = true;
    opts.maintainAspectRatio = false;
    opts.interaction = opts.interaction || { mode: "nearest", intersect: false };

    // 占位替换：x 轴 epoch 天数 → 日期
    var scales = opts.scales || {};
    Object.keys(scales).forEach(function (axis) {
      var ticks = scales[axis].ticks || {};
      if (ticks.__epochDays) {
        var epoch = ticks.__epochDays;
        delete ticks.__epochDays;
        ticks.callback = function (v) { return dayToDate(epoch, v); };
        ticks.maxTicksLimit = 9;
        scales[axis].ticks = ticks;
        opts.plugins = opts.plugins || {};
        opts.plugins.tooltip = opts.plugins.tooltip || {};
        opts.plugins.tooltip.callbacks = {
          title: function (items) {
            return items.length ? dayToDate(epoch, items[0].parsed.x) : "";
          },
        };
      }
    });
    // 占位替换：图例过滤
    var plugins = (opts.plugins = opts.plugins || {});
    var legend = (plugins.legend = plugins.legend || {});
    var labels = (legend.labels = legend.labels || {});
    if (labels.__filterUnderscore) {
      delete labels.__filterUnderscore;
      labels.filter = function (item) { return item.text.charAt(0) !== "_"; };
    }
    return new Chart(canvas, { type: spec.type, data: spec.data, options: opts });
  }

  function renderAll() {
    if (!D) return;
    applyChartDefaults();
    Object.keys(D.charts || {}).forEach(function (id) {
      if (charts[id]) { charts[id].destroy(); delete charts[id]; }
      try {
        var chart = renderPanel(id, resolveSpec(id));
        if (chart) charts[id] = chart;
      } catch (e) {
        console.error("renderPanel failed:", id, e);
      }
    });
  }

  // ---- 主题切换 ----
  function setTheme(theme) {
    root.dataset.theme = theme;
    renderAll();
  }
  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem("theme", next); } catch (e) {}
      setTheme(next);
    });
  }
  var mq = window.matchMedia("(prefers-color-scheme: dark)");
  function onSystemChange(e) {
    var stored = null;
    try { stored = localStorage.getItem("theme"); } catch (err) {}
    if (stored !== "light" && stored !== "dark") setTheme(e.matches ? "dark" : "light");
  }
  if (mq.addEventListener) mq.addEventListener("change", onSystemChange);

  // ---- 语言切换 ----
  var langBtn = document.getElementById("lang-toggle");
  function setLang(next) {
    lang = next;
    root.dataset.lang = next;
    if (langBtn) langBtn.textContent = next === "zh" ? "EN" : "中"; // 按钮显示切换目标
    applyI18n();
    renderAll();
  }
  if (langBtn) {
    langBtn.addEventListener("click", function () {
      var next = lang === "zh" ? "en" : "zh";
      try { localStorage.setItem("lang", next); } catch (e) {}
      setLang(next);
    });
  }

  setLang(lang); // 首帧：应用初始语言（zh 为构建期默认，重渲染幂等）并渲染全部图表

  // ARR 跳动计数器：纯展示效果，刷新回到 build 基准（docs/arr-methodology.md）
  var fmt = new Intl.NumberFormat("en-US");
  document.querySelectorAll(".arr-number[data-arr]").forEach(function (node) {
    var value = parseFloat(node.dataset.arr);
    var perSecond = parseFloat(node.dataset.rate) / 3600;
    if (!isFinite(value) || !isFinite(perSecond)) return;
    setInterval(function () {
      value += perSecond;
      node.textContent = "$" + fmt.format(Math.round(value));
    }, 1000);
  });
})();
