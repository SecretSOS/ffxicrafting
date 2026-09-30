(function(){
var u=new URL(location.href);
if(u.searchParams.get('sos')==='1')try{localStorage.setItem('phoenix-pt','1')}catch(e){}
else if(u.searchParams.get('sos')==='0')try{localStorage.removeItem('phoenix-pt')}catch(e){}
try{window.PT=localStorage.getItem('phoenix-pt')==='1'}catch(e){window.PT=false}
})();
