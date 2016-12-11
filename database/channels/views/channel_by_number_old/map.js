function(doc){
    if(doc.type=="CHANNEL"){
        emit([doc.channel, doc.run_range, doc.version, doc.pass], [1]);
    }
}
