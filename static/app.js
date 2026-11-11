const fileInput=document.querySelector('#file'),drop=document.querySelector('#drop');
const selected=document.querySelector('#selected'),preview=document.querySelector('#preview');
const analyze=document.querySelector('#analyze'),status=document.querySelector('#status');
const result=document.querySelector('#result');let currentFile=null,previewUrl=null;
function setFile(file){
 if(!file)return;
 const allowed=['image/jpeg','image/png','image/webp'];
 if(!allowed.includes(file.type)){status.textContent='Выбери файл JPG, PNG или WEBP.';return}
 if(file.size>15*1024*1024){status.textContent='Файл больше 15 МБ.';return}
 currentFile=file;if(previewUrl)URL.revokeObjectURL(previewUrl);
 previewUrl=URL.createObjectURL(file);preview.src=previewUrl;
 document.querySelector('#filename').textContent=file.name;
 document.querySelector('#filesize').textContent=(file.size/1024/1024).toFixed(2)+' МБ';
 selected.hidden=false;drop.hidden=true;analyze.disabled=false;result.hidden=true;status.textContent='';
}
fileInput.addEventListener('change',e=>setFile(e.target.files[0]));
['dragenter','dragover'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.add('drag')}));
['dragleave','drop'].forEach(n=>drop.addEventListener(n,e=>{e.preventDefault();drop.classList.remove('drag')}));
drop.addEventListener('drop',e=>setFile(e.dataTransfer.files[0]));
document.querySelector('#remove').addEventListener('click',()=>{
 currentFile=null;fileInput.value='';selected.hidden=true;drop.hidden=false;analyze.disabled=true;result.hidden=true;status.textContent='';
 if(previewUrl)URL.revokeObjectURL(previewUrl);
});
analyze.addEventListener('click',async()=>{
 if(!currentFile)return;
 analyze.disabled=true;analyze.textContent='Анализируем…';status.textContent='Модель может загружаться при первом запуске — это займёт время.';result.hidden=true;
 const data=new FormData();data.append('image',currentFile);
 try{
  const response=await fetch('/api/check',{method:'POST',body:data});
  const payload=await response.json();
  if(!response.ok)throw new Error(payload.error||'Не удалось выполнить проверку');
  document.querySelector('#verdict').textContent=payload.verdict;
  document.querySelector('#score').textContent=payload.score+'%';
  document.querySelector('#meter-fill').style.width=payload.score+'%';
  result.hidden=false;status.textContent=`Размер: ${payload.width} × ${payload.height} px`;
 }catch(err){status.textContent=err.message}
 finally{analyze.disabled=false;analyze.innerHTML='Проверить изображение <span>→</span>'}
});
