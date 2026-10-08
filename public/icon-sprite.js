var _iconPos={};
(function(){
  var x=new XMLHttpRequest();
  x.open('GET','/icon-positions.json',true);
  x.onload=function(){if(x.status===200)try{_iconPos=JSON.parse(x.responseText)}catch(e){}};
  x.send();
})();
function iconSpan(id,sz){
  sz=sz||20;
  var p=_iconPos[id];
  if(!p)return '';
  var s='--ic:'+p[1]+';--ir:'+p[2]+';--isz:'+sz+'px';
  if(p[0])s+=';--is:'+p[0];
  return '<span class="icon" style="'+s+'"></span> ';
}
