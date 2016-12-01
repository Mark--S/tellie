function(doc){
    if(doc.type=="TELLIE_CAL"){
        emit([doc.channel, doc.run_range, doc.version, doc.pass], [doc.timestamp]);
    }
}
