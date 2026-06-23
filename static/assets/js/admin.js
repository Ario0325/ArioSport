/* ArioSport Admin Panel interactions */
(function () {
  "use strict";
  function $(s){return document.querySelector(s);}
  var sidebar=$("#adminSidebar"), overlay=$("#sidebarOverlay");
  function open(){sidebar&&sidebar.classList.add("open");overlay&&overlay.classList.add("show");}
  function close(){sidebar&&sidebar.classList.remove("open");overlay&&overlay.classList.remove("show");}
  var ob=$("#sidebarOpen"),cb=$("#sidebarClose");
  ob&&ob.addEventListener("click",open);
  cb&&cb.addEventListener("click",close);
  overlay&&overlay.addEventListener("click",close);

  // auto slug preview for title field
  var title=document.querySelector('input[name="title"]'), slug=document.querySelector('input[name="slug"]');
  // flash auto-dismiss + manual close
  document.querySelectorAll(".flash-x").forEach(function(b){
    b.addEventListener("click",function(){b.parentElement.remove();});
  });
  setTimeout(function(){document.querySelectorAll(".admin-flash-stack .flash").forEach(function(f){f.style.opacity="0";setTimeout(function(){f.remove();},400);});},4500);

  if(window.lucide&&window.lucide.createIcons)window.lucide.createIcons();
})();
