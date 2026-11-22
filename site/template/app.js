// 前端运行时（约定见 docs/frontend.md）。分块：
//   偏好（主题/宽度/字号/语言/术语，localStorage）· i18n · 单例悬停提示 · 术语自动标注 ·
//   左侧目录（章节/资产 + 收放 + scrollspy）· 锚点跳转（5% 落点 + 高亮 + 返回栈）·
//   表头吸顶测量 · 表格排序 · Chart.js 时序图（renderPanel）· ARR 跳动计数器。
// 性能约定：滚动帧内零几何查询（位置一次性缓存，只在布局变化时重算）；scroll/resize
// 一律 passive + rAF 节流；同一帧先读后写；无任何 transition / animation。
// 图表 spec 占位（build.py 生成）：
//   "__surface" -> 当前主题面板底色；"__i18n:<key>" -> 当前语言文案；
//   ticks.__epochDays -> x 轴天数转日期；legend.labels.__filterUnderscore -> 隐藏下划线图例；
//   dataset.__group -> 图例 hover 聚光的分组名。
(function () {
  var root = document.documentElement;
  var MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,'Roboto Mono',monospace";
  var $ = function (id) { return document.getElementById(id); };
  var main = document.querySelector("main");
  var topbar = $("topbar");

  function cssVar(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
  function store(key, v) { try { localStorage.setItem(key, v); } catch (e) {} }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // ================= i18n =================
  var I18N = JSON.parse($("i18n-data").textContent);
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
      Object.keys(args).forEach(function (k) { s = s.split("{" + k + "}").join(args[k]); });
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
    document.querySelectorAll("[data-i18n-tip]").forEach(function (el) {
      el.setAttribute("data-tip", msgFor(el, el.getAttribute("data-i18n-tip")));
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach(function (el) {
      el.setAttribute("aria-label", msgFor(el, el.getAttribute("data-i18n-aria-label")));
    });
  }

  // ================= 单例悬停提示 =================
  // 目标声明 data-tip（纯文本）/ data-tiph（受信 HTML）/ .term（现查词典）；
  // 目录里被截断的条目用 peek 形态原位展开。show 时定位一次，此后零逐帧计算。
  var tip = $("tip");
  var tipTarget = null, tipTimer = 0, tipShown = false, tipHiddenAt = 0;

  function tipContent(el) {
    if (el.classList.contains("term")) {
      var t = TERMS[el.getAttribute("data-term")];
      return t ? "<b>" + esc(el.getAttribute("data-term")) + "</b>  " + esc(t[lang] || t.zh) : "";
    }
    if (el.hasAttribute("data-tiph")) return el.getAttribute("data-tiph");
    return esc(el.getAttribute("data-tip") || "");
  }
  function showTip(el) {
    var peek = el.matches("#toc .toc-list a");
    var html = peek ? esc(el.textContent) : tipContent(el);
    if (!html) return;
    // 读
    var rects = el.getClientRects();
    var r = rects.length ? rects[rects.length - 1] : el.getBoundingClientRect();
    // 写
    tip.className = peek ? "peek" : "";
    tip.innerHTML = html;
    tip.hidden = false;
    // 读（contain: content 把强制布局限制在提示自身）
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var vw = root.clientWidth, vh = window.innerHeight;
    var x, y;
    if (peek) {
      x = r.left - 1; y = r.top - 1;
    } else {
      x = Math.max(4, Math.min(r.left, vw - w - 4));
      y = r.bottom + 4;
      if (y + h > vh - 4 && r.top - h - 4 > 0) y = r.top - h - 4;
    }
    tip.style.transform = "translate(" + Math.round(x) + "px," + Math.round(y) + "px)";
    tipShown = true;
  }
  function hideTip() {
    clearTimeout(tipTimer);
    if (tipShown) { tip.hidden = true; tipShown = false; tipHiddenAt = Date.now(); }
    tipTarget = null;
  }
  document.addEventListener("pointerover", function (e) {
    var el = e.target.closest ? e.target.closest("[data-tip],[data-tiph],.term,#toc .toc-list a") : null;
    if (el && el.classList.contains("term") && root.dataset.terms === "off") el = null;
    if (el && el.matches("#toc .toc-list a") && el.scrollWidth <= el.clientWidth) el = null;
    if (el === tipTarget) return;
    clearTimeout(tipTimer);
    tipTarget = el;
    if (!el) { if (tipShown) { tip.hidden = true; tipShown = false; tipHiddenAt = Date.now(); } return; }
    if (tipShown || Date.now() - tipHiddenAt < 250) showTip(el);
    else tipTimer = setTimeout(function () { if (tipTarget === el) showTip(el); }, 80);
  });
  // scroll 只隐藏已显示的提示，不清定时器与 tipTarget（scroll 事件可能晚于滚动后的 pointerover）
  window.addEventListener("scroll", function () {
    if (tipShown) { tip.hidden = true; tipShown = false; tipHiddenAt = Date.now(); }
  }, { passive: true, capture: true });
  document.addEventListener("pointerdown", hideTip);
  document.documentElement.addEventListener("pointerleave", hideTip);

  // ================= 术语自动标注 =================
  var TERMS = JSON.parse($("terms-data").textContent);
  var termAlias = {}, termRe = null;
  (function () {
    var names = [];
    Object.keys(TERMS).forEach(function (key) {
      [key].concat(TERMS[key].aliases || []).forEach(function (a) { termAlias[a] = key; names.push(a); });
    });
    names.sort(function (a, b) { return b.length - a.length; }); // 长词优先
    termRe = new RegExp(names.map(function (n) {
      return n.replace(/[.*+?^${}()|[\]\\\/-]/g, "\\$&");
    }).join("|"), "g");
  })();
  var TERM_SKIP = "h1,h2,h3,h4,h5,h6,a,code,pre,script,style,canvas,button,.term,.arr-number,.badge,.chip,.tag,[data-tip],[data-tiph]";
  var WORD = /[A-Za-z0-9]/;

  function unwrapTerms() {
    main.querySelectorAll(".term").forEach(function (span) {
      var parent = span.parentNode;
      parent.replaceChild(document.createTextNode(span.textContent), span);
      parent.normalize();
    });
  }
  function annotateTerms() {
    var walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || node.nodeValue.length < 2) return NodeFilter.FILTER_REJECT;
        return node.parentElement.closest(TERM_SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      var text = node.nodeValue, last = 0, frag = null, m;
      termRe.lastIndex = 0;
      while ((m = termRe.exec(text))) {
        var a = m[0], i = m.index, j = i + a.length;
        // 英数词做词边界校验（ARR 不该在 carrying 里亮）
        if (WORD.test(a.charAt(0)) && i > 0 && WORD.test(text.charAt(i - 1))) continue;
        if (WORD.test(a.charAt(a.length - 1)) && j < text.length && WORD.test(text.charAt(j))) continue;
        frag = frag || document.createDocumentFragment();
        if (i > last) frag.appendChild(document.createTextNode(text.slice(last, i)));
        var span = document.createElement("span");
        span.className = "term";
        span.setAttribute("data-term", termAlias[a]);
        span.textContent = a;
        frag.appendChild(span);
        last = j;
      }
      if (frag) {
        if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
        node.parentNode.replaceChild(frag, node);
      }
    });
  }

  // ================= 目录 + scrollspy =================
  var tocEl = $("toc"), tocCh = $("toc-ch"), tocAs = $("toc-as");
  var sections = [].slice.call(main.querySelectorAll(".section"));
  var spy = [];           // [{top, ch: li, as: li|null}] 按文档顺序
  var activeCh = null, activeAs = null;

  function sectionTitle(sec) {
    var h = sec.querySelector(".section-title");
    return (h.children[0].textContent + " " + h.children[1].textContent).trim();
  }
  function li(cls, href, html, withToggle, secId) {
    var el = document.createElement("li");
    el.className = cls;
    el.setAttribute("data-target", href.slice(1));
    if (secId) el.setAttribute("data-sec", secId);
    el.innerHTML = (withToggle ? '<button type="button" class="toc-tog" data-sec="' + secId + '">−</button>'
                               : '<span class="toc-pad"></span>') +
      '<a href="' + href + '">' + html + "</a>";
    return el;
  }
  function buildToc() {
    tocCh.textContent = ""; tocAs.textContent = "";
    var figWord = msg(tocEl.getAttribute("data-fig-key")), tblWord = msg(tocEl.getAttribute("data-tbl-key"));
    sections.forEach(function (sec) {
      tocCh.appendChild(li("lv1", "#" + sec.id, esc(sectionTitle(sec)), true, sec.id));
      var num = parseInt(sec.querySelector(".section-index").textContent, 10);
      var k = 0;
      sec.querySelectorAll(".panel[id]").forEach(function (p) {
        var h3 = p.querySelector("h3");
        if (!h3) return;
        var title = h3.textContent.trim();
        tocCh.appendChild(li("lv2", "#" + p.id, esc(title), false, sec.id));
        var kind = p.getAttribute("data-toc");
        if (kind && !isNaN(num)) {
          k += 1;
          tocAs.appendChild(li("as", "#" + p.id,
            '<span class="toc-num">' + esc((kind === "tbl" ? tblWord : figWord) + " " + num + "-" + k) + "</span>" + esc(title),
            false, sec.id));
        }
      });
    });
    activeCh = activeAs = null;
    syncCollapsedToc();
  }
  function syncCollapsedToc() {
    sections.forEach(function (sec) {
      var collapsed = sec.classList.contains("collapsed");
      tocEl.querySelectorAll('li[data-sec="' + sec.id + '"]').forEach(function (el) {
        if (el.classList.contains("lv1")) el.querySelector(".toc-tog").textContent = collapsed ? "+" : "−";
        else el.classList.toggle("hidden", collapsed);
      });
    });
  }
  // 布局变化后重建位置缓存（唯一做几何查询的地方）
  function recalc() {
    var y0 = window.scrollY;
    var rows = [];
    tocCh.querySelectorAll("li").forEach(function (el) {
      var target = $(el.getAttribute("data-target"));
      if (!target || el.classList.contains("hidden")) return;
      rows.push({ el: target, ch: el });
    });
    var asMap = {};
    tocAs.querySelectorAll("li").forEach(function (el) { asMap[el.getAttribute("data-target")] = el; });
    spy = rows.map(function (r) {
      return { top: r.el.getBoundingClientRect().top + y0, ch: r.ch, as: asMap[r.el.id] || null };
    }).sort(function (a, b) { return a.top - b.top; });
    onScroll();
  }
  function onScroll() {
    var y = window.scrollY + jumpOffset() + 2;
    var cur = null, curAs = null;
    for (var i = 0; i < spy.length; i++) {
      if (spy[i].top > y) break;
      cur = spy[i].ch;
      if (spy[i].as) curAs = spy[i].as;
    }
    if (cur !== activeCh) {
      if (activeCh) activeCh.classList.remove("active");
      if (cur) cur.classList.add("active");
      activeCh = cur;
      requestAnimationFrame(function () {
        if (activeCh && !tocCh.hidden) activeCh.scrollIntoView({ block: "nearest" });
      });
    }
    if (curAs !== activeAs) {
      if (activeAs) activeAs.classList.remove("active");
      if (curAs) curAs.classList.add("active");
      activeAs = curAs;
      requestAnimationFrame(function () {
        if (activeAs && !tocAs.hidden) activeAs.scrollIntoView({ block: "nearest" });
      });
    }
  }
  var scrollQueued = false, resizeQueued = false, topbarH = 24;
  window.addEventListener("scroll", function () {
    if (scrollQueued) return;
    scrollQueued = true;
    requestAnimationFrame(function () { scrollQueued = false; onScroll(); });
  }, { passive: true });
  function relayout() {
    topbarH = topbar.getBoundingClientRect().height;      // 读
    root.style.setProperty("--thTop", topbarH + "px");    // 写
    recalc();
  }
  function queueRelayout() {
    if (resizeQueued) return;
    resizeQueued = true;
    requestAnimationFrame(function () { resizeQueued = false; hideTip(); relayout(); });
  }
  window.addEventListener("resize", queueRelayout, { passive: true });
  window.addEventListener("load", queueRelayout);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(queueRelayout);
  if (window.ResizeObserver) new ResizeObserver(queueRelayout).observe(topbar);

  // 收放：Ctrl 点 = 批量；三态：全展开→收起，全收起/部分→展开
  function setCollapsed(list, collapsed) {
    list.forEach(function (sec) { sec.classList.toggle("collapsed", collapsed); });
    syncCollapsedToc();
    queueRelayout();
  }
  function batchToggle() {
    var allOpen = sections.every(function (s) { return !s.classList.contains("collapsed"); });
    setCollapsed(sections, allOpen);
  }
  tocEl.addEventListener("click", function (e) {
    var tog = e.target.closest(".toc-tog");
    if (tog) {
      if (e.ctrlKey || e.metaKey) batchToggle();
      else {
        var sec = $(tog.getAttribute("data-sec"));
        setCollapsed([sec], !sec.classList.contains("collapsed"));
      }
      return;
    }
    if (e.target.id === "toc-all") { batchToggle(); return; }
    var tab = e.target.id === "toc-tab-ch" ? "ch" : e.target.id === "toc-tab-as" ? "as" : null;
    if (tab) {
      tocCh.hidden = tab !== "ch"; tocAs.hidden = tab !== "as";
      $("toc-tab-ch").setAttribute("aria-pressed", tab === "ch");
      $("toc-tab-as").setAttribute("aria-pressed", tab === "as");
      store("tocTab", tab);
    }
  });

  // ================= 锚点跳转：5% 落点 + 高亮 + 返回栈 =================
  var backBtn = $("back-btn"), backStack = [], hlEl = null, hlTimer = 0;

  function jumpOffset() { return Math.max(window.innerHeight * 0.05, topbarH + 8); }
  function targetY(el) { return Math.max(0, el.getBoundingClientRect().top + window.scrollY - jumpOffset()); }
  function highlight(el) {
    clearTimeout(hlTimer);
    if (hlEl) hlEl.classList.remove("jump-hl");
    hlEl = el.classList.contains("section") ? el.querySelector(".section-title") : el;
    hlEl.classList.add("jump-hl");
    hlTimer = setTimeout(function () { hlEl.classList.remove("jump-hl"); hlEl = null; }, 2000);
  }
  function jumpTo(id, push) {
    var el = $(id);
    if (!el) return;
    if (push) {
      backStack.push(window.scrollY);
      if (backStack.length > 5) backStack.shift();
      syncBack();
    }
    var sec = el.closest(".section");
    if (sec && sec !== el && sec.classList.contains("collapsed")) {
      sec.classList.remove("collapsed");
      syncCollapsedToc();
      relayout();
    }
    if (id === "top") { window.scrollTo(0, 0); return; }
    window.scrollTo(0, targetY(el));
    highlight(el);
    var tries = 3;                       // 图表等尺寸落定后的落点校正，至多 3 帧
    (function fix() {
      if (tries-- <= 0) return;
      requestAnimationFrame(function () {
        var y = targetY(el);
        if (Math.abs(y - window.scrollY) > 2) { window.scrollTo(0, y); fix(); }
      });
    })();
  }
  function syncBack() {
    backBtn.hidden = !backStack.length;
    backBtn.setAttribute("data-i18n-args", JSON.stringify({ n: backStack.length }));
    backBtn.textContent = msgFor(backBtn, "ui.back");
  }
  backBtn.addEventListener("click", function () {
    if (!backStack.length) return;
    window.scrollTo(0, backStack.pop());
    syncBack();
  });
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a) return;
    e.preventDefault();
    hideTip();
    jumpTo(a.getAttribute("href").slice(1), !!a.closest("main")); // 只有正文内锚点入返回栈
  });

  // ================= 表格排序（点表头；空值恒在末尾）=================
  document.addEventListener("click", function (e) {
    var th = e.target.closest ? e.target.closest("th[data-sort]") : null;
    if (!th) return;
    var tr = th.parentNode, idx = [].indexOf.call(tr.children, th);
    var tbody = th.closest("table").tBodies[0];
    var desc = th.getAttribute("aria-sort") !== "descending";
    var numeric = th.getAttribute("data-sort") === "num";
    [].forEach.call(tr.children, function (c) { c.removeAttribute("aria-sort"); });
    th.setAttribute("aria-sort", desc ? "descending" : "ascending");
    var rows = [].slice.call(tbody.rows).map(function (row) {
      var cell = row.cells[idx], raw = cell.getAttribute("data-v");
      if (raw === null) raw = cell.textContent.trim();
      return { row: row, v: numeric ? (raw === "" ? null : parseFloat(raw)) : raw };
    });
    rows.sort(function (a, b) {
      if (a.v === null || a.v === "") return 1;
      if (b.v === null || b.v === "") return -1;
      var c = numeric ? a.v - b.v : String(a.v).localeCompare(String(b.v));
      return desc ? -c : c;
    });
    var frag = document.createDocumentFragment();
    rows.forEach(function (r) { frag.appendChild(r.row); });
    tbody.appendChild(frag);
    queueRelayout();
  });

  // ================= Chart.js 时序图 =================
  var dataEl = $("dashboard-data");
  var D = dataEl && typeof Chart !== "undefined"
    ? (window.DASHBOARD = JSON.parse(dataEl.textContent))
    : null;
  var charts = {};
  var CHART_FS = { s: 12, m: 12, l: 13.5 };   // 图内文字不低于 12px

  // 时序图十字指示线：悬停处画一条竖线，配合 index 模式的全系列提示
  var crosshair = {
    id: "crosshair",
    afterDatasetsDraw: function (chart) {
      var active = chart.tooltip && chart.tooltip.getActiveElements();
      if (!active || !active.length || !chart.options.__crosshair) return;
      var x = active[0].element.x, area = chart.chartArea, ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, area.top); ctx.lineTo(x, area.bottom);
      ctx.lineWidth = 1; ctx.strokeStyle = cssVar("--text-3");
      ctx.stroke();
      ctx.restore();
    },
  };

  function applyChartDefaults() {
    Chart.defaults.font.family = MONO;
    Chart.defaults.font.size = CHART_FS[root.dataset.fs] || 12;
    Chart.defaults.color = cssVar("--text-2");
    Chart.defaults.borderColor = cssVar("--chart-grid");
    Chart.defaults.animation = false;
    var labels = Chart.defaults.plugins.legend.labels;
    labels.boxWidth = 14;
    labels.boxHeight = 10;
    var tt = Chart.defaults.plugins.tooltip;
    tt.backgroundColor = cssVar("--surface");
    tt.titleColor = cssVar("--text");
    tt.bodyColor = cssVar("--text-2");
    tt.borderColor = cssVar("--text-2");
    tt.borderWidth = 1;
    tt.cornerRadius = 0;
    tt.padding = 8;
    tt.boxPadding = 4;
    tt.titleFont = { family: MONO, weight: "bold" };
    tt.bodyFont = { family: MONO };
  }

  // ---- 图例 hover 聚光：淡出非当前组的系列 ----
  var DIM = 0.12;
  var COLOR_KEYS = ["backgroundColor", "borderColor", "pointBackgroundColor",
                    "pointBorderColor", "hoverBackgroundColor", "hoverBorderColor"];
  function fade(c, alpha) {
    if (Array.isArray(c)) return c.map(function (x) { return fade(x, alpha); });
    if (typeof c !== "string" || c.charAt(0) !== "#") return c;
    var hex = c.slice(1);
    if (hex.length === 3 || hex.length === 4) hex = hex.replace(/./g, function (ch) { return ch + ch; });
    if (hex.length !== 6 && hex.length !== 8) return c;
    var a = hex.length === 8 ? parseInt(hex.slice(6), 16) : 255;
    var out = Math.round(a * alpha).toString(16);
    return "#" + hex.slice(0, 6) + (out.length < 2 ? "0" + out : out);
  }
  function emphasisState(chart) {
    if (!chart.$emphasis) {
      var sets = chart.data.datasets;
      chart.$emphasis = {
        group: null,
        groups: sets.map(function (ds, i) { return ds.__group || "#" + i; }),
        base: sets.map(function (ds) {
          var snap = {};
          COLOR_KEYS.forEach(function (k) { if (k in ds) snap[k] = ds[k]; });
          return snap;
        }),
      };
    }
    return chart.$emphasis;
  }
  function setEmphasis(chart, datasetIndex) {
    var st = emphasisState(chart);
    var group = datasetIndex == null ? null : st.groups[datasetIndex];
    if (st.group === group) return;
    st.group = group;
    chart.data.datasets.forEach(function (ds, i) {
      var dim = group !== null && st.groups[i] !== group;
      Object.keys(st.base[i]).forEach(function (k) {
        ds[k] = dim ? fade(st.base[i][k], DIM) : st.base[i][k];
      });
    });
    chart.update("none");
  }

  function dayToDate(epochISO, days) {
    var d = new Date(epochISO + "T00:00:00Z");
    d.setUTCDate(d.getUTCDate() + Math.round(days));
    return d.toISOString().slice(0, 10);
  }
  function resolveSpec(id) {
    var json = JSON.stringify(D.charts[id]);
    json = json.split('"__surface"').join(JSON.stringify(cssVar("--surface")));
    json = json.replace(/__i18n:[a-z0-9_]+(?:\.[a-z0-9_]+)*/g, function (tok) {
      return JSON.stringify(msg(tok.slice(7))).slice(1, -1);
    });
    return JSON.parse(json);
  }
  function fmtNum(v) {
    var a = Math.abs(v);
    return a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : a >= 1 ? v.toFixed(2) : v.toFixed(3);
  }

  function renderPanel(id, spec) {
    var canvas = $("chart-" + id);
    if (!canvas) return null;
    var opts = spec.options || {};
    opts.responsive = true;
    opts.maintainAspectRatio = false;
    var plugins = (opts.plugins = opts.plugins || {});
    var tooltip = (plugins.tooltip = plugins.tooltip || {});
    var scales = opts.scales || {};
    var epochAxis = false;

    Object.keys(scales).forEach(function (axis) {
      var ticks = scales[axis].ticks || {};
      if (ticks.__epochDays) {
        var epoch = ticks.__epochDays;
        epochAxis = true;
        delete ticks.__epochDays;
        ticks.callback = function (v) { return dayToDate(epoch, v); };
        ticks.maxTicksLimit = 9;
        scales[axis].ticks = ticks;
        tooltip.callbacks = {
          title: function (items) { return items.length ? dayToDate(epoch, items[0].parsed.x) : ""; },
          label: function (item) {
            return item.dataset.label.replace(/^_/, "") + ": $" + fmtNum(item.parsed.y) + "B";
          },
        };
      }
      // 对数轴刻度用普通数字（缺省是科学计数法）
      if (scales[axis].type === "logarithmic") {
        scales[axis].ticks = scales[axis].ticks || {};
        scales[axis].ticks.callback = function (v) {
          var lead = v / Math.pow(10, Math.floor(Math.log10(v) + 1e-9));
          return Math.abs(lead - 1) < 1e-6 || Math.abs(lead - 3) < 1e-6 ? fmtNum(v).replace(/\.0+$/, "") : "";
        };
      }
    });
    if (epochAxis) {
      opts.interaction = { mode: "nearest", intersect: false };
    } else {
      // 类目 x 轴的时序图：同一日期的全部系列一起提示，按数值降序，配十字指示线
      opts.interaction = { mode: "index", intersect: false };
      opts.__crosshair = true;
      tooltip.itemSort = function (a, b) { return b.parsed.y - a.parsed.y; };
      tooltip.filter = function (item) { return item.parsed.y != null; };
      tooltip.callbacks = {
        label: function (item) { return item.dataset.label + ": " + fmtNum(item.parsed.y); },
      };
    }
    var legend = (plugins.legend = plugins.legend || {});
    var labels = (legend.labels = legend.labels || {});
    if (labels.__filterUnderscore) {
      delete labels.__filterUnderscore;
      labels.filter = function (item) { return item.text.charAt(0) !== "_"; };
    }
    legend.onHover = function (e, item, leg) {
      setEmphasis(leg.chart, item.datasetIndex);
      if (e.native) e.native.target.style.cursor = "pointer";
    };
    legend.onLeave = function (e, item, leg) {
      setEmphasis(leg.chart, null);
      if (e.native) e.native.target.style.cursor = "";
    };
    return new Chart(canvas, { type: spec.type, data: spec.data, options: opts, plugins: [crosshair] });
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

  // ================= 偏好：更多菜单 =================
  var moreBtn = $("more-btn"), moreMenu = $("more-menu");
  function syncSegs() {
    moreMenu.querySelectorAll(".seg").forEach(function (seg) {
      var cur = root.dataset[seg.getAttribute("data-pref")];
      seg.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-v") === cur);
      });
    });
  }
  function setLang(next) {
    lang = next;
    root.dataset.lang = next;
    hideTip();
    unwrapTerms();
    applyI18n();
    annotateTerms();      // 必须在建位置缓存之前
    buildToc();
    syncBack();
    renderAll();
    relayout();
  }
  moreBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    moreMenu.hidden = !moreMenu.hidden;
    moreBtn.setAttribute("aria-expanded", !moreMenu.hidden);
  });
  document.addEventListener("click", function (e) {
    if (!moreMenu.hidden && !e.target.closest(".more")) {
      moreMenu.hidden = true;
      moreBtn.setAttribute("aria-expanded", "false");
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { moreMenu.hidden = true; hideTip(); }
  });
  moreMenu.addEventListener("click", function (e) {
    var b = e.target.closest(".seg button");
    if (!b) return;
    var pref = b.parentNode.getAttribute("data-pref"), v = b.getAttribute("data-v");
    store(pref, v);
    if (pref === "lang") { setLang(v); syncSegs(); return; }
    root.dataset[pref] = v;
    syncSegs();
    if (pref === "theme" || pref === "fs") renderAll();   // 主题不改布局，但图表颜色要重注入
    if (pref !== "theme" && pref !== "terms") queueRelayout();
  });

  // ================= 启动 =================
  (function () {
    var tab = null;
    try { tab = localStorage.getItem("tocTab"); } catch (e) {}
    if (tab === "as") {
      tocCh.hidden = true; tocAs.hidden = false;
      $("toc-tab-ch").setAttribute("aria-pressed", "false");
      $("toc-tab-as").setAttribute("aria-pressed", "true");
    }
  })();
  setLang(lang);
  syncSegs();

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
