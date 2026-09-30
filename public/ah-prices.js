(function(){
"use strict";
var CACHE_KEY='phoenix-ah-v1',MAX_AGE=3600;
window.AH=null;
function load(){
 try{
  var c=JSON.parse(localStorage.getItem(CACHE_KEY));
  if(c&&c.prices&&(Date.now()/1000-c.fetched)<MAX_AGE){window.AH=c.prices;show(c);return;}
 }catch(e){}
 var x=new XMLHttpRequest();
 x.open('GET','/data/ah-prices.json');
 x.onload=function(){
  if(x.status===200){
   try{
    var d=JSON.parse(x.responseText);
    window.AH=d.prices;
    try{localStorage.setItem(CACHE_KEY,x.responseText);}catch(e){}
    show(d);
   }catch(e){}
  }
 };
 x.send();
}
function show(d){
 if(!window.PT)return;
 var el=document.getElementById('ahStatus');
 if(!el)return;
 var ago=Math.floor((Date.now()/1000-d.fetched)/60);
 var t=ago<60?ago+'m ago':Math.floor(ago/60)+'h ago';
 el.innerHTML='<span class="ah-dot"></span>AH: '+d.count+' items ('+t+')';
 el.title='Prices from PSXI.gg for PhoenixXI';
 el.style.display='';
}
load();
})();
