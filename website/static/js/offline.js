// OFFLINE POS - EBEK PHARMACY
let offlineSales = JSON.parse(localStorage.getItem('ebek_offline_sales') || '[]');

function saveOfflineSale(cart, total){
  let sale = {cart:cart, total:total, date:new Date().toISOString(), synced:false};
  offlineSales.push(sale);
  localStorage.setItem('ebek_offline_sales', JSON.stringify(offlineSales));
  showOfflineBadge();
  alert('📴 No Internet - Sale saved OFFLINE: GHS '+total.toFixed(2)+'\nWill sync when internet returns.');
}

function showOfflineBadge(){
  let count = offlineSales.filter(s=>!s.synced).length;
  let badge = document.getElementById('offlineBadge');
  if(badge) badge.innerText = count>0 ? count+' offline sales' : 'Online';
}

async function syncWhenOnline(){
  if(!navigator.onLine || offlineSales.length==0) return;
  let unsynced = offlineSales.filter(s=>!s.synced);
  if(unsynced.length==0) return;
  
  for(let sale of unsynced){
    try{
      let res = await fetch('/sync-offline', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(sale)
      });
      if(res.ok) sale.synced = true;
    }catch(e){ console.log('sync fail, will retry'); }
  }
  offlineSales = offlineSales.filter(s=>!s.synced); // keep only failed
  localStorage.setItem('ebek_offline_sales', JSON.stringify(offlineSales));
  showOfflineBadge();
  if(offlineSales.length==0) console.log('All synced!');
}

window.addEventListener('online', syncWhenOnline);
window.addEventListener('offline', ()=>{ document.getElementById('offlineBadge').innerText='Offline Mode'; });
setInterval(syncWhenOnline, 10000); // try every 10 sec