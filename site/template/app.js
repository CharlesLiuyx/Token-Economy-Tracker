// 前端渲染：renderPanel（Chart.js 薄封装，约束 line/bar/scatter 子集）+ ARR 跳动计数器。
// 图表 spec 由 build.py 生成（见 docs/frontend.md），本文件只做主题注入与少量占位替换：
//   ticks.__epochDays  -> x 轴天数 → 日期字符串
//   legend.labels.__filterUnderscore -> 隐藏下划线开头的图例项（置信带/外推段等）
(function () {
  var el = document.getElementById("dashboard-data");
  if (!el || typeof Chart === "undefined") return;
  var D = (window.DASHBOARD = JSON.parse(el.textContent));

  var INK = "#1A1A1A";
  var MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,monospace";
  Chart.defaults.font.family = MONO;
  Chart.defaults.font.size = 10.5;
  Chart.defaults.color = INK;
  Chart.defaults.borderColor = "rgba(26,26,26,.14)";
  Chart.defaults.animation = false;
  Chart.defaults.plugins.legend.labels.boxWidth = 11;
  Chart.defaults.plugins.legend.labels.boxHeight = 11;
  var tt = Chart.defaults.plugins.tooltip;
  tt.backgroundColor = "#FFF9E8";
  tt.titleColor = INK;
  tt.bodyColor = INK;
  tt.borderColor = INK;
  tt.borderWidth = 2;
  tt.cornerRadius = 0;
  tt.padding = 10;
  tt.titleFont = { family: MONO, weight: "bold" };
  tt.bodyFont = { family: MONO };

  function dayToDate(epochISO, days) {
    var d = new Date(epochISO + "T00:00:00Z");
    d.setUTCDate(d.getUTCDate() + Math.round(days));
    return d.toISOString().slice(0, 10);
  }

  function renderPanel(id, spec) {
    var canvas = document.getElementById("chart-" + id);
    if (!canvas) return;
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

  Object.keys(D.charts || {}).forEach(function (id) {
    try {
      renderPanel(id, D.charts[id]);
    } catch (e) {
      console.error("renderPanel failed:", id, e);
    }
  });

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
