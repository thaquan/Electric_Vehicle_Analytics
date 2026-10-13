// Disposable Desktop verification copy using the existing exported Gold parquet.
// The committed Fabric / Direct Lake model is never converted or rebound.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'), dest=path.join(root,'output/redesign/desktop');
fs.mkdirSync(dest,{recursive:true});
const previewDefinition=path.resolve(dest,'RPT_EV_Analytics.Report/definition');
if(!previewDefinition.startsWith(path.resolve(root,'output/redesign/desktop')+path.sep))throw Error('Unsafe preview target');
fs.rmSync(previewDefinition,{recursive:true,force:true});
for(const name of ['RPT_EV_Analytics.Report','SM_EV_Analytics.SemanticModel']) {
 fs.cpSync(path.join(root,name),path.join(dest,name),{recursive:true,filter:src=>!src.split(path.sep).some(p=>p==='.pbi'||p==='.platform')});
}
fs.copyFileSync(path.join(root,'RPT_EV_Analytics.pbip'),path.join(dest,'RPT_EV_Analytics.pbip'));
const mapping={'EV Respondents':'fact_ev_purchase_intent','Demographics':'dim_demographics','Income':'dim_income','Mobility':'dim_mobility','Charging':'dim_charging','Attitude and Incentive':'dim_attitude_incentive'};
for(const [name,role] of Object.entries(mapping)) {
 const file=path.join(dest,'SM_EV_Analytics.SemanticModel/definition/tables',name+'.tmdl');
 let text=fs.readFileSync(file,'utf8');
 const source=path.join(root,'output/gold_export_staging/source_parquet',role);
 if(!fs.existsSync(source))throw Error('Missing exported Gold: '+source);
 const query=`let\n    Files = Folder.Files("${source}"),\n    Parquets = Table.SelectRows(Files, each [Extension] = ".parquet"),\n    Result = Table.Combine(List.Transform(Parquets[Content], each Parquet.Document(_)))\nin\n    Result`;
 text=text.slice(0,text.indexOf('\tpartition '))+`\tpartition '${name}' = m\n\t\tmode: import\n\t\tsource =\n`+query.split('\n').map(l=>'\t\t\t\t'+l).join('\n')+'\n';
 fs.writeFileSync(file,text);
}
console.log(path.join(dest,'RPT_EV_Analytics.pbip'));
