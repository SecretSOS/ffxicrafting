(function(){
"use strict";

/* ── Live filter ── */
document.querySelectorAll("[data-filter-target]").forEach(function(input){
  var target = document.getElementById(input.getAttribute("data-filter-target"));
  if(!target) return;
  var isTable = target.tagName === "TABLE";
  var rows = isTable
    ? Array.from(target.querySelectorAll("tbody tr"))
    : Array.from(target.children);
  var counter = document.getElementById(input.getAttribute("data-filter-count"));

  input.addEventListener("input", function(){
    var q = this.value.toLowerCase().trim();
    var vis = 0;
    rows.forEach(function(r){
      var text = (r.textContent || "").toLowerCase();
      var show = !q || text.indexOf(q) !== -1;
      r.style.display = show ? "" : "none";
      if(show) vis++;
    });
    if(counter) counter.textContent = vis + " / " + rows.length;
  });
});

/* ── Sortable table headers ── */
document.querySelectorAll("th[data-sort]").forEach(function(th){
  th.style.cursor = "pointer";
  th.style.userSelect = "none";
  th.setAttribute("tabindex","0");

  var arrow = document.createElement("span");
  arrow.className = "sort-arrow";
  arrow.textContent = "";
  th.appendChild(arrow);

  function doSort(){
    var table = th.closest("table");
    var tbody = table.querySelector("tbody");
    var rows = Array.from(tbody.rows);
    var ci = Array.from(th.parentNode.cells).indexOf(th);
    var type = th.getAttribute("data-sort");
    var asc = th.getAttribute("aria-sort") !== "ascending";

    table.querySelectorAll("th .sort-arrow").forEach(function(a){ a.textContent = ""; });
    table.querySelectorAll("th[aria-sort]").forEach(function(h){ h.removeAttribute("aria-sort"); });
    th.setAttribute("aria-sort", asc ? "ascending" : "descending");
    arrow.textContent = asc ? " ▲" : " ▼";

    rows.sort(function(a,b){
      var av = a.cells[ci] ? a.cells[ci].getAttribute("data-v") || a.cells[ci].textContent.trim() : "";
      var bv = b.cells[ci] ? b.cells[ci].getAttribute("data-v") || b.cells[ci].textContent.trim() : "";
      if(type === "num"){
        av = parseFloat(av.replace(/[^0-9.\-]/g,"")) || 0;
        bv = parseFloat(bv.replace(/[^0-9.\-]/g,"")) || 0;
        return asc ? av - bv : bv - av;
      }
      av = av.toLowerCase(); bv = bv.toLowerCase();
      return asc ? (av < bv ? -1 : av > bv ? 1 : 0) : (bv < av ? -1 : bv > av ? 1 : 0);
    });
    rows.forEach(function(r){ tbody.appendChild(r); });
  }

  th.addEventListener("click", doSort);
  th.addEventListener("keydown", function(e){ if(e.key === "Enter") doSort(); });
});

/* ── Tabs ── */
document.querySelectorAll("[data-tabs]").forEach(function(tabBar){
  var tabs = Array.from(tabBar.children);
  tabs.forEach(function(tab){
    tab.addEventListener("click", function(){
      tabs.forEach(function(t){
        t.classList.remove("active");
        var p = document.getElementById(t.getAttribute("data-tab"));
        if(p) p.hidden = true;
      });
      tab.classList.add("active");
      var panel = document.getElementById(tab.getAttribute("data-tab"));
      if(panel) panel.hidden = false;
    });
  });
});

/* ── Section TOC scroll-spy ── */
var toc = document.querySelector("[data-toc]");
if(toc){
  var links = Array.from(toc.querySelectorAll("a[href^='#']"));
  var sections = links.map(function(a){
    return document.getElementById(a.getAttribute("href").slice(1));
  }).filter(Boolean);

  function updateToc(){
    var scrollY = window.scrollY || window.pageYOffset;
    var active = null;
    sections.forEach(function(s, i){
      if(s.getBoundingClientRect().top <= 120) active = i;
    });
    links.forEach(function(a, i){
      a.classList.toggle("active", i === active);
    });
  }
  var tocRaf;
  window.addEventListener("scroll", function(){
    cancelAnimationFrame(tocRaf);
    tocRaf = requestAnimationFrame(updateToc);
  }, {passive:true});
  updateToc();
}

/* ── Back to top ── */
var btn = document.createElement("button");
btn.className = "back-to-top";
btn.setAttribute("aria-label","Back to top");
btn.innerHTML = "&#9650;";
btn.addEventListener("click", function(){ window.scrollTo({top:0,behavior:"smooth"}); });
document.body.appendChild(btn);
var topRaf;
window.addEventListener("scroll", function(){
  cancelAnimationFrame(topRaf);
  topRaf = requestAnimationFrame(function(){
    btn.classList.toggle("visible", (window.scrollY || window.pageYOffset) > 400);
  });
}, {passive:true});

})();
